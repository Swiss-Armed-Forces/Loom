"""index_archive_task must never drop a blob.

What this guards is specific: a blob that is neither an encrypted archive nor a plain
one must still produce a File entry and an index entry, because the endpoint answers 202
before any of this runs and a dropped blob leaves no error behind.

Everything that can be is driven through `route_archive_blob(content, services)`, which
takes its services as an argument. Only the tests that go through the Celery task itself
-- which resolves its own -- install anything globally, and those do it through the
`install_services` fixture so it is put back afterwards.
"""

import io
import json
import zipfile
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from common.archive.archive_detection import ENCRYPTED_ARCHIVE_MAGIC, MANIFEST_FILENAME
from common.archive.archive_encryption_service import ArchiveEncryptionService
from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive
from common.dependencies import (
    get_file_storage_service,
    get_task_scheduling_service,
)
from common.services.encryption_service import AESMasterKey
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import ArchiveImportRequest

from worker.create_archive.index_archive import (
    ArchiveDecision,
    ArchiveServices,
    _unpack_fits_on_disk,
    index_archive_task,
    route_archive_blob,
)
from worker.create_archive.infra.archive_processing_task import ArchiveProcessingTask

ARCHIVE_ROOT_DIR = "loom_archive_2026-06-07_09_14_40.812597"
FULL_NAME = "//loom-intake/usb-crawled/KINGSTON-4c53/report.zip"
SOURCE_ID = "crawler/loom-intake"
THRESHOLD_BYTES = 64
UPLOADED_AT = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)


