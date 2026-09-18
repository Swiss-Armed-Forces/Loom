import io
import json
import zipfile
from datetime import datetime

import pytest

from common.archive.archive_detection import (
    ENCRYPTED_ARCHIVE_MAGIC,
    MANIFEST_FILENAME,
    find_manifest_entry,
    is_encrypted_archive_header,
    is_loom_archive,
    is_loom_archive_manifest,
)
from common.archive.archive_encryption_service import ArchiveEncryptionService
from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive
from common.services.encryption_service import AESMasterKey
from common.services.query_builder import QueryParameters

ARCHIVE_ROOT_DIR = "loom_archive_2026-06-07_09_14_40.812597"


def _manifest(version: int = LOOM_ARCHIVE_VERSION) -> bytes:
    archive = Archive(
        query=QueryParameters(query_id="q", search_string="*"),
        created_at=datetime(2026, 6, 7, 9, 14, 40),
    )
    payload = json.loads(archive.model_dump_json())
    payload["version"] = version
    return json.dumps(payload).encode()


def _zip(entries: dict[str, bytes]) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        for name, content in entries.items():
            zip_file.writestr(name, content)
    buffer.seek(0)
    return buffer


def test_detects_a_loom_archive():
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()})

    assert is_loom_archive(archive) is True


def test_rejects_a_plain_zip():
    assert is_loom_archive(_zip({"report.pdf": b"not a manifest"})) is False


def test_rejects_a_manifest_at_the_archive_root():
    """The manifest always sits one level down, under the timestamped folder.

    A bare MANIFEST.json at the root is not the layout unzip_loom_archive expects, so
    accepting it would route a file into a pipeline that cannot unpack it.
    """
    assert is_loom_archive(_zip({MANIFEST_FILENAME: _manifest()})) is False


def test_rejects_an_unsupported_archive_version():
    archive = _zip(
        {f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest(LOOM_ARCHIVE_VERSION + 1)}
    )

    assert is_loom_archive(archive) is False


def test_rejects_a_manifest_that_is_not_an_archive():
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": b'{"nope": true}'})

    assert is_loom_archive(archive) is False


def test_rejects_a_non_zip():
    assert is_loom_archive(io.BytesIO(b"%PDF-1.7\nnot a zip at all")) is False


def test_rejects_a_truncated_zip():
    truncated = _zip(
        {f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()}
    ).getvalue()

    assert is_loom_archive(io.BytesIO(truncated[: len(truncated) // 2])) is False


def test_rejects_an_empty_blob():
    assert is_loom_archive(io.BytesIO(b"")) is False


@pytest.mark.parametrize(
    "head,expected",
    [
        (ENCRYPTED_ARCHIVE_MAGIC + b"\x00" * 64, True),
        (ENCRYPTED_ARCHIVE_MAGIC, True),
        (b"PK\x03\x04", False),
        (b"", False),
        (ENCRYPTED_ARCHIVE_MAGIC[:-1], False),
    ],
)
def test_encrypted_header_detection(head: bytes, expected: bool):
    assert is_encrypted_archive_header(head) is expected


def test_find_manifest_entry_picks_the_nested_manifest():
    names = [
        f"{ARCHIVE_ROOT_DIR}/README.md",
        f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}",
        f"{ARCHIVE_ROOT_DIR}/files/report.pdf",
    ]

    assert find_manifest_entry(names) == f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}"


def test_find_manifest_entry_returns_none_when_absent():
    assert find_manifest_entry([f"{ARCHIVE_ROOT_DIR}/files/report.pdf"]) is None


def test_manifest_validation_rejects_garbage():
    assert is_loom_archive_manifest(b"not json at all") is False


def test_magic_matches_what_the_archive_encryptor_actually_writes():
    """Tie the constant to the real encoder, not to itself.

    ArchiveEncryptionService overrides FileEncryptionService's generic `LOOMENC` marker
    with its own, so a detector built on the generic default would classify every .loom
    as an ordinary file. Asserting against a freshly encrypted stream is what makes that
    impossible to reintroduce.
    """
    service = ArchiveEncryptionService(AESMasterKey())

    encrypted = b"".join(service.get_encrypted_stream(iter([b"payload"])))

    assert is_encrypted_archive_header(encrypted)
