import abc
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from traceback import format_exception
from typing import NamedTuple

from celery import Task, chain, chord, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File, FilePurePath
from common.llm.exceptions import LLMError, LLMTransientError, classify_llm_error
from common.services.lazybytes_service import TempLazyBytes, TempTypedLazyBytes
from common.services.task_scheduling_service import IndexingPriority
from common.utils.cache import cache
from pydantic import BaseModel, ConfigDict

from worker.dependencies import (
    get_llm_ocr_language_detection_so_agent,
    get_tika_service,
)
from worker.index_file.extractor.base import (
    ExtractNotSupported,
    ExtractorBase,
)
from worker.index_file.extractor.gzip_extractor import GzipExtractor
from worker.index_file.extractor.pcap_extractor import PcapExtractor
from worker.index_file.extractor.pst_extractor import (
    PstExtractor,
)
from worker.index_file.extractor.strings_extractor import StringsExtractor
from worker.index_file.extractor.tar_extractor import TarExtractor
from worker.index_file.extractor.unar_extractor import UnarExtractor
from worker.index_file.extractor.xz_extractor import XZExtractor
from worker.index_file.extractor.zip_extractor import ZipExtractor
from worker.index_file.extractor.zstd_extractor import ZstdExtractor
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.tasks import (
    email_processing,
    extract_magic_file_type,
    image_description,
)
from worker.index_file.tasks.create_embedding import (
    signature as create_embedding_signature,
)
from worker.index_file.tasks.schedule_attachments import schedule_attachments
from worker.index_file.tasks.secret_scan import signature as secret_scan_signature
from worker.index_file.tasks.summarize import signature as summarize_signature
from worker.index_file.tasks.translate import signature as translate_signature
from worker.services.tika_service import (
    TIKA_MAX_TEXT_SIZE,
    TikaAttachment,
    TikaError,
    TikaResult,
    TikaTransientError,
)
from worker.settings import TikaCommonOcrLanguage, settings
from worker.utils.persisting_task import persisting_task

TIKA_MAX_RETRIES = 15
# Only the transient half of the TikaError hierarchy. A TikaPermanentError fails the
# same way on every attempt, so retrying it buys nothing and occupies a worker for the
# whole backoff budget.
TIKA_RETRY_EXCEPTIONS = (TikaTransientError,)
# Elasticsearch's own cut-off for a keyword it will still index.
DEGRADATION_REASON_MAX_LENGTH = 256

# The content types whose OCR language tika is ever told about. `X-Tika-OCRLanguage`
# reaches tesseract for images and for the PDFs tika decides to OCR, and for nothing
# else -- so asking a decision model about a .docx is one inference per file for an
# answer that is then discarded.
OCR_CANDIDATE_CONTENT_TYPES = ("image/", "application/pdf")

logger = logging.getLogger(__name__)

app = get_celery_app()


def _exception_as_str(ex: Exception) -> str:
    return "".join(format_exception(type(ex), ex, ex.__traceback__))


def _degradation_reason(ex: Exception) -> str:
    """Summarise a failure in one line, for the field a degraded document carries.

    The traceback goes to the log; what is persisted has to stay an aggregatable
    keyword, so it is the exception type and its message, capped at the length
    Elasticsearch stops indexing a keyword at.
    """
    return f"{type(ex).__name__}: {ex}".strip()[:DEGRADATION_REASON_MAX_LENGTH]


def _merge_degradation_reasons(
    tika_processing_results: list[TikaProcessingResult],
) -> list[str]:
    """Collect every reason the chord's branches saw, in order and without repeats.

    Each fallback is handed its own copy of what tika returned, so tika's own reason
    comes back once per branch.
    """
    return list(
        dict.fromkeys(
            reason
            for tika_processing_result in tika_processing_results
            for reason in tika_processing_result.degradation_reasons
        )
    )


