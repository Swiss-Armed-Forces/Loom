"""index_archive_task must never drop a blob.

The regression this guards is specific: the old canvas ran two chains that each
returned None when their case did not apply, so a blob that was neither an
encrypted archive nor a plain one produced no File entry, no index entry and no
error -- the endpoint had already answered 202.
"""

import io
import json
import zipfile
from datetime import datetime

import pytest
from common import dependencies
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
    index_archive_task,
    route_archive_blob,
)

ARCHIVE_ROOT_DIR = "loom_archive_2026-06-07_09_14_40.812597"
FULL_NAME = "//loom-intake/usb-crawled/KINGSTON-4c53/report.zip"
SOURCE_ID = "crawler/loom-intake"


@pytest.fixture(autouse=True)
def real_services(file_storage_service_inmemory):
    """Swap in services that behave, where mock_init's MagicMocks cannot.

    The storage service has to round-trip real bytes, because classification reads them.
    The archive encryption service has to be a real one on a random key, so that the
    undecryptable case fails the way it does in production -- through PyCryptodome's MAC
    check -- rather than returning a MagicMock from get_decrypted_stream.
    """
    dependencies._archive_encryption_service = (  # pylint: disable=protected-access
        ArchiveEncryptionService(AESMasterKey())
    )
    return file_storage_service_inmemory


@pytest.fixture(name="dispatched_files")
def dispatched_files_fixture():
    """Capture what the router sends down the ordinary file-indexing path."""
    scheduling_service = get_task_scheduling_service()
    scheduling_service.dispatch_index_file.reset_mock()
    return scheduling_service.dispatch_index_file


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


def _request(payload: bytes) -> ArchiveImportRequest:
    return ArchiveImportRequest(
        file_content=get_file_storage_service().from_bytes(payload),
        full_name=FULL_NAME,
        source_id=SOURCE_ID,
        uploaded_datetime=datetime(2026, 9, 18, 12, 0, 0),
    )


def test_a_plain_file_is_indexed_rather_than_dropped(dispatched_files):
    index_archive_task(_request(b"%PDF-1.7\nnot an archive at all"))

    dispatched_files.assert_called_once()
    assert dispatched_files.call_args.kwargs["full_name"] == FULL_NAME
    assert dispatched_files.call_args.kwargs["source_id"] == SOURCE_ID


