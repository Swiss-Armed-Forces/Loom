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
    is_encrypted_archive_header,
    is_loom_archive,
)
from common.services.s3_range_reader import S3RangeReader
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class IntakeObjectKind(StrEnum):
    """What a crawled intake object turned out to be."""

    PLAIN_FILE = "plain_file"
    LOOM_ARCHIVE = "loom_archive"
    LOOM_ARCHIVE_ENCRYPTED = "loom_archive_encrypted"


def classify_intake_object(
    client: Minio, bucket: str, object_name: str, size: int
) -> IntakeObjectKind:
    """Decide whether an intake object is a loom archive, plain or encrypted.

    `LOOM_ARCHIVE` is exact: the object's own MANIFEST.json is read and validated.
    `LOOM_ARCHIVE_ENCRYPTED` is not -- it is a header match and nothing more, because
    the crawler has no `archive_enc_master_key` (see
    charts/templates/crawler/_deployment.yaml) and so cannot tell whether the container
    will open with this deployment's key. That question is settled in the worker,
    cheaply, by `index_archive._inspect_encrypted_header`.

    Falls back to `PLAIN_FILE` on anything unexpected. That direction matters: a plain
    file misrouted to the archive pipeline used to be discarded without a trace, whereas
    an archive misrouted to the ordinary indexing pipeline is merely indexed as the zip
    it is. Degrade towards the recoverable mistake.
    """
    try:
        reader = S3RangeReader(client, bucket, object_name, size)

        # Asked for exactly, not read through the reader. A seven-byte `read` pulls
        # a whole 64 KiB block that the zip probe below then seeks away from -- and
        # this runs on every object a USB mirror lands in the bucket, so at 300k
        # objects that is ~19 GB of range reads fetched and thrown away.
        if is_encrypted_archive_header(
            reader.fetch_range(0, len(ENCRYPTED_ARCHIVE_MAGIC))
        ):
            return IntakeObjectKind.LOOM_ARCHIVE_ENCRYPTED

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
