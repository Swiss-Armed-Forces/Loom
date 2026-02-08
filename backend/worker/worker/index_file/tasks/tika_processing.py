import abc
import logging
import os
import tempfile
from pathlib import Path
from typing import Generator, Iterable

from celery import chain, chord, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from requests import RequestException

from worker.dependencies import get_tika_service
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.processor.extractor.archive_extractors import (
    BinwalkExtractor,
    ExtractNotSupported,
    ExtractorBase,
    PcapExtractor,
    PstArchiveExtractor,
    TarExtractor,
    ZipExtractor,
)
from worker.index_file.tasks import email_processing
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


class TikaFallback:
    """Base class for implementing fallbacks creating TikaResults."""

    @abc.abstractmethod
    def handle(self, file_content: LazyBytes) -> TikaResult | None:
        """Creates a TikaResult based on the given file content."""


class TikaExtractorFallback(TikaFallback):
    def __init__(self, extractor: ExtractorBase) -> None:
        self.extractor = extractor

    def handle(self, file_content: LazyBytes) -> TikaResult | None:
        with get_lazybytes_service().load_file_named(
            file_content
        ) as fd, tempfile.TemporaryDirectory() as d:
            try:
                self.extractor.extract(fd, d)
            except ExtractNotSupported:
                return None
            attachments = list(self._collect_tika_attachments(Path(d)))
        return TikaResult(attachments=attachments)

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
    TikaExtractorFallback(TarExtractor()),
    TikaExtractorFallback(ZipExtractor()),
    TikaExtractorFallback(PstArchiveExtractor()),
    TikaExtractorFallback(PcapExtractor()),
    # Run binwalk only when no other extractor can deal with the file
    TikaExtractorFallback(BinwalkExtractor()),
]

# Fallback objects to be used in the case of an unsuccessful unpack by Tika
FALLBACK_CONTENT_TYPES: set[str] = {
    "application/vnd.ms-outlook-pst",  # Outlook archive file
    "application/vnd.tcpdump.pcap",  # pcap
    "application/x-tika-msoffice",  # msi
    "application/x-msdownload",  # exe, dll
    "application/x-sharedlib",  # elf, so
    "application/x-iso9660-image",  # iso
    "application/octet-stream",  # general binaries / data
}


def signature(file_content: LazyBytes, file: File) -> Signature:
    """Create the signature for the tasks chain that processes a file and persists the
    result."""
    return chain(
        group(
            chain(
                tika_processor_task.s(file_content, file),
                chord(
                    (fallback_task.s(fallback, file_content) for fallback in FALLBACKS),
                    choose_tika_result_task.s(),
                ),
                group(
                    chain(
                        persist_tika_content_task.s(file),
                        group(
                            summarize_signature(file),
                            translate_signature(file),
                            create_embedding_signature(file),
                            secret_scan_signature(file),
                        ),
                    ),
                    persist_tika_meta_task.s(file),
                    schedule_attachments.s(file),
                ),
            ),
            chain(
                tika_get_language_task.s(file_content, file),
                persist_tika_language_task.s(file),
            ),
            chain(
                tika_get_file_type_task.s(file_content, file),
                group(
                    persist_tika_file_type_task.s(file),
                    email_processing.signature(file_content, file),
                ),
            ),
        ),
    )


@app.task(  # type: ignore[call-overload]
    base=FileIndexingTask,
    autoretry_for=TIKA_RETRY_EXCEPTIONS,
    max_retries=TIKA_MAX_RETRIES,
    retry_backoff=True,
)
@cache(key_function=lambda _, file: file.sha256)
def tika_processor_task(file_content: LazyBytes, file: File) -> TikaResult | None:
    """Task to process the raw data of a file."""
    logger.info("Processing %s with tika", file.full_name)
    with get_lazybytes_service().load_memoryview(file_content) as memview:
        try:
            result = get_tika_service().parse(memview)
        except TikaError:
            # will proceed to fallback
            return None

    if result.meta.get("Content-Type", None) in FALLBACK_CONTENT_TYPES:
        # force a fallback
        return None

    return result


@app.task(base=FileIndexingTask)
def fallback_task(
    tika_result: TikaResult | None,
    fallback: TikaFallback,
    file_content: LazyBytes,
) -> TikaResult | None:
    """Task to use fallback in case of an unsuccessful Tika processing."""
    if tika_result is not None:
        # no fallback required, tika processing was successful
        return tika_result

    return fallback.handle(file_content)


@app.task(base=FileIndexingTask)
def choose_tika_result_task(tika_results: Iterable[TikaResult | None]) -> TikaResult:
    """Task to choose a TikaResult generated from the fallback tasks."""
    # To explain why the following logic is sufficient, we consider the following
    # possible scenarios:
    #   - in case of a successful parse, all results are the same and all
    #     correspond to what was been returned by the initial Tika task.
    #     So taking the first non-None result is sufficient.
    #   - in case of an uncuccessful parse, the fallback tasks have all
    #     run and will generate maybe-None results, in which case we
    #     just want to pick the first non-None result.
    for tika_result in tika_results:
        if tika_result is not None:
            return tika_result
    # fallbacks unsuccessful, re-raise a TikaError
    raise TikaError


@persisting_task(app, IndexingPersister)
def persist_tika_content_task(persister: IndexingPersister, tika_result: TikaResult):
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
def persist_tika_meta_task(persister: IndexingPersister, tika_result: TikaResult):
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
    with get_lazybytes_service().load_memoryview(file_content) as memview:
        return get_tika_service().get_language(memview)


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
    with get_lazybytes_service().load_memoryview(file_content) as memview:
        return get_tika_service().get_file_type(memview)


@persisting_task(app, IndexingPersister)
def persist_tika_file_type_task(persister: IndexingPersister, tika_file_type: str):
    persister.set_tika_file_type(tika_file_type)
