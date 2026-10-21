import io

import pytest
from common.dependencies import get_s3_intake_client
from crawler.settings import settings

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import (
    fetch_files_from_api,
    fetch_files_tree,
    get_file_preview_by_name,
)


@pytest.mark.parametrize(
    "upload_name,src_filename,expected_tree_children",
    [
        ("empty_file.txt", "empty_file.txt", []),
        (".hidden", "empty_file.txt", []),
        # The quoted archive extracts to a member whose own name is a quote.
        ('".zip', '".zip', ['"']),
    ],
)
def test_upload_file(
    upload_name: str, src_filename: str, expected_tree_children: list[str]
):
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
    # Opening a file in the folder view asks the tree for the children of its own
    # path, and that path becomes a Lucene RegExp. Only this ingestion route keeps a
    # name's metacharacters literal; the upload endpoint percent-encodes them.
    children = fetch_files_tree(search_string="*", node_path=res_path).nodes
    assert [child.full_path.name for child in children] == expected_tree_children


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
