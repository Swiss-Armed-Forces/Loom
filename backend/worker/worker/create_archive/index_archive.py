"""Routing a blob that was handed to the archive importer.

This used to be a `group` of two chains -- one assuming an encrypted archive, one
assuming a plain zip -- each of which detected its own case and returned None when it
did not apply. A blob that was neither therefore ended up in *both* branches doing
nothing: no File entry, no index entry, and no error anywhere, because `POST
/v1/archive/import` had already answered 202. A file handed to the wrong endpoint simply
disappeared.

So the decision is made here, up front and in one place, and there is a third outcome:
anything that is not an importable archive is indexed as the ordinary file it is.
Nothing that reaches this task can be dropped.

Detecting synchronously is affordable because none of it transfers content. Every check
here reads through `load_seekable`, so deciding what a 300 GB archive is costs a handful
of range requests rather than a download and a local copy -- see
`decrypts_to_a_loom_zip` for the one question that would otherwise have cost a full
pass.
"""

import logging
from dataclasses import dataclass
from enum import StrEnum

from common.archive.archive_detection import (
    decrypts_to_a_loom_zip,
    encrypted_probe_length,
    is_encrypted_archive_header,
    is_loom_archive,
)
from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
    get_task_scheduling_service,
)
from common.services.lazybytes_service import FileStorageLazyBytes
from common.services.task_scheduling_service import ArchiveImportRequest

from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks import unzip_loom_archive
from worker.create_archive.tasks.load_loom_archive_encrypted import decrypt_loom_archive

logger = logging.getLogger(__name__)

app = get_celery_app()


class ArchiveDecision(StrEnum):
    """What to do with a blob handed to the archive importer."""

    IMPORT_PLAIN = "import_plain"
    IMPORT_DECRYPTED = "import_decrypted"
    INDEX_AS_FILE = "index_as_file"


@dataclass(frozen=True)
class ArchiveRouting:
    """The decision, plus the zip to unpack and why it was decided that way."""

    decision: ArchiveDecision
    archive_zip: FileStorageLazyBytes | None
    reason: str


class EncryptedBlobVerdict(StrEnum):
    """What the first few dozen bytes of a blob say about its encryption."""

    NOT_ENCRYPTED = "not_encrypted"
    FOREIGN_KEY = "foreign_key"
    DECRYPTS_TO_ZIP = "decrypts_to_zip"


def _inspect_encrypted_header(
    file_content: FileStorageLazyBytes,
) -> EncryptedBlobVerdict:
    """Answer both encryption questions from a single read of the header.

    Whether the blob is an encrypted container and whether this deployment's key opens
    it are settled from the same ~61 bytes, so they share one read rather than two.
    """
    service = get_archive_encryption_service()
    with get_file_storage_service().load_seekable(file_content) as fd:
        head = fd.read(encrypted_probe_length(service))

    if not is_encrypted_archive_header(head):
        return EncryptedBlobVerdict.NOT_ENCRYPTED

    if not decrypts_to_a_loom_zip(service, head):
        return EncryptedBlobVerdict.FOREIGN_KEY

    return EncryptedBlobVerdict.DECRYPTS_TO_ZIP


def _is_importable_archive(file_content: FileStorageLazyBytes) -> bool:
    with get_file_storage_service().load_seekable(file_content) as fd:
        return is_loom_archive(fd)


def route_archive_blob(file_content: FileStorageLazyBytes) -> ArchiveRouting:
    """Decide what a blob actually is, doing any decryption it takes to find out.

    Separate from the task so the decision can be tested on its own: everything
    below this line is Celery canvas plumbing, and everything above it is the
    part that used to get this wrong.
    """
    verdict = _inspect_encrypted_header(file_content)

    if verdict is EncryptedBlobVerdict.FOREIGN_KEY:
        # Carries the archive magic but will not open with this deployment's key
        # -- almost always an archive from another box. Settled from the header,
        # so no part of the body is transferred to find out.
        return ArchiveRouting(
            ArchiveDecision.INDEX_AS_FILE,
            None,
            "encrypted, and the key does not fit",
        )

    if verdict is EncryptedBlobVerdict.DECRYPTS_TO_ZIP:
        decrypted = decrypt_loom_archive(file_content)
        if decrypted is None:
            # The header probe already said the key fits, so reaching here means
            # the body failed its MAC: truncation or corruption, not a foreign
            # archive. Worth distinguishing in the log -- the two have different
            # causes and different fixes.
            return ArchiveRouting(
                ArchiveDecision.INDEX_AS_FILE,
                None,
                "encrypted, and decryption failed",
            )

        if not _is_importable_archive(decrypted):
            return ArchiveRouting(
                ArchiveDecision.INDEX_AS_FILE,
                None,
                "decrypted, but not a loom archive",
            )

        return ArchiveRouting(ArchiveDecision.IMPORT_DECRYPTED, decrypted, "")

    if not _is_importable_archive(file_content):
        return ArchiveRouting(
            ArchiveDecision.INDEX_AS_FILE, None, "no valid MANIFEST.json"
        )

    return ArchiveRouting(ArchiveDecision.IMPORT_PLAIN, file_content, "")


def _index_as_ordinary_file(request: ArchiveImportRequest, reason: str) -> None:
    """Index the blob as a plain file, because it is not an archive we can open."""
    logger.info(
        "'%s' is not an importable loom archive (%s); indexing it as a plain file",
        request.full_name,
        reason,
    )
    get_task_scheduling_service().dispatch_index_file(
        full_name=request.full_name,
        file_content=request.file_content,
        source_id=request.source_id,
        parent_id=None,
        uploaded_datetime=request.uploaded_datetime,
    )


@app.task(base=ArchiveProcessingTask)
def index_archive_task(request: ArchiveImportRequest):
    """Import a loom archive, or index the blob as a file when it is not one."""
    routing = route_archive_blob(request.file_content)

    if routing.decision is ArchiveDecision.INDEX_AS_FILE:
        _index_as_ordinary_file(request, routing.reason)
        return

    # `encrypted_archive_zip` is what links the restored archive back to the blob
    # the operator actually supplied, so it stays the original rather than the
    # decrypted copy.
    encrypted_archive_zip = (
        request.file_content
        if routing.decision is ArchiveDecision.IMPORT_DECRYPTED
        else None
    )

    # `route_archive_blob` has already read the zip's central directory and its
    # MANIFEST.json, so the canvas is handed the archive directly -- there is no
    # detection step left to put in front of it.
    unzip_loom_archive.signature(
        encrypted_archive_zip=encrypted_archive_zip
    ).apply_async(args=(routing.archive_zip,)).forget()
