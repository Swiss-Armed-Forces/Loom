import io

import pytest
from common.dependencies import get_s3_intake_client
from crawler.settings import settings

from utils.consts import ASSETS_DIR
from utils.fetch_from_api import (
    fetch_files_from_api,
    fetch_files_tree,
    get_file_by_name,
    get_file_preview_by_name,
)
from utils.upload_asset import reindex_uploaded_asset


@pytest.mark.parametrize(
    "upload_name,src_filename,additional_recursion_depth,extracted_member,"
    "expected_tree_children",
    [
        ("empty_file.txt", "empty_file.txt", 0, None, []),
        (".hidden", "empty_file.txt", 0, None, []),
        # The quoted archive holds `"/"""/"""text"".txt`, so one level of extraction
        # puts a member whose own name is a quote under the archive's path.
        ('".zip', '".zip', 1, '"""text"".txt', ['"']),
    ],
)
def test_upload_file(
    upload_name: str,
    src_filename: str,
    additional_recursion_depth: int,
    extracted_member: str | None,
    expected_tree_children: list[str],
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

    if additional_recursion_depth > 0:
        reindex_uploaded_asset(upload_name, additional_recursion_depth)

    if extracted_member is not None:
        # Wait for the extracted member before asking the tree for the children.
        get_file_by_name(extracted_member)

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
