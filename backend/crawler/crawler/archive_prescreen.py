"""Deciding what an intake object is, without downloading it.

The crawler is the only component that holds an S3 client pointed at the object while it
is still in the bucket, which is what lets it classify an intake object from a handful
of range reads instead of transferring the body. The reader that makes that possible is
`common.services.s3_range_reader.S3RangeReader`; it lives in `common` because file
storage needs the same trick (`LazyBytesService.load_seekable`), but here it is pointed
straight at the intake bucket, where there is no `LazyBytes` to go through.

The classification itself is `common.archive.archive_detection`, the very function the
worker's archive router (`worker.create_archive.index_archive`) uses, so the two can
never disagree about what a loom archive is.
"""

import io
import logging
from enum import StrEnum

from common.archive.archive_detection import (
    ENCRYPTED_ARCHIVE_MAGIC,
    ZIP_LOCAL_FILE_HEADER,
    is_encrypted_archive_header,
    is_loom_archive,
)
from common.services.s3_range_reader import S3ObjectClient, S3RangeReader
from minio.error import S3Error

logger = logging.getLogger(__name__)

# Enough of the object to answer both "is this the encrypted container?" and "is this
# zip-shaped at all?" from one range read, since neither magic is longer than this.
HEAD_LENGTH = max(len(ENCRYPTED_ARCHIVE_MAGIC), len(ZIP_LOCAL_FILE_HEADER))


class IntakeObjectKind(StrEnum):
    """What a crawled intake object turned out to be."""

    PLAIN_FILE = "plain_file"
    LOOM_ARCHIVE = "loom_archive"
    LOOM_ARCHIVE_ENCRYPTED = "loom_archive_encrypted"


def classify_intake_object(
    client: S3ObjectClient, bucket: str, object_name: str, size: int
) -> IntakeObjectKind:
    """Decide whether an intake object is a loom archive, plain or encrypted.

    `LOOM_ARCHIVE` is exact: the object's own MANIFEST.json is read and validated.
    `LOOM_ARCHIVE_ENCRYPTED` is not -- it is a header match and nothing more, because
    the crawler has no `archive_enc_master_key` (see
    charts/templates/crawler/_deployment.yaml) and so cannot tell whether the container
    will open with this deployment's key. That question is settled in the worker,
    cheaply, by `index_archive._inspect_encrypted_header`.

    Falls back to `PLAIN_FILE` on anything unexpected. That direction is the recoverable
    one: an archive misrouted to the ordinary indexing pipeline is merely indexed as the
    zip it is.
    """
    try:
        reader = S3RangeReader(client, bucket, object_name, size)

        # Asked for exactly, not read through the reader. A seven-byte `read` pulls
        # a whole 64 KiB block that the zip probe below then seeks away from -- and
        # this runs on every object a USB mirror lands in the bucket, so at 300k
        # objects that is ~19 GB of range reads fetched and thrown away.
        head = reader.fetch_range(0, HEAD_LENGTH)

        if is_encrypted_archive_header(head):
            return IntakeObjectKind.LOOM_ARCHIVE_ENCRYPTED

        # Gated on the local file header, out of the bytes already in hand. Handing a
        # non-zip to ZipFile is not free: `_EndRecData` reads the trailing 22 bytes,
        # fails the signature check, then seeks back for the last ~64 KiB looking for a
        # displaced end-of-central-directory record -- two further round trips for every
        # ordinary file on a stick, which is nearly all of them.
        #
        # Exact for the archives this codebase writes: `compress_files.py` builds every
        # one as `zipfile.ZipFile(buf, mode="w")` with at least a MANIFEST.json in it, so
        # the first bytes are always a local file header. What it gives up is a loom
        # archive hidden behind a prepended self-extracting stub, which nothing here
        # produces.
        if not head.startswith(ZIP_LOCAL_FILE_HEADER):
            return IntakeObjectKind.PLAIN_FILE

        # BufferedReader for two reasons: it coalesces zipfile's many tiny reads
        # on top of the reader's block cache, and it is what makes this a plain
        # binary file object as far as ZipFile and mypy are concerned.
        with io.BufferedReader(reader) as source:
            if is_loom_archive(source):
                return IntakeObjectKind.LOOM_ARCHIVE
    # Deliberately not a bare `except Exception`: pylint's broad-exception-caught
    # is enabled, and these are the failures that actually reach here. A genuinely
    # exotic transport error propagates to the caller, which leaves the object
    # unmarked so the next poll retries it.
    except (OSError, ValueError, S3Error):
        logger.warning(
            "Could not classify intake object '%s'; treating it as a plain file",
            object_name,
            exc_info=True,
        )

    return IntakeObjectKind.PLAIN_FILE
