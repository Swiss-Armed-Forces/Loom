"""Deciding whether a blob is a loom archive.

Lives in `common` so that the crawler can reach it too: crawler depends on `common` and
`minio` only (backend/crawler/pyproject.toml), so it cannot import anything under
`worker`, where the archive router (`worker.create_archive.index_archive`) calls the
same functions.

The crawler needs this because it is the one component holding an S3 client pointed at
the object, which lets it classify an intake object from a handful of range reads
instead of downloading the body -- see crawler/archive_prescreen.py.
"""

import logging
import lzma
import struct
import zlib
from typing import IO
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

from pydantic import ValidationError

from common.archive.archive_encryption_service import (
    LOOM_ARCHIVE_MAGIC_BYTES,
    ArchiveEncryptionService,
)
from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive

logger = logging.getLogger(__name__)

# Restated rather than imported from
# worker.create_archive.tasks.archive_cli._constants, and that is deliberate:
# archive_cli is *vendored into every archive*. compress_files._cli_entries
# copies each .py file in that package verbatim into the zip, where it runs from
# an extracted folder with nothing but a standard Python installation -- so an
# import of `common` there would break every archive ever extracted.
#
# tests/test_archive_detection.py asserts the two spellings agree, which is what
# keeps this copy from drifting.
MANIFEST_FILENAME = "MANIFEST.json"

# The `.loom` container's first bytes. Not a filename heuristic: this is the
# header ArchiveEncryptionService actually writes.
#
# Deliberately NOT encryption_service.DEFAULT_ENCRYPTED_MAGIC_BYTES (`LOOMENC`).
# ArchiveEncryptionService overrides that default with its own marker, so an
# encrypted archive never carries the generic one, and detecting on it would
# classify every `.loom` as an ordinary file.
ENCRYPTED_ARCHIVE_MAGIC = LOOM_ARCHIVE_MAGIC_BYTES


def is_encrypted_archive_header(head: bytes) -> bool:
    """True when `head` opens with the loom encrypted-container magic."""
    return head.startswith(ENCRYPTED_ARCHIVE_MAGIC)


def is_loom_archive_manifest(manifest: bytes) -> bool:
    """True when `manifest` is a MANIFEST.json this Loom knows how to import."""
    try:
        parsed = Archive.model_validate_json(manifest)
    except ValidationError:
        return False

    if parsed.version != LOOM_ARCHIVE_VERSION:
        logger.warning("Unsupported loom archive version: %s", parsed.version)
        return False

    return True


def find_manifest_entry(names: list[str]) -> str | None:
    """Return the archive's MANIFEST.json entry, or None.

    Matched by suffix rather than by equality because a loom archive nests its contents
    under a single timestamped directory, so the manifest is always one level down.
    """
    return next((n for n in names if n.endswith(f"/{MANIFEST_FILENAME}")), None)


# The most a MANIFEST.json is allowed to weigh before it is refused unread.
#
# A real one is a few kilobytes: `Archive` is a handful of scalar fields. The cap is
# not about those -- it is about what this function is pointed at. The crawler
# prescreen (crawler/archive_prescreen.py) runs it on every intake object, which on
# this appliance means arbitrary zips carried in on a stranger's USB stick.
# Deflate reaches roughly 1000:1, so an unbounded `read` of a member that merely
# *ends in* /MANIFEST.json inflates a 5 MB entry to ~5 GB. MemoryError is not an
# OSError and not a ValueError, so neither this except clause nor the prescreen's
# catches it: the crawler pod dies, the object was never marked processed, and the
# restarted pod picks the same one up again -- a permanent wedge on the whole intake
# path rather than one rejected file.
MAX_MANIFEST_BYTES = 4 * 1024 * 1024