class _CountingFileStorage(InMemoryFileStorageLazyBytesService):
    """An in-memory store that records every *full* transfer of an object.

    `load_seekable` serves reads from ranges and is the cheap path by design, so it is
    deliberately not counted. `_load_to` and `_load_to_generator` move the whole object,
    and are what an expensive decision looks like.
    """

    def __init__(self, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self.full_transfer_bytes = 0

    @property
    def stored_objects(self) -> int:
        """How many objects the store is holding, which is what a leak shows up in."""
        return len(self._storage)

    def _load_to(self, service_id, dst):
        self.full_transfer_bytes += len(self._storage[service_id])
        super()._load_to(service_id, dst)

    def _load_to_generator(self, service_id):
        self.full_transfer_bytes += len(self._storage[service_id])
        yield from super()._load_to_generator(service_id)


class _SeekableFailsAfter(_CountingFileStorage):
    """Storage whose Nth seekable read raises, to reach the routing failure path."""

    def __init__(self, *, threshold_bytes: int, allowed_reads: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self._allowed_reads = allowed_reads

    def _load_seekable(self, service_id):
        if self._allowed_reads <= 0:
            raise OSError("connection reset by peer")
        self._allowed_reads -= 1
        return super()._load_seekable(service_id)


class _OversizedBlob(_CountingFileStorage):
    """Storage that reports an enormous object without holding one.

    The size ceiling is about disks, not about bytes in a test: reporting the size is
    the one thing that has to be large.
    """

    reported_size = 10**18

    def size(self, lazy_bytes) -> int:
        return self.reported_size


@pytest.fixture(name="storage")
def storage_fixture() -> _CountingFileStorage:
    """Storage that round-trips real bytes and can say what a decision cost.

    Real bytes because classification reads them: `mock_init`'s MagicMock cannot
    answer a range read.
    """
    return _CountingFileStorage(threshold_bytes=THRESHOLD_BYTES)


@pytest.fixture(name="services")
def services_fixture(storage) -> ArchiveServices:
    """Routing's dependencies, with a real encryptor on a key nothing else knows.

    Real, because the undecryptable case has to fail the way it does in production --
    through PyCryptodome's MAC check -- rather than by a MagicMock returning a MagicMock
    from `get_decrypted_stream`.
    """
    return ArchiveServices(
        file_storage=storage, encryption=ArchiveEncryptionService(AESMasterKey())
    )


@pytest.fixture(name="dispatched_files")
def dispatched_files_fixture():
    """Capture what the router sends down the ordinary file-indexing path."""
    scheduling_service = get_task_scheduling_service()
    scheduling_service.dispatch_index_file.reset_mock()
    return scheduling_service.dispatch_index_file


@pytest.fixture(name="task_services")
def task_services_fixture(install_services, services, storage) -> ArchiveServices:
    """The same services, but where `index_archive_task` will find them.

    The task takes no arguments -- it is the Celery entry point -- so this is the one
    place the dependency globals have to be stood in for. The fixture puts them back.
    """
    install_services(file_storage=storage, archive_encryption=services.encryption)
    return services


def _manifest(version: int = LOOM_ARCHIVE_VERSION) -> bytes:
    archive = Archive(
        query=QueryParameters(query_id="q", search_string="*"),
        created_at=datetime(2026, 6, 7, 9, 14, 40),
    )
    payload = json.loads(archive.model_dump_json())
    payload["version"] = version
    return json.dumps(payload).encode()


def _loom_archive_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr(f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}", _manifest())
    return buffer.getvalue()


def _encrypted(services: ArchiveServices, payload: bytes) -> bytes:
    return b"".join(services.encryption.get_encrypted_stream(iter([payload])))


def _request(payload: bytes) -> ArchiveImportRequest:
    return ArchiveImportRequest(
        file_content=get_file_storage_service().from_bytes(payload),
        full_name=FULL_NAME,
        source_id=SOURCE_ID,
        # Aware, like every writer of this field: it is indexed as an Elasticsearch
        # Date and ordered on, and the fallback path below is what carries it through.
        uploaded_datetime=UPLOADED_AT,
    )


def _run_task(request: ArchiveImportRequest, *, last_attempt: bool = True) -> None:
    """Call the bound task with a stand-in for the task instance.

    `app.task` is a no-op decorator under the mocked dependencies, so `bind=True`
    injects nothing and the caller supplies `self`. Only `is_last_attempt` is read.
    """
    task = MagicMock(spec=ArchiveProcessingTask)
    task.is_last_attempt = last_attempt
    index_archive_task(task, request)


@pytest.mark.usefixtures("task_services")
def test_a_plain_file_is_indexed_rather_than_dropped(dispatched_files):
    _run_task(_request(b"%PDF-1.7\nnot an archive at all"))

    dispatched_files.assert_called_once()
    assert dispatched_files.call_args.kwargs["full_name"] == FULL_NAME
    assert dispatched_files.call_args.kwargs["source_id"] == SOURCE_ID
    # The provenance is the whole reason `ArchiveImportRequest` carries these: without
    # them the fallback has nothing to index the blob *as*. Asserted here because
    # `_index_as_ordinary_file` could drop either and nothing else would notice.
    assert dispatched_files.call_args.kwargs["uploaded_datetime"] == UPLOADED_AT
    assert dispatched_files.call_args.kwargs["parent_id"] is None


@pytest.mark.usefixtures("task_services")
def test_an_ordinary_zip_is_indexed_rather_than_dropped(dispatched_files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("notes/report.pdf", b"no manifest here")

    _run_task(_request(buffer.getvalue()))

    dispatched_files.assert_called_once()


@pytest.mark.usefixtures("task_services")
def test_an_undecryptable_loom_blob_is_indexed_rather_than_dropped(dispatched_files):
    """The common case for a `.loom` carried in from another box.

    The key is per deployment -- `preInstall.generateSecret` mints one per cluster -- so
    a container built elsewhere does not open here. (Unset means the published all-zero
    `FIXED_AES_KEY` rather than a random one, so two deployments that were never given a
    key are the exception.) This blob is not a real container at all.
    """
    _run_task(_request(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096))

    dispatched_files.assert_called_once()
    assert dispatched_files.call_args.kwargs["full_name"] == FULL_NAME


def test_a_real_archive_routes_to_the_plain_import(services, storage):
    routing = route_archive_blob(storage.from_bytes(_loom_archive_bytes()), services)

    assert routing.decision is ArchiveDecision.IMPORT_PLAIN
    assert routing.archive_zip is not None


def test_a_real_encrypted_archive_routes_to_the_decrypted_import(services, storage):
    """End to end through the real encryptor, with a key that does fit."""
    encrypted = _encrypted(services, _loom_archive_bytes())

    routing = route_archive_blob(storage.from_bytes(encrypted), services)

    assert routing.decision is ArchiveDecision.IMPORT_DECRYPTED
    assert routing.archive_zip is not None


def test_an_undecryptable_blob_routes_to_the_file_path(services, storage):
    routing = route_archive_blob(
        storage.from_bytes(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096), services
    )

    assert routing.decision is ArchiveDecision.INDEX_AS_FILE
    assert routing.archive_zip is None


def test_a_truncated_archive_of_our_own_is_indexed_rather_than_dropped(
    services, storage
):
    """The branch the cheap header probe cannot catch, by construction.

    The header says the key fits -- it really is this deployment's archive -- but the
    MAC at the tail fails, which is what a `.loom` truncated by a stick pulled mid-copy
    looks like. It must come back as a file to index, and with a reason distinct from
    "the key does not fit": the two have different causes.
    """
    encrypted = _encrypted(services, _loom_archive_bytes())
    truncated = encrypted[: len(encrypted) - 32]

    routing = route_archive_blob(storage.from_bytes(truncated), services)

    assert routing.decision is ArchiveDecision.INDEX_AS_FILE
    assert routing.archive_zip is None
    assert routing.reason == "encrypted, and decryption failed"


def test_an_encrypted_blob_that_is_not_an_archive_is_indexed_rather_than_dropped(
    services, storage
):
    """Our own key, a clean decrypt, and a zip with no manifest in it.

    The object count is the second half of this, and the expensive half: decrypting
    wrote a full plaintext copy into permanent storage, and the routing that follows
    carries None, so nothing downstream holds its service id and no File entity ever
    references it. Left behind it is a permanent leak the size of the archive, on a
    single-disk appliance, now reached unattended off a USB stick.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("notes/report.pdf", b"no manifest here")
    encrypted = _encrypted(services, buffer.getvalue())
    file_content = storage.from_bytes(encrypted)
    stored_before = storage.stored_objects

    routing = route_archive_blob(file_content, services)

    assert routing.decision is ArchiveDecision.INDEX_AS_FILE
    assert routing.reason == "decrypted, but not a loom archive"
    assert storage.stored_objects == stored_before


def test_a_blob_that_cannot_even_be_inspected_is_indexed_rather_than_dropped(
    install_services, services, dispatched_files
):
    """The never-drop guarantee has to survive the decision itself failing.

    Everything routing does is parse attacker-shaped bytes off a stranger's stick, so
    "deciding what this is raised" is a real outcome -- and letting it out of the task
    loses the blob outright: the app sets `task_acks_late` together with
    `task_acks_on_failure_or_timeout`, so a failed task is acked rather than
    redelivered, nothing is dead-lettered to `graveyard`, and the endpoint answered 202
    long ago.
    """

    class _UnreadableStorage(InMemoryFileStorageLazyBytesService):
        def _load_seekable(self, service_id):
            del service_id  # unused
            raise OSError("connection reset by peer")

    storage = _UnreadableStorage(threshold_bytes=THRESHOLD_BYTES)
    install_services(file_storage=storage, archive_encryption=services.encryption)

    _run_task(_request(b"%PDF-1.7\nsomething went wrong reading this"))

    dispatched_files.assert_called_once()
    assert dispatched_files.call_args.kwargs["full_name"] == FULL_NAME


@pytest.mark.usefixtures("task_services")
def test_a_foreign_loom_blob_is_rejected_without_transferring_it(
    storage, dispatched_files
):
    """The cost of the decision, not its correctness.

    Answering "does this key fit?" by running the decryption would mean streaming every
    byte -- GCM's MAC sits at the tail -- and writing every decrypted byte back into
    storage before raising. On a several-hundred gigabyte `.loom` that is a full round
    trip to produce `return None`, and since `archive_enc_master_key` is per-deployment
    it would happen to *every* archive carried in from another box.

    The header probe settles it from ~61 bytes, so nothing may be transferred at all.
    """
    request = _request(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096)
    storage.full_transfer_bytes = 0

    _run_task(request)

    assert storage.full_transfer_bytes == 0
    dispatched_files.assert_called_once()


def test_a_decrypted_copy_is_removed_when_inspecting_it_raises(services, storage):
    """The failure path of the same leak the test above covers for the clean path.

    Reading the decrypted copy is reading an attacker-shaped zip, so it is exactly where
    this raises -- and the copy is a full-size plaintext archive in permanent storage
    that nothing downstream holds the id of.
    """
    # One seekable read is allowed -- the header probe -- and the next one, over the
    # decrypted copy, fails.
    storage = _SeekableFailsAfter(threshold_bytes=THRESHOLD_BYTES, allowed_reads=1)
    file_content = storage.from_bytes(_encrypted(services, _loom_archive_bytes()))
    stored_before = storage.stored_objects

    with pytest.raises(OSError):
        route_archive_blob(
            file_content,
            ArchiveServices(file_storage=storage, encryption=services.encryption),
        )

    assert storage.stored_objects == stored_before


def test_an_unattended_archive_that_cannot_fit_three_times_over_is_declined():
    """The unpack wants three concurrent copies in `tempfile_dir`.

    On a single-disk appliance, with no operator in front of it, filling the disk takes
    the deployment down -- while declining costs only that the blob is indexed as the
    zip it is.
    """
    assert _unpack_fits_on_disk(1) is True
    assert _unpack_fits_on_disk(10**18) is False


def test_an_unattended_oversized_archive_is_indexed_as_a_file(services):
    huge = _OversizedBlob(threshold_bytes=THRESHOLD_BYTES)
    file_content = huge.from_bytes(_loom_archive_bytes())

    routing = route_archive_blob(
        file_content,
        ArchiveServices(file_storage=huge, encryption=services.encryption),
        unattended=True,
    )

    assert routing.decision is ArchiveDecision.INDEX_AS_FILE
    assert "too large to unpack unattended" in routing.reason


def test_an_operator_supplied_oversized_archive_is_still_imported(services):
    """The ceiling is about the unattended path; an operator asked for this one."""
    huge = _OversizedBlob(threshold_bytes=THRESHOLD_BYTES)
    file_content = huge.from_bytes(_loom_archive_bytes())

    routing = route_archive_blob(
        file_content,
        ArchiveServices(file_storage=huge, encryption=services.encryption),
        unattended=False,
    )

    assert routing.decision is ArchiveDecision.IMPORT_PLAIN


def test_a_plain_archive_is_routed_without_transferring_it(services, storage):
    """Detection reads structure, so it has no reason to move the body."""
    file_content = storage.from_bytes(_loom_archive_bytes())
    storage.full_transfer_bytes = 0

    routing = route_archive_blob(file_content, services)

    assert routing.decision is ArchiveDecision.IMPORT_PLAIN
    assert storage.full_transfer_bytes == 0


def test_an_archive_this_box_can_open_is_still_fully_decrypted(services, storage):
    """The probe must not become a substitute for authentication.

    It is unauthenticated by construction, so a blob that passes it still has to go
    through the real decrypt and have its MAC verified before anything is imported.
    """
    encrypted = _encrypted(services, _loom_archive_bytes())
    file_content = storage.from_bytes(encrypted)
    storage.full_transfer_bytes = 0

    routing = route_archive_blob(file_content, services)

    assert routing.decision is ArchiveDecision.IMPORT_DECRYPTED
    assert storage.full_transfer_bytes >= len(encrypted)
