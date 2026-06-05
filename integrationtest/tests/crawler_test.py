import io

import pytest
from common.dependencies import get_s3_intake_client
from common.dependencies import init as init_common_dependencies
from crawler.settings import settings

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import fetch_files_from_api, get_file_preview_by_name


@pytest.fixture(autouse=True)
def setup_crawler_dependencies():
    init_common_dependencies()


@pytest.mark.parametrize(
    "upload_name,src_filename",
    [
        ("empty_file.txt", "empty_file.txt"),
        (".hidden", "empty_file.txt"),
        ('".zip', '".zip'),
    ],
)
def test_upload_file(upload_name: str, src_filename: str):
    client = get_s3_intake_client()
    file_src = ASSETS_DIR / src_filename
    with open(file_src, "rb") as file:
        f = file.read()
        client.put_object(
            settings.intake_storage.bucket_name,
            upload_name,
            io.BytesIO(f),
            len(f),
        )
    fileprev = get_file_preview_by_name(upload_name)
    res_path = f"//{settings.intake_storage.bucket_name}/{upload_name}"
    assert fileprev
    assert fileprev.name == upload_name
    assert fileprev.path == res_path


def test_reupload_file_creates_new_entry():
    client = get_s3_intake_client()
    upload_name = "empty_file.txt"
    src = ASSETS_DIR / "empty_file.txt"
    with open(src, "rb") as f:
        data = f.read()
    client.put_object(
        settings.intake_storage.bucket_name,
        upload_name,
        io.BytesIO(data),
        len(data),
    )
    fetch_files_from_api(
        search_string=f"filename:{upload_name}", expected_no_of_files=1
    )

    src = ASSETS_DIR / "text.txt"  # important: different content
    with open(src, "rb") as f:
        data = f.read()
    client.put_object(
        settings.intake_storage.bucket_name,
        upload_name,
        io.BytesIO(data),
        len(data),
    )
    fetch_files_from_api(
        search_string=f"filename:{upload_name}", expected_no_of_files=2
    )
