import io
import json
import struct
import zipfile
from datetime import datetime

import pytest

from common.archive.archive_detection import (
    ENCRYPTED_ARCHIVE_MAGIC,
    MANIFEST_FILENAME,
    MAX_CENTRAL_DIRECTORY_BYTES,
    MAX_MANIFEST_BYTES,
    ZIP_LOCAL_FILE_HEADER,
    decrypts_to_a_loom_zip,
    encrypted_probe_length,
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


def _manifest_of_size(size: int) -> bytes:
    """A manifest that still validates, padded out to exactly `size` bytes.

    Padded through an unknown key: `Archive` ignores extras, so the document is as valid
    at four megabytes as it is at four hundred bytes and only its weight differs.
    """
    payload = json.loads(_manifest())
    payload["_padding"] = ""
    payload["_padding"] = "x" * (size - len(json.dumps(payload)))
    rendered = json.dumps(payload).encode()
    assert len(rendered) == size
    return rendered


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


def test_a_zip_bomb_dressed_as_a_manifest_is_refused_unread():
    """This runs in the crawler on arbitrary zips off a stranger's USB stick.

    The honest half of the problem: a stored member that is simply enormous, caught by
    the declared size alone. The member that *lies* about its size is the case below.
    MemoryError is not caught anywhere on this path, the crawler pod dies, and because
    the object was never marked processed the restarted pod picks the same one up again
    -- the whole intake path wedges, not just the one file.
    """
    bomb = b"\0" * (MAX_MANIFEST_BYTES * 4)
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": bomb})

    assert is_loom_archive(archive) is False


def _zip_declaring(content: bytes, declared: int, method: int) -> io.BytesIO:
    """A zip whose headers understate what the single member inflates to.

    The declared size is patched in both the local file header and the central
    directory, which is where `read_manifest` reads it from. That is the shape the
    bounded read exists for: a central directory is attacker-controlled, so a member
    may claim a hundred bytes and inflate to gigabytes.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=method) as zip_file:
        zip_file.writestr(f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}", content)

    raw = bytearray(buffer.getvalue())
    lie = struct.pack("<I", declared)
    local = raw.find(b"PK\x03\x04")
    raw[local + 22 : local + 26] = lie
    central = raw.find(b"PK\x01\x02")
    raw[central + 24 : central + 28] = lie
    return io.BytesIO(bytes(raw))


def test_a_deflated_manifest_whose_header_lies_is_still_bounded():
    """The guard the declared-size check cannot make: a central directory that lies.

    Written with deflate and a small declared size, so the first check passes and only
    the bounded read stands between the crawler and a multi-gigabyte allocation. A
    stored member cannot reach this -- `file_size` is exact there -- which is why the
    rest of this suite never exercised it.
    """
    bomb = _zip_declaring(b"\0" * (MAX_MANIFEST_BYTES * 8), 128, zipfile.ZIP_DEFLATED)

    assert is_loom_archive(bomb) is False


def test_a_manifest_compressed_with_bzip2_is_refused_unread():
    """`ZipExtFile.read(n)` is output-bounded for deflate only.

    Every other method decompresses the member whole and truncates afterwards, so both
    of `read_manifest`'s guards read an already-materialised value. A 759-byte zip built
    this way costs 1.6 GiB, against the crawler's `memory: "1.5Gi"`. `compress_files.py`
    only ever writes deflate, so the method itself is the verdict.
    """
    bomb = _zip_declaring(b"\0" * (MAX_MANIFEST_BYTES * 8), 128, zipfile.ZIP_BZIP2)

    assert is_loom_archive(bomb) is False


def test_a_bzip2_manifest_is_refused_even_when_it_is_a_valid_one():
    """Stated as its own case so the refusal is known to be about the method.

    Loom never writes a bzip2 member, so nothing this deployment produced is lost by
    declining one -- and the blob still reaches the index as an opaque file.
    """
    archive = _zip_declaring(_manifest(), len(_manifest()), zipfile.ZIP_BZIP2)

    assert is_loom_archive(archive) is False


def test_a_zip_declaring_an_oversized_central_directory_is_refused_unopened():
    """ZipFile parses the whole central directory in its constructor.

    It scales with member count rather than compression, so a backup zip of a few
    million small files needs no zip bomb to exhaust the crawler's 1.5 GiB -- and an
    OOMKill under a cgroup limit is not a catchable MemoryError, so the object is never
    recorded and the restarted pod reaches it again.
    """
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()}).getvalue()
    eocd = archive.rfind(b"PK\x05\x06")
    raw = bytearray(archive)
    raw[eocd + 12 : eocd + 16] = struct.pack("<I", MAX_CENTRAL_DIRECTORY_BYTES + 1)

    assert is_loom_archive(io.BytesIO(bytes(raw))) is False


def test_a_manifest_right_at_the_cap_is_still_read():
    """The cap must not reject what it is meant to let through.

    Sized to the limit rather than to the few hundred bytes a real manifest weighs,
    because that is where `read_manifest`'s two checks actually meet: the declared size
    in the central directory, and the bounded read that does not trust it. A small
    manifest exercises neither, and simply repeats `test_detects_a_loom_archive`.
    """
    archive = _zip(
        {
            f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest_of_size(
                MAX_MANIFEST_BYTES
            )
        }
    )

    assert is_loom_archive(archive) is True


def test_a_manifest_one_byte_over_the_cap_is_refused():
    archive = _zip(
        {
            f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest_of_size(
                MAX_MANIFEST_BYTES + 1
            )
        }
    )

    assert is_loom_archive(archive) is False


def test_an_entry_name_that_lies_about_being_utf8_is_declined():
    """What a CP932 or GBK zip tool writes.

    ZipFile decodes a central directory name with `.decode("utf-8")` and no guard when
    general-purpose bit 11 is set, so a name whose bytes are not UTF-8 raises
    UnicodeDecodeError -- not BadZipFile, and not pydantic's ValidationError. On the
    worker such an error escapes the router and takes the blob round the retry chain
    into the graveyard queue with no File entity: exactly the silent disappearance this
    module exists to make impossible.
    """
    # Written with a non-ASCII name so zipfile sets bit 11, then the two UTF-8 bytes
    # are replaced in place by two that are not. Same length, so every offset in the
    # zip stays valid and only the decode is broken.
    valid = _zip({f"é{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()})
    mangled = io.BytesIO(valid.getvalue().replace(b"\xc3\xa9", b"\xff\xfe"))

    assert is_loom_archive(mangled) is False


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


def _encrypted_archive(service: ArchiveEncryptionService) -> bytes:
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()}).getvalue()
    return b"".join(service.get_encrypted_stream(iter([archive])))


def _probe_head(service: ArchiveEncryptionService, encrypted: bytes) -> bytes:
    return encrypted[: encrypted_probe_length(service)]


def test_the_matching_key_recognises_its_own_archive():
    service = ArchiveEncryptionService(AESMasterKey())

    encrypted = _encrypted_archive(service)

    assert decrypts_to_a_loom_zip(service, _probe_head(service, encrypted)) is True


def test_a_foreign_key_rejects_the_archive():
    """The case this exists for: a `.loom` carried in from another box.

    `archive_enc_master_key` is minted per cluster by `preInstall.generateSecret`, so
    this is the ordinary outcome for anything arriving on a USB stick -- and it has to
    be answered from the header, not by decrypting several hundred gigabytes to reach
    the MAC. (Two deployments that were never given a key share the published all-zero
    `FIXED_AES_KEY` instead, so there the outcome is the opposite one.)
    """
    owner = ArchiveEncryptionService(AESMasterKey())
    stranger = ArchiveEncryptionService(AESMasterKey())

    encrypted = _encrypted_archive(owner)

    assert decrypts_to_a_loom_zip(stranger, _probe_head(owner, encrypted)) is False


def test_the_probe_reads_only_the_header():
    """It must decide from the head alone -- no part of the body may be needed."""
    service = ArchiveEncryptionService(AESMasterKey())

    encrypted = _encrypted_archive(service)
    head = _probe_head(service, encrypted)

    assert len(head) == service.header_size + 4
    assert decrypts_to_a_loom_zip(service, head) is True


def test_a_truncated_head_is_rejected():
    service = ArchiveEncryptionService(AESMasterKey())

    encrypted = _encrypted_archive(service)

    assert decrypts_to_a_loom_zip(service, encrypted[:10]) is False


def test_a_plain_zip_is_not_an_encrypted_archive():
    service = ArchiveEncryptionService(AESMasterKey())

    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()}).getvalue()

    assert decrypts_to_a_loom_zip(service, archive[:200]) is False


def test_the_expected_signature_is_what_loom_actually_writes():
    """Pin the constant to a real archive rather than to itself.

    `compress_files` builds archives with `zipfile.ZipFile(..., mode="w")`, so the first
    bytes are a local file header. If that ever changed, the probe would start rejecting
    archives this deployment can open -- silently, since the fallback indexes them as
    opaque blobs.
    """
    archive = _zip({f"{ARCHIVE_ROOT_DIR}/{MANIFEST_FILENAME}": _manifest()}).getvalue()

    assert archive.startswith(ZIP_LOCAL_FILE_HEADER)
