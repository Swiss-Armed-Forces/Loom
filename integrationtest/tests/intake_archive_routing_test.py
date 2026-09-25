"""What the crawler does with an archive it finds in the intake bucket.

This is the seam USB ingest creates, and nothing else crosses it. `crawler_test.py` only
ever puts plain files in the bucket; `create_archive_test.py` only ever imports through
`POST /v1/archive/import`. Putting an *archive* in the *bucket* is new, and it is the
whole of what `loom-usb-ingest` does -- the appliance copies bytes and leaves the
decision to the crawler, which classifies each object from a few S3 range reads
(crawler/archive_prescreen.py).

The unit tests cover each half: that the prescreen reads the right bytes, and that the
router never drops a blob. What only a live cluster can show is the two working together
over a real SeaweedFS, with real range requests rather than a MagicMock.

Every negative assertion below is made *after* a positive one that proves the object has
been through the pipeline. Asserting "no such file" against a bucket the crawler has not
polled yet would pass for the wrong reason.
"""

import io
import zipfile
from uuid import UUID

import requests
from common.archive.archive_encryption_service import LOOM_ARCHIVE_MAGIC_BYTES
from common.dependencies import get_s3_intake_client
from common.services.query_builder import QueryParameters
from crawler.settings import settings

from utils.consts import ARCHIVE_ENDPOINT, REQUEST_TIMEOUT
from utils.fetch_from_api import (
    fetch_archives_from_api,
    fetch_files_from_api,
    fetch_query_id,
    get_file_preview_by_name,
)
from utils.upload_asset import upload_asset

# The names loom-usb-ingest would produce, flattened: the object key becomes the
# file's path verbatim (S3Crawler._download_object), and a flat key keeps the
# assertions below about names rather than about how a nested path renders.
ARCHIVE_OBJECT_NAME = "loom_archive_2026-09-18_12_00_00.000000.zip"
ENCRYPTED_OBJECT_NAME = "loom_archive_2026-09-18_12_00_00.000000.loom"
PLAIN_ZIP_OBJECT_NAME = "holiday_photos.zip"


def _put_in_intake(object_name: str, payload: bytes) -> None:
    """Drop an object in the bucket, exactly as `mc mirror` would."""
    get_s3_intake_client().put_object(
        settings.intake_storage.bucket_name,
        object_name,
        io.BytesIO(payload),
        len(payload),
    )


def _create_archive_of_everything() -> UUID:
    response = requests.post(
        ARCHIVE_ENDPOINT,
        json={
            "query": (
                QueryParameters(
                    search_string="*", query_id=fetch_query_id()
                ).model_dump()
            )
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return UUID(response.json()["archive_id"])


def _download_archive(archive_id: UUID) -> bytes:
    response = requests.get(
        f"{ARCHIVE_ENDPOINT}/{archive_id}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


def test_a_loom_archive_in_the_intake_bucket_is_imported_not_indexed_as_a_zip():
    """The USB path end to end: bucket -> prescreen -> archive importer.

    Reaching `imported` is something only the archive pipeline can do, so it is
    the positive proof that the object was routed rather than indexed. The
    absence of a zip-shaped File entry afterwards is the other half: it has to go
    down one path, not both.

    An archive indexed as an opaque zip is technically not lost, but its contents
    are unsearchable -- which defeats the point of carrying it in on a stick.
    """
    upload_asset("empty_file.txt")
    get_file_preview_by_name("empty_file.txt")

    archive_id = _create_archive_of_everything()
    archives = fetch_archives_from_api()
    assert archives[0].file_id == archive_id

    _put_in_intake(ARCHIVE_OBJECT_NAME, _download_archive(archive_id))

    imported = fetch_archives_from_api(
        expected_no_of_archives=1, expected_state="imported"
    )
    # Tied back to the archive that was actually put in the bucket. The helper
    # only counts how many hits are in the expected state, so an importer that
    # created a *second* archive row would satisfy the call above and nothing
    # else here would notice.
    assert imported[0].file_id == archive_id

    # Only now is this meaningful: the import above proves the object was seen.
    fetch_files_from_api(
        search_string=f'filename:"{ARCHIVE_OBJECT_NAME}"',
        expected_no_of_files=0,
    )


def test_an_ordinary_zip_in_the_intake_bucket_is_still_indexed_as_a_file():
    """The prescreen must not route every zip to the importer.

    A zip with no MANIFEST.json is an ordinary document as far as Loom is concerned, and
    misrouting it used to mean losing it outright: the archive pipeline had no outcome
    for 'not an archive' other than doing nothing.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("holiday/beach.txt", b"not a loom archive")

    _put_in_intake(PLAIN_ZIP_OBJECT_NAME, buffer.getvalue())

    preview = get_file_preview_by_name(PLAIN_ZIP_OBJECT_NAME)

    assert preview.name == PLAIN_ZIP_OBJECT_NAME
    assert (
        preview.path
        == f"//{settings.intake_storage.bucket_name}/{PLAIN_ZIP_OBJECT_NAME}"
    )


def test_an_undecryptable_loom_archive_is_indexed_rather_than_dropped():
    """The never-drop guarantee, on its most likely trigger.

    A `.loom` carried in from another box carries the right magic and will not decrypt
    here, because `archive_enc_master_key` is per-deployment. It has to end up findable
    as an opaque blob rather than silently going nowhere -- and on the way there it must
    not fail the task into the graveyard queue either, which is what the bare
    `ValueError` from the MAC check used to do.
    """
    payload = LOOM_ARCHIVE_MAGIC_BYTES + bytes(range(256)) * 16

    _put_in_intake(ENCRYPTED_OBJECT_NAME, payload)

    preview = get_file_preview_by_name(ENCRYPTED_OBJECT_NAME)

    assert preview.name == ENCRYPTED_OBJECT_NAME
    assert (
        preview.path
        == f"//{settings.intake_storage.bucket_name}/{ENCRYPTED_OBJECT_NAME}"
    )
    # Checked after the file appeared, so the pipeline has demonstrably run: it
    # could not be opened, so no archive should have been created. The call is
    # the assertion -- it raises FetchException on the first non-empty poll and
    # otherwise returns an empty list, so wrapping it in `assert not` would be
    # dead code rather than a second check.
    fetch_archives_from_api(expected_no_of_archives=0, expected_state=None)