def test_an_ordinary_zip_is_indexed_rather_than_dropped(dispatched_files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("notes/report.pdf", b"no manifest here")

    index_archive_task(_request(buffer.getvalue()))

    dispatched_files.assert_called_once()


def test_an_undecryptable_loom_blob_is_indexed_rather_than_dropped(dispatched_files):
    """The common case for a `.loom` carried in from another box.

    archive_enc_master_key is unset by default, so FileEncryptionService invents a
    random key per process and this never decrypts.
    """
    index_archive_task(_request(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096))

    dispatched_files.assert_called_once()
    assert dispatched_files.call_args.kwargs["full_name"] == FULL_NAME


def test_a_real_archive_routes_to_the_plain_import():
    routing = route_archive_blob(
        get_file_storage_service().from_bytes(_loom_archive_bytes())
    )

    assert routing.decision is ArchiveDecision.IMPORT_PLAIN
    assert routing.archive_zip is not None


def test_a_real_encrypted_archive_routes_to_the_decrypted_import():
    """End to end through the real encryptor, with a key that does fit."""
    master_key = AESMasterKey()
    dependencies._archive_encryption_service = (  # pylint: disable=protected-access
        ArchiveEncryptionService(master_key)
    )
    encrypted = b"".join(
        ArchiveEncryptionService(master_key).get_encrypted_stream(
            iter([_loom_archive_bytes()])
        )
    )

    routing = route_archive_blob(get_file_storage_service().from_bytes(encrypted))

    assert routing.decision is ArchiveDecision.IMPORT_DECRYPTED
    assert routing.archive_zip is not None


def test_an_undecryptable_blob_routes_to_the_file_path():
    routing = route_archive_blob(
        get_file_storage_service().from_bytes(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096)
    )

    assert routing.decision is ArchiveDecision.INDEX_AS_FILE
    assert routing.archive_zip is None


class _CountingFileStorage(InMemoryFileStorageLazyBytesService):
    """An in-memory store that records every *full* transfer of an object.

    `load_seekable` serves reads from ranges and is the cheap path by design, so it is
    deliberately not counted. `_load_to` and `_load_to_generator` move the whole object,
    and are what an expensive decision looks like.
    """

    def __init__(self, *, threshold_bytes: int):
        super().__init__(threshold_bytes=threshold_bytes)
        self.full_transfer_bytes = 0

    def _load_to(self, service_id, dst):
        self.full_transfer_bytes += len(self._storage[service_id])
        super()._load_to(service_id, dst)

    def _load_to_generator(self, service_id):
        self.full_transfer_bytes += len(self._storage[service_id])
        yield from super()._load_to_generator(service_id)


@pytest.fixture(name="counting_storage")
def counting_storage_fixture():
    """Inject a storage service that can say how many bytes a decision cost.

    Replaces the one `real_services` installed, and inherits its threshold so that the
    embedded-versus-stored boundary stays where the rest of the module expects it.
    `real_services` is autouse, so it has already run by the time this does.
    """
    storage = _CountingFileStorage(
        threshold_bytes=get_file_storage_service().threshold_bytes
    )
    dependencies._file_storage_service = storage  # pylint: disable=protected-access
    return storage


def test_a_foreign_loom_blob_is_rejected_without_transferring_it(
    counting_storage, dispatched_files
):
    """The cost regression, not the correctness one.

    Routing used to answer "does this key fit?" by running the decryption: GCM's MAC
    sits at the tail, so `get_decrypted_stream` had to stream every byte -- and write
    every decrypted byte back into storage -- before raising. On a several-hundred
    gigabyte `.loom` that is a full round trip to produce `return None`, and since
    `archive_enc_master_key` is per-deployment it happened to *every* archive carried in
    from another box.

    The header probe settles it from ~61 bytes, so nothing may be transferred at all.
    """
    request = _request(ENCRYPTED_ARCHIVE_MAGIC + b"\x7f" * 4096)
    counting_storage.full_transfer_bytes = 0

    index_archive_task(request)

    assert counting_storage.full_transfer_bytes == 0
    dispatched_files.assert_called_once()


def test_a_plain_archive_is_routed_without_transferring_it(counting_storage):
    """Detection reads structure, so it has no reason to move the body."""
    file_content = counting_storage.from_bytes(_loom_archive_bytes())
    counting_storage.full_transfer_bytes = 0

    routing = route_archive_blob(file_content)

    assert routing.decision is ArchiveDecision.IMPORT_PLAIN
    assert counting_storage.full_transfer_bytes == 0


def test_an_archive_this_box_can_open_is_still_fully_decrypted(counting_storage):
    """The probe must not become a substitute for authentication.

    It is unauthenticated by construction, so a blob that passes it still has to go
    through the real decrypt and have its MAC verified before anything is imported.
    """
    master_key = AESMasterKey()
    dependencies._archive_encryption_service = (  # pylint: disable=protected-access
        ArchiveEncryptionService(master_key)
    )
    encrypted = b"".join(
        ArchiveEncryptionService(master_key).get_encrypted_stream(
            iter([_loom_archive_bytes()])
        )
    )
    file_content = counting_storage.from_bytes(encrypted)
    counting_storage.full_transfer_bytes = 0

    routing = route_archive_blob(file_content)

    assert routing.decision is ArchiveDecision.IMPORT_DECRYPTED
    assert counting_storage.full_transfer_bytes >= len(encrypted)
