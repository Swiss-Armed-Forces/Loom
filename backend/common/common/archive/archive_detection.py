"""Deciding whether a blob is a loom archive.

Extracted from worker's `detect_loom_archive` task so that the crawler can reach it too:
crawler depends on `common` and `minio` only (backend/crawler/pyproject.toml), so it
cannot import anything under `worker`.

The crawler needs this because it is the one component holding an S3 client pointed at
the object, which lets it classify an intake object from a handful of range reads
instead of downloading the body -- see crawler/archive_prescreen.py.
"""

import logging
from typing import IO
from zipfile import BadZipFile, ZipFile

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


def is_loom_archive(fd: IO[bytes]) -> bool:
    """True when `fd` is a zip carrying a valid loom MANIFEST.json.

    `fd` must be seekable: ZipFile reads the end-of-central-directory record first.
    """
    try:
        with ZipFile(fd) as zip_file:
            manifest_entry = find_manifest_entry(zip_file.namelist())
            if manifest_entry is None:
                return False
            return is_loom_archive_manifest(zip_file.read(manifest_entry))
    except (BadZipFile, ValidationError, OSError):
        return False


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

    `archive_enc_master_key` is unset by default and every deployment then invents its
    own, so a foreign archive is the *expected* case here, not an exotic one.

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