def _degraded_tika_facet(file: File, facet: str) -> str:
    """Give up on an optional tika facet rather than failing the file over it.

    The empty string is already this service's answer for an empty document, and the
    language and file type are search facets: losing one costs less than failing the
    whole indexing chain for a document tika will never parse.
    """
    logger.warning(
        "Tika %s detection failed, indexing without it (file=%s sha256=%s)",
        facet,
        file.full_name,
        file.sha256,
        exc_info=True,
    )
    return ""


def _log_degradation(
    file: File, file_type: str, ex: Exception, *, retries_exhausted: bool
) -> None:
    """Announce that tika will not parse this document and the fallbacks take over.

    This is where the traceback lives. The document itself keeps only the one-line
    reason, in tika_degradation_reasons.
    """
    logger.warning(
        "Tika parsing failed, degrading to the fallback extractors "
        "(file=%s sha256=%s file_type=%s retries_exhausted=%s)",
        file.full_name,
        file.sha256,
        file_type,
        retries_exhausted,
        exc_info=ex,
    )


class InferredOcrLanguage(NamedTuple):
    """What `infer_language_via_llm_task` hands to `tika_processor_task`.

    One value rather than two, because celery passes a task's return value to the next
    link in a chain as a single positional argument whatever its shape.
    """

    file_type: str
    language: TikaCommonOcrLanguage | None


class TikaProcessingResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_type: str
    result: TempTypedLazyBytes[TikaResult] | None = None
    exceptions: list[str] = []
    # The same failures as `exceptions`, one summary line each. `exceptions` carries
    # tracebacks and is only ever read when nothing produced a result at all; this is
    # what survives onto a document that a fallback did index.
    degradation_reasons: list[str] = []
    handled_by: str | None = None


class TikaFallback:
    """Base class for implementing fallbacks creating TikaResults."""

    @abc.abstractmethod
    def handle(self, file_content: TempLazyBytes, file_type: str) -> TikaResult | None:
        """Creates a TikaResult based on the given file content and type."""


class TikaExtractorFallback(TikaFallback):
    def __init__(self, extractor: ExtractorBase):
        self.extractor = extractor
        self.lazybytes_service = get_lazybytes_service()

    def handle(self, file_content: TempLazyBytes, file_type: str) -> TikaResult | None:
        with tempfile.TemporaryDirectory(
            dir=settings.tempfile_dir
        ) as out_dir, tempfile.NamedTemporaryFile(
            dir=settings.tempfile_dir
        ) as out_content:
            try:
                self.extractor.extract(file_content, file_type, out_dir, out_content)
            except ExtractNotSupported:
                return None
            attachments = self._collect_tika_attachments(Path(out_dir))
            # read text
            out_content.flush()
            out_content.seek(0)
            text = out_content.read(TIKA_MAX_TEXT_SIZE)
        return TikaResult(
            text=self.lazybytes_service.from_bytes(text),
            text_truncated=len(text) >= TIKA_MAX_TEXT_SIZE,
            attachments=attachments,
        )

    def _collect_tika_attachments(self, directory: Path) -> list[TikaAttachment]:
        filepaths = (
            Path(dirpath, filename)
            for dirpath, _, filenames in os.walk(directory)
            for filename in filenames
        )

        def _process(filepath: Path) -> TikaAttachment:
            with filepath.open("rb") as fd:
                lazybytes = get_lazybytes_service().from_file(fd)
            return TikaAttachment(
                name=str(filepath.relative_to(directory)), data=lazybytes
            )

        with ThreadPoolExecutor() as executor:
            return list(executor.map(_process, filepaths))


# Fallback objects to be used in the case of an unsuccessful unpack by Tika.
# Ordered list indicating the order of fallback extractor to be used.
FALLBACKS: list[TikaFallback] = [
    TikaExtractorFallback(XZExtractor()),
    TikaExtractorFallback(ZstdExtractor()),
    TikaExtractorFallback(TarExtractor()),
    TikaExtractorFallback(GzipExtractor()),
    TikaExtractorFallback(ZipExtractor()),
    TikaExtractorFallback(PstExtractor()),
    TikaExtractorFallback(PcapExtractor()),
    # Last: `unar` reads several of the formats above, so every extractor that
    # names one keeps first claim and this one only sees what they all declined.
    TikaExtractorFallback(UnarExtractor()),
]

