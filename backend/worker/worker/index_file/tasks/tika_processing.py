import abc
import logging
import os
import tempfile
from pathlib import Path
from typing import Generator

from celery import Task, chain, chord, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes, TypedLazyBytes
from common.utils.cache import cache
from pydantic import BaseModel, ConfigDict
from requests import RequestException

from worker.dependencies import get_tika_service
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
from worker.index_file.extractor.xz_extractor import XZExtractor
from worker.index_file.extractor.zip_extractor import ZipExtractor
from worker.index_file.extractor.zstd_extractor import ZstdExtractor
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.tasks import email_processing, extract_magic_file_type
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
)
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

TIKA_MAX_RETRIES = 15
TIKA_RETRY_EXCEPTIONS = (RequestException,)

logger = logging.getLogger(__name__)

app = get_celery_app()


class TikaProcessingResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_type: str
    result: TypedLazyBytes[TikaResult] | None = None
    exceptions: list[Exception] = []
    handled_by: str | None = None


class TikaFallback:
    """Base class for implementing fallbacks creating TikaResults."""

    @abc.abstractmethod
    def handle(self, file_content: LazyBytes, file_type: str) -> TikaResult | None:
        """Creates a TikaResult based on the given file content and type."""


class TikaExtractorFallback(TikaFallback):
    def __init__(self, extractor: ExtractorBase):
        self.extractor = extractor
        self.lazybytes_service = get_lazybytes_service()

    def handle(self, file_content: LazyBytes, file_type: str) -> TikaResult | None:
        with tempfile.TemporaryDirectory(
            dir=settings.tempfile_dir
        ) as out_dir, tempfile.NamedTemporaryFile(
            dir=settings.tempfile_dir
        ) as out_content:
            try:
                self.extractor.extract(file_content, file_type, out_dir, out_content)
            except ExtractNotSupported:
                return None
            attachments = list(self._collect_tika_attachments(Path(out_dir)))
            # read text
            out_content.flush()
            out_content.seek(0)
            text = out_content.read(TIKA_MAX_TEXT_SIZE)
        return TikaResult(
            text=self.lazybytes_service.from_bytes(text),
            text_truncated=len(text) >= TIKA_MAX_TEXT_SIZE,
            attachments=attachments,
        )

    def _collect_tika_attachments(
        self, directory: Path
    ) -> Generator[TikaAttachment, None, None]:
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                filepath = Path(dirpath, filename)
                with filepath.open("rb") as fd:
                    lazybytes = get_lazybytes_service().from_file(fd)
                name = str(filepath.relative_to(directory))
                yield TikaAttachment(name=name, data=lazybytes)


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
}


def _get_fallback_name(fallback: TikaFallback) -> str:
    """Derive a unique name from the fallback's extractor class."""
    if isinstance(fallback, TikaExtractorFallback):
        return fallback.extractor.__class__.__name__.lower()
    return fallback.__class__.__name__.lower()