# The most a zip's central directory is allowed to weigh before the zip is refused
# unopened.
#
# `ZipFile.__init__` parses the central directory eagerly: `_RealGetContents` issues a
# single `read(size_cd)`, copies the result into a BytesIO and builds one ZipInfo per
# member. The directory scales with member count rather than with compression, so it
# needs no zip bomb -- a backup zip of a few million small files carries a
# several-hundred-megabyte central directory and costs multiple gigabytes to parse,
# against the crawler's `memory: "1.5Gi"`. Under a cgroup limit that is an OOMKill
# rather than a catchable MemoryError, which is the permanent wedge MAX_MANIFEST_BYTES
# is written to prevent.
#
# 32 MiB is roughly 300k members, far past any archive this deployment writes, and
# bounds the parse at a few hundred megabytes.
MAX_CENTRAL_DIRECTORY_BYTES = 32 * 1024 * 1024

# How much of the tail to read looking for the end-of-central-directory record. The
# record is 22 bytes plus a comment of at most 65535, and a range reader serves this
# from one cached block.
_EOCD_SEARCH_BYTES = 64 * 1024 + 22

_EOCD_SIGNATURE = b"PK\x05\x06"
_ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
_ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"
_ZIP64_MARKER = 0xFFFFFFFF


def _central_directory_bytes(fd: IO[bytes]) -> int | None:
    """The size the zip declares for its central directory, or None if unreadable.

    Read straight off the end-of-central-directory record -- and the Zip64 record behind
    it when the 32-bit field is saturated -- so that the size is known *before* ZipFile
    allocates it. None means "this does not look like a zip", which leaves the verdict
    to ZipFile itself.
    """
    fd.seek(0, 2)
    size = fd.tell()
    window = min(size, _EOCD_SEARCH_BYTES)
    fd.seek(size - window)
    tail = fd.read(window)

    start = tail.rfind(_EOCD_SIGNATURE)
    if start < 0 or len(tail) - start < 22:
        return None

    declared = struct.unpack_from("<I", tail, start + 12)[0]
    if declared != _ZIP64_MARKER:
        return declared

    locator = start - 20
    if locator < 0 or tail[locator : locator + 4] != _ZIP64_LOCATOR_SIGNATURE:
        return declared
    record_offset = struct.unpack_from("<Q", tail, locator + 8)[0]
    if record_offset + 56 > size:
        return declared

    fd.seek(record_offset)
    record = fd.read(56)
    if len(record) < 56 or not record.startswith(_ZIP64_EOCD_SIGNATURE):
        return declared
    return int(struct.unpack_from("<Q", record, 40)[0])


def _central_directory_fits(fd: IO[bytes]) -> bool:
    """True when the zip's declared central directory is small enough to parse."""
    try:
        declared = _central_directory_bytes(fd)
    except (OSError, ValueError, struct.error):
        return False
    finally:
        fd.seek(0)

    if declared is not None and declared > MAX_CENTRAL_DIRECTORY_BYTES:
        logger.warning(
            "Ignoring zip with an oversized central directory: %d bytes", declared
        )
        return False
    return True


def is_loom_archive(fd: IO[bytes]) -> bool:
    """True when `fd` is a zip carrying a valid loom MANIFEST.json.

    `fd` must be seekable: ZipFile reads the end-of-central-directory record first.
    """
    try:
        if not _central_directory_fits(fd):
            return False
        with ZipFile(fd) as zip_file:
            manifest_entry = find_manifest_entry(zip_file.namelist())
            if manifest_entry is None:
                return False
            return is_loom_archive_manifest(read_manifest(zip_file, manifest_entry))
    # RuntimeError covers two more things a stranger's stick routinely carries: a
    # member that wants a password, and -- as NotImplementedError, a subclass -- a
    # compression method zipfile has no decompressor for, which is what WinZip's AES
    # ("method 99") is. Either would otherwise take the crawler pod down on an object
    # it can simply decline.
    #
    # ValueError rather than pydantic's ValidationError alone, because it subsumes it
    # *and* UnicodeDecodeError, which is what ZipFile -- not BadZipFile -- raises for a
    # central directory entry whose general-purpose bit 11 claims UTF-8 over bytes that
    # are not: CPython decodes the name with no guard, and every archive written by a
    # CP932 or GBK tool does exactly that.
    #
    # zlib.error and lzma.LZMAError inherit straight from Exception, so neither is
    # covered by the four above: a damaged deflate stream in a */MANIFEST.json member
    # -- 0.46% of random mutations of a real archive -- would otherwise escape a
    # function whose whole contract is to answer a question about a hostile blob.
    # EOFError is the same case for a truncated member.
    except (
        BadZipFile,
        ValueError,
        OSError,
        RuntimeError,
        zlib.error,
        lzma.LZMAError,
        EOFError,
    ):
        return False


