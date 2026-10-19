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
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from common.archive.archive_detection import (
    decrypts_to_a_loom_zip,
    encrypted_probe_length,
    is_encrypted_archive_header,
    is_loom_archive,
)
from common.archive.archive_encryption_service import ArchiveEncryptionService
from common.dependencies import (
    get_archive_encryption_service,
    get_celery_app,
    get_file_storage_service,
    get_task_scheduling_service,
)
from common.services.lazybytes_service import (
    FileStorageLazyBytes,
    FileStorageTag,
    LazyBytesService,
)
from common.services.task_scheduling_service import ArchiveImportRequest
from common.settings import settings
from minio.error import MinioException, S3Error

from worker.create_archive.decrypt_archive import decrypt_loom_archive
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask
from worker.create_archive.tasks import unzip_loom_archive

logger = logging.getLogger(__name__)

app = get_celery_app()

# How many simultaneous copies of the archive the unpack wants on local disk.
#
# `unzip_loom_archive` is a group of three branches, each of which independently calls
# `load_file(archive_zip)` -- a full download plus a full copy into `tempfile_dir` --
# and being a group they run at the same time.
UNZIP_CONCURRENT_COPIES = 3

# How many retries a transport fault gets before the blob is indexed as a plain file.
INDEX_ARCHIVE_MAX_RETRIES = 5


@dataclass(frozen=True)
class ArchiveServices:
    """What deciding what a blob is takes from the outside world.

    Passed in rather than looked up inside each helper, so that the routing can be
    exercised against real services on a known key -- the undecryptable branch only
    means anything against a real encryptor -- without any of it being patched into the
    dependency globals behind the code's back.
    """

    file_storage: LazyBytesService[FileStorageTag]
    encryption: ArchiveEncryptionService

    @classmethod
    def resolved(cls) -> "ArchiveServices":
        """The deployment's own, read at call time rather than at import time."""
        return cls(
            file_storage=get_file_storage_service(),
            encryption=get_archive_encryption_service(),
        )


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
    file_content: FileStorageLazyBytes, services: ArchiveServices
) -> EncryptedBlobVerdict:
    """Answer both encryption questions from a single read of the header.

    Whether the blob is an encrypted container and whether this deployment's key opens
    it are settled from the same ~61 bytes, so they share one read rather than two.
    """
    with services.file_storage.load_seekable(file_content) as fd:
        head = fd.read(encrypted_probe_length(services.encryption))

    if not is_encrypted_archive_header(head):
        return EncryptedBlobVerdict.NOT_ENCRYPTED

    if not decrypts_to_a_loom_zip(services.encryption, head):
        return EncryptedBlobVerdict.FOREIGN_KEY

    return EncryptedBlobVerdict.DECRYPTS_TO_ZIP


def _is_importable_archive(
    file_content: FileStorageLazyBytes, services: ArchiveServices
) -> bool:
    with services.file_storage.load_seekable(file_content) as fd:
        return is_loom_archive(fd)


def _unpack_fits_on_disk(size: int) -> bool:
    """Whether three concurrent copies of this archive would fit in `tempfile_dir`.

    The appliance is a single-disk box, and the unpack is unattended there: the crawler
    routes every archive-shaped object in the intake bucket here, off a stick somebody
    carried in. Filling the disk takes the whole deployment down, while declining to
    unpack costs only that the blob is indexed as the opaque zip it is -- so the archive
    has to be measured against the free space before it is accepted.
    """
    target = settings.tempfile_dir or Path("/tmp")
    try:
        free = shutil.disk_usage(target).free
    except OSError:
        logger.warning("Could not read the free space of %s", target, exc_info=True)
        return True
    return size * UNZIP_CONCURRENT_COPIES <= free


def _route_decrypted(
    file_content: FileStorageLazyBytes, services: ArchiveServices
) -> ArchiveRouting:
    """Open a container this deployment's key fits, and route what came out.

    Its own function rather than a branch of `route_archive_blob`, because the decrypted
    copy has to be deleted on every way out that does not hand it on and that is easier
    to see -- and to keep right -- in one short scope.
    """
    decrypted = decrypt_loom_archive(
        file_content, services.file_storage, services.encryption
    )
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

    # Deleted on every way out that does not hand it on -- the failed read
    # included. `decrypt_loom_archive` has already written a full plaintext copy
    # into permanent file storage, and once this returns nothing holds its service
    # id. It is not leaked forever: `flush_file_storage_service_task` runs on the
    # beat schedule, walks the bucket from a random start point and removes objects
    # older than a day that no repository references. But that is a randomised,
    # 1000-objects-per-run, idle-gated sweep, so the copy sits on disk for at least
    # 24 hours -- on a single-disk appliance, reached unattended off a USB stick
    # rather than by an operator calling the import endpoint. Reading an
    # attacker-shaped zip is exactly where this raises, so the exception path is
    # the one that matters.
    handed_on = False
    try:
        if not _is_importable_archive(decrypted, services):
            return ArchiveRouting(
                ArchiveDecision.INDEX_AS_FILE,
                None,
                "decrypted, but not a loom archive",
            )
        handed_on = True
        return ArchiveRouting(ArchiveDecision.IMPORT_DECRYPTED, decrypted, "")
    finally:
        if not handed_on:
            services.file_storage.delete(decrypted)