FALLBACKS_LEVEL2: list[TikaFallback] = [
    TikaExtractorFallback(StringsExtractor()),
]

# Mime types where Tika's parsing is insufficient and specialized extractors are needed.
# Even if Tika would succeeds, we force fallback to extractors (PST, PCAP, binaries, etc.)
# that can properly extract embedded content and attachments from these formats.
# Must match: file -i FILENAME
# See:
# - https://mimetype.io
FALLBACK_CONTENT_TYPES: set[str] = {
    "application/vnd.ms-outlook",  # Outlook archive file
    "application/vnd.tcpdump.pcap",  # pcap
    "application/x-msdownload",  # exe, dll
    "application/x-msi",  # msi installer
    "application/x-sharedlib",  # elf, so
    "application/x-iso9660-image",  # iso
    "application/octet-stream",  # general binaries / data
    # Tika's /unpack/all silently drops 0-byte archive members, so empty files
    # inside tar archives would never be indexed. The TarExtractor fallback
    # handles all members regardless of size.
    "application/x-tar",
    "application/x-gtar",
    "application/x-ustar",
}


def _get_fallback_name(fallback: TikaFallback) -> str:
    """Derive a unique name from the fallback's extractor class."""
    if isinstance(fallback, TikaExtractorFallback):
        return fallback.extractor.__class__.__name__.lower()
    return fallback.__class__.__name__.lower()


LEVEL2_FALLBACK_NAMES: set[str] = {
    _get_fallback_name(fallback) for fallback in FALLBACKS_LEVEL2
}


def _create_fallback_task(fallback: TikaFallback) -> Task:
    """Factory to create a distinct Celery task for a TikaFallback."""
    fallback_name = _get_fallback_name(fallback)
    task_name = f"{__name__}.fallback_{fallback_name}_task"

    # Apply cache decorator with explicit namespace (dynamic functions share __qualname__)
    @cache(key_function=lambda _, __, file: file.sha256, namespace=task_name)
    def task_handler(
        tika_processing_result: TikaProcessingResult,
        file_content: TempLazyBytes,
        _: File,
    ) -> TikaProcessingResult:
        if tika_processing_result.result is not None:
            # result already available: do nothing
            return tika_processing_result
        result: TikaResult | None = None
        try:
            result = fallback.handle(file_content, tika_processing_result.file_type)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # we don't let any exception from the fallbacks bubble up,
            # otherwise one exception from a fallback might stop the whole
            # tika processing pipeline.
            logger.exception("Tika fallback failed: %s", fallback_name)
            tika_processing_result.exceptions.append(_exception_as_str(ex))
            tika_processing_result.degradation_reasons.append(
                f"{fallback_name}: {_degradation_reason(ex)}"
            )
        if result is None:
            return tika_processing_result
        return TikaProcessingResult(
            file_type=tika_processing_result.file_type,
            result=get_lazybytes_service().from_object(result),
            degradation_reasons=tika_processing_result.degradation_reasons,
            handled_by=fallback_name,
        )

    return app.task(base=FileIndexingTask, name=task_name)(task_handler)


# List of generated fallback tasks (maintains order matching FALLBACKS)
FALLBACK_TASKS: list[Task] = [_create_fallback_task(fb) for fb in FALLBACKS]
FALLBACK_TASKS_LEVEL2: list[Task] = [
    _create_fallback_task(fb) for fb in FALLBACKS_LEVEL2
]