def read_manifest(zip_file: ZipFile, entry: str) -> bytes:
    """The manifest member, or b"" when it is too big to be one.

    The compression method is checked first, then the declared size -- which costs
    nothing and rejects the honest zip bomb -- and then the read itself is bounded
    anyway, because the central directory is attacker-controlled and may understate what
    the member inflates to.
    """
    info = zip_file.getinfo(entry)

    # `ZipExtFile.read(n)` is output-bounded only for ZIP_DEFLATED, where `_read1` calls
    # `decompress(data, n)`. Every other method takes the `else` branch and calls
    # `self._decompressor.decompress(data)` with no max_length, truncating to the
    # declared file_size only once the whole thing is already in memory -- so both
    # guards below read an already-truncated value and see nothing. A 759-byte zip with
    # one bzip2 member declaring file_size=100 costs 1.6 GiB that way, which on the
    # crawler's `memory: "1.5Gi"` is an OOMKill. compress_files.py only ever writes
    # ZIP_DEFLATED, so refusing anything else costs this deployment nothing.
    if info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
        logger.warning(
            "Ignoring archive manifest with unsupported compression method %s: %s",
            info.compress_type,
            entry,
        )
        return b""

    if info.file_size > MAX_MANIFEST_BYTES:
        logger.warning("Ignoring oversized archive manifest: %s", entry)
        return b""

    with zip_file.open(entry) as member:
        payload = member.read(MAX_MANIFEST_BYTES + 1)

    if len(payload) > MAX_MANIFEST_BYTES:
        logger.warning("Ignoring oversized archive manifest: %s", entry)
        return b""
    return payload


# What a loom archive's *plaintext* opens with. compress_files.py writes every
# archive as `zipfile.ZipFile(buf, mode="w", allowZip64=True)` and adds members
# through ZipInfo, and an archive always contains at least MANIFEST.json -- so the
# first bytes are always a local file header, never an empty-archive EOCD.
ZIP_LOCAL_FILE_HEADER = b"PK\x03\x04"


def encrypted_probe_length(service: ArchiveEncryptionService) -> int:
    """How many bytes of an encrypted archive `decrypts_to_a_loom_zip` needs."""
    return service.header_size + len(ZIP_LOCAL_FILE_HEADER)


def decrypts_to_a_loom_zip(service: ArchiveEncryptionService, head: bytes) -> bool:
    """True when `head` decrypts, under this deployment's key, to something zip-shaped.

    The cheap half of "can this box open this archive". Reading the MAC would settle it
    properly, but GCM puts the MAC at the tail, so asking `get_decrypted_stream` means
    transferring the entire object -- hundreds of gigabytes to learn that a `.loom`
    carried in from another box was never ours to begin with.

    A foreign archive is an ordinary case here rather than an exotic one, because the
    key is per deployment: `preInstall.generateSecret` mints one per cluster. Note what
    *unset* means, though -- `Settings.parse_archive_enc_master_key` substitutes the
    published all-zero `FIXED_AES_KEY` rather than inventing a random one, so two
    deployments that were never given a key read each other's archives.

    Answering False is cheap and safe: the blob is indexed as the opaque file it is.
    Answering True commits only to *attempting* a real decrypt, which verifies the MAC
    and still falls back if it fails -- so a false positive costs one wasted pass and
    reaches the same outcome. See `FileEncryptionService.decrypt_prefix` on why the
    plaintext here is unauthenticated.
    """
    return (
        service.decrypt_prefix(head, len(ZIP_LOCAL_FILE_HEADER))
        == ZIP_LOCAL_FILE_HEADER
    )
