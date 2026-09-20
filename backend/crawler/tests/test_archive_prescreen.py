import io
import json
import zipfile
from datetime import datetime
from unittest.mock import MagicMock

from common.archive.archive_detection import ENCRYPTED_ARCHIVE_MAGIC, MANIFEST_FILENAME
from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive
from common.services.query_builder import QueryParameters
from minio import Minio
from minio.error import S3Error

from crawler.archive_prescreen import IntakeObjectKind, classify_intake_object

BUCKET = "loom-intake"
OBJECT = "usb-crawled/KINGSTON-4c53/report"
ARCHIVE_ROOT_DIR = "loom_archive_2026-06-07_09_14_40.812597"


def _manifest(version: int = LOOM_ARCHIVE_VERSION) -> bytes:
    archive = Archive(
        query=QueryParameters(query_id="q", search_string="*"),
        created_at=datetime(2026, 6, 7, 9, 14, 40),
    )
    payload = json.loads(archive.model_dump_json())
    payload["version"] = version
    return json.dumps(payload).encode()


def _zip_bytes(
    entries: dict[str, bytes],
    comment: bytes = b"",
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression) as zip_file:
        for name, content in entries.items():
            zip_file.writestr(name, content)
        zip_file.comment = comment
    return buffer.getvalue()


def _loom_archive_bytes(comment: bytes = b"") -> bytes:
    return _zip_bytes(
        {
            f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest(),
            f"{ARCHIVE_ROOT_DIR}/files/report.pdf": b"%PDF-1.7 payload" * 512,
        },
        comment=comment,
    )


class _FakeResponse:
    """What minio's get_object hands back: a urllib3-ish response."""

    def __init__(self, payload: bytes):
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class _ObjectStore:
    """Serves real byte ranges out of an in-memory object, and counts requests."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.responses: list[_FakeResponse] = []

    def get_object(
        self, bucket: str, object_name: str, offset: int = 0, length: int = 0
    ):
        assert bucket == BUCKET
        assert object_name == OBJECT
        end = offset + length if length else len(self.payload)
        response = _FakeResponse(self.payload[offset:end])
        self.responses.append(response)
        return response


def _client_for(payload: bytes) -> tuple[MagicMock, _ObjectStore]:
    store = _ObjectStore(payload)
    client = MagicMock(spec=Minio)
    client.get_object.side_effect = store.get_object
    return client, store


def _classify(payload: bytes) -> IntakeObjectKind:
    client, _ = _client_for(payload)
    return classify_intake_object(client, BUCKET, OBJECT, len(payload))


def test_detects_a_plain_loom_archive():
    assert _classify(_loom_archive_bytes()) is IntakeObjectKind.LOOM_ARCHIVE


def test_detects_an_encrypted_loom_archive():
    payload = ENCRYPTED_ARCHIVE_MAGIC + b"\x01" * 4096

    assert _classify(payload) is IntakeObjectKind.LOOM_ARCHIVE_ENCRYPTED


def test_an_ordinary_zip_is_a_plain_file():
    payload = _zip_bytes({"notes/report.pdf": b"nothing loom about this"})

    assert _classify(payload) is IntakeObjectKind.PLAIN_FILE


def test_a_pdf_is_a_plain_file():
    assert _classify(b"%PDF-1.7\n" + b"\x00" * 10_000) is IntakeObjectKind.PLAIN_FILE


def test_an_empty_object_is_a_plain_file():
    assert _classify(b"") is IntakeObjectKind.PLAIN_FILE


def test_an_unsupported_archive_version_is_a_plain_file():
    payload = _zip_bytes(
        {f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest(LOOM_ARCHIVE_VERSION + 1)}
    )

    assert _classify(payload) is IntakeObjectKind.PLAIN_FILE


def test_a_truncated_archive_is_a_plain_file():
    """A half-written object must not be mistaken for an archive."""
    payload = _loom_archive_bytes()

    assert _classify(payload[: len(payload) // 2]) is IntakeObjectKind.PLAIN_FILE


def test_an_archive_with_a_large_trailing_comment_is_still_detected():
    """The EOCD is not at a fixed offset; a comment pushes it up to 64 KiB back."""
    payload = _loom_archive_bytes(comment=b"c" * 60_000)

    assert _classify(payload) is IntakeObjectKind.LOOM_ARCHIVE


def test_a_storage_error_degrades_to_plain_file():
    """Never fail closed: a classification failure must not drop the object."""
    client = MagicMock(spec=Minio)
    client.get_object.side_effect = OSError("connection reset by peer")

    assert (
        classify_intake_object(client, BUCKET, OBJECT, 1024)
        is IntakeObjectKind.PLAIN_FILE
    )


def test_an_s3_error_degrades_to_plain_file():
    client = MagicMock(spec=Minio)
    client.get_object.side_effect = S3Error(
        code="NoSuchKey",
        message="object vanished mid-crawl",
        resource=OBJECT,
        request_id="req-1",
        host_id="host-1",
        response=None,
    )

    assert (
        classify_intake_object(client, BUCKET, OBJECT, 1024)
        is IntakeObjectKind.PLAIN_FILE
    )


def test_classification_reads_a_fraction_of_a_large_archive():
    """The whole point: classification must not stream the body.

    The big member is stored uncompressed and pseudo-random, because a compressible one
    would deflate away and prove nothing about the read volume.
    """
    filler = (bytes(range(256)) * 16_000)[:4_000_000]
    big = _zip_bytes(
        {
            f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest(),
            f"{ARCHIVE_ROOT_DIR}/files/big.bin": filler,
        },
        compression=zipfile.ZIP_STORED,
    )
    assert len(big) > 1_000_000  # the stored payload really is large
    client, store = _client_for(big)

    assert (
        classify_intake_object(client, BUCKET, OBJECT, len(big))
        is IntakeObjectKind.LOOM_ARCHIVE
    )

    fetched = sum(len(response.read()) for response in store.responses)
    assert fetched < len(big) // 4, f"read {fetched} of {len(big)} bytes"
    assert all(response.closed and response.released for response in store.responses)