def signature(
    file_content: TempLazyBytes,
    file: File,
    max_recursion_depth: int,
    priority: IndexingPriority = IndexingPriority.MEDIUM,
) -> Signature:
    return group(
        chain(
            extract_magic_file_type.signature(file_content, file),
            group(
                email_processing.signature(file_content, file),
                image_description.signature(file_content, file),
                chain(
                    infer_language_via_llm_task.s(file.full_name),
                    tika_processor_task.s(file_content, file),
                    chord(
                        (task.s(file_content, file) for task in FALLBACK_TASKS),
                        choose_tika_processing_result_task.s(),
                    ),
                    chord(
                        (task.s(file_content, file) for task in FALLBACK_TASKS_LEVEL2),
                        choose_tika_processing_result_task.s(),
                    ),
                    group(
                        persist_tika_handled_by.s(file.id_),
                        persist_tika_degradation_reasons.s(file.id_),
                        chain(
                            extract_tika_result_from_tika_processing_result_task.s(),
                            group(
                                persist_tika_result_task.s(file.id_),
                                persist_tika_meta_task.s(file.id_),
                                schedule_attachments.s(
                                    file, max_recursion_depth, priority
                                ),
                                chain(
                                    extract_text_from_lazy_tika_result.s(),
                                    group(
                                        summarize_signature(file),
                                        translate_signature(file),
                                        create_embedding_signature(file),
                                        secret_scan_signature(file),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        chain(
            tika_get_language_task.s(file_content, file),
            persist_tika_language_task.s(file.id_),
        ),
        chain(
            tika_get_file_type_task.s(file_content, file),
            persist_tika_file_type_task.s(file.id_),
        ),
    )


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    bind=True,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
# Keyed on the inferred language as well as the bytes: the language is derived from
# the file's name, so two copies of one scanned document filed under different names
# are OCR'd differently and must not share an entry.
@cache(key_function=lambda _, inferred, __, file: (file.sha256, inferred.language))
def tika_processor_task(
    self: FileIndexingTask,
    inferred: InferredOcrLanguage,
    file_content: TempLazyBytes,
    file: File,
) -> TikaProcessingResult:
    file_type, inferred_language = inferred
    lazybytes_service = get_lazybytes_service()

    if file_type in FALLBACK_CONTENT_TYPES:
        # force a fallback
        return TikaProcessingResult(file_type=file_type)

    generator = lazybytes_service.load_generator(file_content)
    try:
        result = get_tika_service().parse_from_generator(generator, inferred_language)
    except TikaTransientError as ex:
        if not self.is_last_attempt:
            # Re-raise the same object: autoretry_for matches on what leaves here.
            raise
        _log_degradation(file, file_type, ex, retries_exhausted=True)
        return TikaProcessingResult(
            file_type=file_type,
            exceptions=[_exception_as_str(ex)],
            degradation_reasons=[
                f"tika_processor (retries exhausted): {_degradation_reason(ex)}"
            ],
        )
    except Exception as ex:  # pylint: disable=broad-exception-caught
        # A permanent tika refusal, or anything unforeseen: a retry ends in the same
        # place, so degrade to the fallback extractors now.
        _log_degradation(file, file_type, ex, retries_exhausted=False)
        return TikaProcessingResult(
            file_type=file_type,
            exceptions=[_exception_as_str(ex)],
            degradation_reasons=[f"tika_processor: {_degradation_reason(ex)}"],
        )

    return TikaProcessingResult(
        file_type=file_type,
        result=lazybytes_service.from_object(result),
        handled_by="tika_processor",
    )


@app.task(base=FileIndexingTask)
def choose_tika_processing_result_task(
    tika_processing_results: list[TikaProcessingResult],
) -> TikaProcessingResult:
    """Task to choose a TikaResult generated from the fallback tasks."""
    # To explain why the following logic is sufficient, we consider the
    # possible scenarios:
    #   - in case of a successful parse, all results are the same and all
    #     correspond to what was been returned by the initial Tika task.
    #     So taking the first non-None result is sufficient.
    #   - in case of an uncuccessful parse, the fallback tasks have all
    #     run and will generate maybe-None results, in which case we
    #     just want to pick the first non-None result.
    degradation_reasons = _merge_degradation_reasons(tika_processing_results)
    for tika_processing_result in tika_processing_results:
        if tika_processing_result.result is not None:
            if tika_processing_result.handled_by in LEVEL2_FALLBACK_NAMES:
                # The last resort won. For a document format tika handles, this means
                # its text was replaced by whatever byte sequences looked printable.
                logger.warning(
                    "Tika processing degraded to a last-resort fallback: %s",
                    tika_processing_result.handled_by,
                )
            # The winner saw only its own branch of the chord, so the reasons the
            # others collected are grafted on here: whoever produced the content is
            # the only result that reaches the document.
            return tika_processing_result.model_copy(
                update={"degradation_reasons": degradation_reasons}
            )
    # if all invalid, merge results
    merged_tika_processing_result = TikaProcessingResult(
        file_type=tika_processing_results[0].file_type,
        exceptions=[
            exception
            for tika_processing_result in tika_processing_results
            for exception in tika_processing_result.exceptions
        ],
        degradation_reasons=degradation_reasons,
    )
    return merged_tika_processing_result


@app.task(base=FileIndexingTask)
def extract_tika_result_from_tika_processing_result_task(
    tika_processing_result: TikaProcessingResult,
) -> TempTypedLazyBytes[TikaResult]:
    if tika_processing_result.result is None:
        raise TikaError(tika_processing_result.exceptions)
    return tika_processing_result.result


@persisting_task(app, IndexingPersister)
def persist_tika_handled_by(
    persister: IndexingPersister, tika_processing_result: TikaProcessingResult
):
    if tika_processing_result.handled_by is None:
        return
    persister.set_tika_handled_by(tika_processing_result.handled_by)


@persisting_task(app, IndexingPersister)
def persist_tika_degradation_reasons(
    persister: IndexingPersister, tika_processing_result: TikaProcessingResult
):
    """Record why a fallback indexed this file instead of tika.

    The document is otherwise indistinguishable from one tika parsed, apart from its
    tika_handled_by: the text a fallback produced looks like extracted content, and for
    an email the strings extractor's output reads like the message itself.
    """
    if not tika_processing_result.degradation_reasons:
        return
    persister.set_tika_degradation_reasons(tika_processing_result.degradation_reasons)


@persisting_task(app, IndexingPersister)
def persist_tika_result_task(
    persister: IndexingPersister, lazy_tika_result: TempTypedLazyBytes[TikaResult]
):
    lazybytes_service = get_lazybytes_service()
    tika_result = lazybytes_service.load_object(lazy_tika_result)
    if tika_result.text is not None:
        with get_lazybytes_service().load_memoryview(tika_result.text) as memview:
            text = (
                memview[:TIKA_MAX_TEXT_SIZE]
                .tobytes()
                .decode(errors=settings.decode_error_handler)
            )
            persister.set_content(text)
    persister.set_content_truncated(tika_result.text_truncated)


@persisting_task(app, IndexingPersister)
def persist_tika_meta_task(
    persister: IndexingPersister, lazy_tika_result: TempTypedLazyBytes[TikaResult]
):
    lazybytes_service = get_lazybytes_service()
    tika_result = lazybytes_service.load_object(lazy_tika_result)
    persister.set_tika_meta(tika_result.meta)


def infer_ocr_language(full_name: FilePurePath) -> TikaCommonOcrLanguage | None:
    """Guess the OCR language from a path, or None when there is no usable guess.

    None when the model answers "other", which says the name carries no language
    signal: tesseract is then left with `settings.tika_ocr_languages` alone.

    Raises LLMTransientError or LLMPermanentError when the decision model fails.
    """
    try:
        system_one_return = get_llm_ocr_language_detection_so_agent().run_sync(
            f"Fullpath: {full_name}"
        )
    except Exception as ex:
        raise classify_llm_error(ex, "OCR language detection failed") from ex

    if system_one_return.output is TikaCommonOcrLanguage.OTHER:
        return None

    return system_one_return.output


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    bind=True,
    autoretry_for=(LLMTransientError,),
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
def infer_language_via_llm_task(
    self: FileIndexingTask,
    file_type: str,
    full_name: FilePurePath,
) -> InferredOcrLanguage:
    """Guess the OCR language of a file from its name.

    Heads the tika chain, so anything raised here costs the file its extraction, its
    fallbacks and everything downstream. A language hint is worth none of that: once the
    retry budget is spent the file goes to tika without one.

    The failure is caught out here rather than inside `_infer_ocr_language`, so that the
    cache below holds inferences alone. Cached, the "no hint" a ten-minute outage
    produces would be served for `CACHE_DEFAULT_TTL_SECONDS` to every file name seen
    during it, long after the service came back.
    """
    if settings.skip_ocr_language_detection_while_indexing:
        return InferredOcrLanguage(file_type, None)

    if not file_type.startswith(OCR_CANDIDATE_CONTENT_TYPES):
        return InferredOcrLanguage(file_type, None)

    try:
        return _infer_ocr_language(file_type, full_name)
    except LLMError as ex:
        if isinstance(ex, LLMTransientError) and not self.is_last_attempt:
            raise
        logger.warning(
            "OCR language detection failed, indexing without a language hint "
            "(file=%s)",
            full_name,
            exc_info=True,
        )
        return InferredOcrLanguage(file_type, None)


# The cache sits on the inference rather than on the task, because its key is the
# file's name: a content type nobody asks the model about would otherwise take one
# redis entry per name indexed, for an answer that is a comparison away.
@cache(key_function=lambda file_type, full_name: (file_type, full_name))
def _infer_ocr_language(
    file_type: str,
    full_name: FilePurePath,
) -> InferredOcrLanguage:
    logger.info("Getting language for %s with LLM call", full_name)
    return InferredOcrLanguage(file_type, infer_ocr_language(full_name))


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    bind=True,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
@cache(key_function=lambda _, __, file: file.sha256)
def tika_get_language_task(
    self: FileIndexingTask, file_content: TempLazyBytes, file: File
) -> str:
    """Task to get the tika detected language."""
    logger.info("Getting language for %s with tika", file.full_name)
    file_generator = get_lazybytes_service().load_generator(file_content)
    try:
        return get_tika_service().get_language_from_generator(file_generator)
    except TikaTransientError:
        if not self.is_last_attempt:
            raise
        return _degraded_tika_facet(file, "language")
    except TikaError:
        return _degraded_tika_facet(file, "language")


@persisting_task(app, IndexingPersister)
def persist_tika_language_task(persister: IndexingPersister, tika_language: str):
    persister.set_tika_language(tika_language)


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    bind=True,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
@cache(key_function=lambda _, __, file: file.sha256)
def tika_get_file_type_task(
    self: FileIndexingTask, file_content: TempLazyBytes, file: File
) -> str:
    """Task to get the tika detected file type."""
    logger.info("Getting file type for %s with tika", file.full_name)
    file_generator = get_lazybytes_service().load_generator(file_content)
    try:
        return get_tika_service().get_file_type_from_generator(file_generator)
    except TikaTransientError:
        if not self.is_last_attempt:
            raise
        return _degraded_tika_facet(file, "file type")
    except TikaError:
        return _degraded_tika_facet(file, "file type")


@persisting_task(app, IndexingPersister)
def persist_tika_file_type_task(persister: IndexingPersister, tika_file_type: str):
    persister.set_tika_file_type(tika_file_type)


@app.task(base=FileIndexingTask)
def extract_text_from_lazy_tika_result(
    lazy_tika_result: TempTypedLazyBytes[TikaResult],
) -> TempLazyBytes | None:
    tika_result = get_lazybytes_service().load_object(lazy_tika_result)
    return tika_result.text