def route_archive_blob(
    file_content: FileStorageLazyBytes,
    services: ArchiveServices | None = None,
    unattended: bool = False,
) -> ArchiveRouting:
    """Decide what a blob actually is, doing any decryption it takes to find out.

    Separate from the task so the decision can be tested on its own: everything
    below this line is Celery canvas plumbing, and everything above it is the
    part that used to get this wrong. `services` defaults to the deployment's own
    and is a parameter so a caller can hand in doubles -- the same shape as
    `loom_installer.install.run` taking its CommandRunner.

    `unattended` says nobody asked for this import, which is the crawler's case and
    the one where a too-large archive is declined rather than unpacked.
    """
    services = services or ArchiveServices.resolved()

    if unattended:
        size = services.file_storage.size(file_content)
        if not _unpack_fits_on_disk(size):
            return ArchiveRouting(
                ArchiveDecision.INDEX_AS_FILE,
                None,
                f"{size} bytes, too large to unpack unattended on this disk",
            )

    verdict = _inspect_encrypted_header(file_content, services)

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
        return _route_decrypted(file_content, services)

    if not _is_importable_archive(file_content, services):
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


@app.task(
    base=ArchiveProcessingTask,
    bind=True,
    # Transport faults only. A `MinioException` that is not an `S3Error` -- a connection
    # reset, an unparsable response -- is a property of the object store rather than of
    # the document, so it is worth the backoff; everything else below degrades instead.
    autoretry_for=(MinioException,),
    max_retries=INDEX_ARCHIVE_MAX_RETRIES,
    retry_backoff=True,
)
def index_archive_task(
    self: ArchiveProcessingTask, request: ArchiveImportRequest
) -> None:
    """Import a loom archive, or index the blob as a file when it is not one."""
    try:
        routing = route_archive_blob(
            request.file_content, unattended=request.unattended
        )
    # The never-drop guarantee this module exists for, held even when deciding *what*
    # the blob is fails. Everything above is parsing attacker-shaped bytes -- a zip
    # central directory, a container header -- off a stranger's USB stick. Indexing the
    # blob as the opaque thing it is stays the recoverable outcome.
    #
    # The same three as `crawler.archive_prescreen`: `S3Error` rather than the wider
    # `MinioException`, because a 404 or a 416 on this object is a verdict about the
    # object, while the rest of the family is a transport fault that the `autoretry_for`
    # above is there to ride out.
    except (OSError, ValueError, S3Error) as exc:
        logger.exception("Could not decide what '%s' is", request.full_name)
        _index_as_ordinary_file(request, f"routing failed: {exc}")
        return
    except MinioException as exc:
        # Retried by the decorator above until the budget is gone, and only then
        # degraded -- rather than failing, which would lose the blob: the app sets
        # `task_acks_late` *and* `task_acks_on_failure_or_timeout`, so an exception
        # leaving this task is acked, never redelivered, never dead-lettered to
        # `graveyard`, and the `POST /v1/archive/import` that produced it answered 202
        # long ago.
        if not self.is_last_attempt:
            raise
        logger.exception(
            "Gave up reaching the object store for '%s'", request.full_name
        )
        _index_as_ordinary_file(request, f"the object store could not be read: {exc}")
        return
    # Total, deliberately: with acks-on-failure there is no retry chain behind this
    # task, so anything that escapes is a silent drop -- an `AttributeError` or a
    # `KeyError` in the routing would disappear the file the module docstring promises
    # cannot disappear.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected failure deciding what '%s' is", request.full_name)
        _index_as_ordinary_file(request, f"routing failed: {exc}")
        return

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
    #
    # What the canvas then does with it is *not* cheap, and this is the moment to
    # say so rather than let the sentence above imply otherwise. `unzip_loom_archive`
    # is a group of three branches -- restore_archive_metadata_task,
    # store_raw_files_task, upsert_file_objects_task -- and each one independently
    # calls `load_file(archive_zip)`: a full download plus a full second copy into
    # `tempfile_dir`. Being a group they run concurrently, so a 300 GB archive wants
    # up to three simultaneous 300 GB temp files, and `dispatch_archive_file_stats_task`
    # streams the object end to end twice more for its checksum and its size.
    #
    # Pre-existing in unzip_loom_archive.py -- but the crawler prescreen now reaches
    # this path with no operator in it, so on a single-disk appliance it bites once an
    # archive passes a third of the free space. `route_archive_blob` therefore declines
    # an unattended archive that large outright, which bounds the exposure; the proper
    # fix is still a chain over one `load_file` (or one `load_file_named` path shared
    # by the three passes), with the checksum folded into the same pass.
    unzip_loom_archive.signature(
        encrypted_archive_zip=encrypted_archive_zip
    ).apply_async(args=(routing.archive_zip,)).forget()