def _create_fallback_task(fallback: TikaFallback) -> Task:
    """Factory to create a distinct Celery task for a TikaFallback."""
    fallback_name = _get_fallback_name(fallback)
    task_name = f"{__name__}.fallback_{fallback_name}_task"

    # Apply cache decorator with explicit namespace (dynamic functions share __qualname__)
    @cache(key_function=lambda _, __, file: file.sha256, namespace=task_name)
    def task_handler(
        tika_processing_result: TikaProcessingResult,
        file_content: LazyBytes,
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
            tika_processing_result.exceptions.append(ex)
        if result is None:
            return tika_processing_result
        return TikaProcessingResult(
            file_type=tika_processing_result.file_type,
            result=get_lazybytes_service().from_object(result),
            handled_by=fallback_name,
        )

    return app.task(base=FileIndexingTask, name=task_name)(task_handler)


# List of generated fallback tasks (maintains order matching FALLBACKS)
FALLBACK_TASKS: list[Task] = [_create_fallback_task(fb) for fb in FALLBACKS]
FALLBACK_TASKS_LEVEL2: list[Task] = [
    _create_fallback_task(fb) for fb in FALLBACKS_LEVEL2
]


def signature(file_content: LazyBytes, file: File) -> Signature:
    return group(
        chain(
            extract_magic_file_type.signature(file_content, file),
            group(
                email_processing.signature(file_content, file),
                chain(
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
                        chain(
                            extract_tika_result_from_tika_processing_result_task.s(),
                            group(
                                persist_tika_result_task.s(file.id_),
                                persist_tika_meta_task.s(file.id_),
                                schedule_attachments.s(file),
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
@cache(key_function=lambda _, __, ___, file: file.sha256)
def tika_processor_task(
    self: FileIndexingTask, file_type: str, file_content: LazyBytes, _: File
) -> TikaProcessingResult:
    lazybytes_service = get_lazybytes_service()

    if file_type in FALLBACK_CONTENT_TYPES:
        # force a fallback
        return TikaProcessingResult(file_type=file_type)

    generator = lazybytes_service.load_generator(file_content)
    try:
        result = get_tika_service().parse_from_generator(generator)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        if ex in TIKA_RETRY_EXCEPTIONS and self.request.retries < TIKA_MAX_RETRIES:
            raise ex
        # will proceed to fallback
        return TikaProcessingResult(file_type=file_type, exceptions=[ex])

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
    # To explain why the following logic is sufficient, we consider the following
    # possible scenarios:
    #   - in case of a successful parse, all results are the same and all
    #     correspond to what was been returned by the initial Tika task.
    #     So taking the first non-None result is sufficient.
    #   - in case of an uncuccessful parse, the fallback tasks have all
    #     run and will generate maybe-None results, in which case we
    #     just want to pick the first non-None result.
    for tika_processing_result in tika_processing_results:
        if tika_processing_result.result is not None:
            return tika_processing_result
    # if all invalid, merge resulsts
    merged_tika_processing_result = TikaProcessingResult(
        file_type=tika_processing_results[0].file_type,
        exceptions=[
            exception
            for tika_processing_result in tika_processing_results
            for exception in tika_processing_result.exceptions
        ],
    )
    return merged_tika_processing_result


@app.task(base=FileIndexingTask)
def extract_tika_result_from_tika_processing_result_task(
    tika_processing_result: TikaProcessingResult,
) -> TypedLazyBytes[TikaResult]:
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
def persist_tika_result_task(
    persister: IndexingPersister, lazy_tika_result: TypedLazyBytes[TikaResult]
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
    persister: IndexingPersister, lazy_tika_result: TypedLazyBytes[TikaResult]
):
    lazybytes_service = get_lazybytes_service()
    tika_result = lazybytes_service.load_object(lazy_tika_result)
    persister.set_tika_meta(tika_result.meta)


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
@cache(key_function=lambda _, file: file.sha256)
def tika_get_language_task(file_content: LazyBytes, file: File) -> str:
    """Task to get the tika detected language."""
    logger.info("Getting language for %s with tika", file.full_name)
    file_generator = get_lazybytes_service().load_generator(file_content)
    return get_tika_service().get_language_from_generator(file_generator)


@persisting_task(app, IndexingPersister)
def persist_tika_language_task(persister: IndexingPersister, tika_language: str):
    persister.set_tika_language(tika_language)


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
@cache(key_function=lambda _, file: file.sha256)
def tika_get_file_type_task(file_content: LazyBytes, file: File) -> str:
    """Task to get the tika detected file type."""
    logger.info("Getting file type for %s with tika", file.full_name)
    file_generator = get_lazybytes_service().load_generator(file_content)
    return get_tika_service().get_file_type_from_generator(file_generator)


@persisting_task(app, IndexingPersister)
def persist_tika_file_type_task(persister: IndexingPersister, tika_file_type: str):
    persister.set_tika_file_type(tika_file_type)


@app.task(base=FileIndexingTask)
def extract_text_from_lazy_tika_result(
    lazy_tika_result: TypedLazyBytes[TikaResult],
) -> LazyBytes | None:
    tika_result = get_lazybytes_service().load_object(lazy_tika_result)
    return tika_result.text
