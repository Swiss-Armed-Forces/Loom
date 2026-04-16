import pytest

from utils.fetch_from_api import build_search_string, fetch_files_from_api
from utils.upload_asset import upload_asset


@pytest.mark.parametrize(
    "file, expected_content",
    [
        # Tar archive extraction tests
        (
            "single_file.tar",
            ["single_file.tar", "single_file.tar/single_file_tar"],
        ),
        (
            "single_file.tar.gz",
            [
                "single_file.tar.gz",
                "single_file.tar.gz/0",
                "single_file.tar.gz/0/single_file_tar_gz",
            ],
        ),
        ("hidden_file.tar", ["hidden_file.tar", "hidden_file.tar/.hidden_file_tar"]),
        (
            "hidden_file.tar.gz",
            [
                "hidden_file.tar.gz",
                "hidden_file.tar.gz/0",
                "hidden_file.tar.gz/0/.hidden_file_tar_gz",
            ],
        ),
        ("empty_file.tar", ["empty_file.tar"]),
        ("empty_file.tar.gz", ["empty_file.tar.gz", "empty_file.tar.gz/0"]),
        (
            "multi_file.tar",
            [
                "multi_file.tar",
                "multi_file.tar/multi_file_1_tar",
                "multi_file.tar/multi_file_2_tar",
                "multi_file.tar/multi_file_3_tar",
            ],
        ),
        (
            "multi_file.tar.gz",
            [
                "multi_file.tar.gz",
                "multi_file.tar.gz/0",
                "multi_file.tar.gz/0/multi_file_1_tar_gz",
                "multi_file.tar.gz/0/multi_file_2_tar_gz",
                "multi_file.tar.gz/0/multi_file_3_tar_gz",
            ],
        ),
        (
            "sub_folder.tar",
            [
                "sub_folder.tar",
                "sub_folder.tar/parent_file_tar",
                "sub_folder.tar/sub_folder_tar/child_file_tar",
            ],
        ),
        (
            "sub_folder.tar.gz",
            [
                "sub_folder.tar.gz",
                "sub_folder.tar.gz/0",
                "sub_folder.tar.gz/0/parent_file_tar_gz",
                "sub_folder.tar.gz/0/sub_folder_tar_gz/child_file_tar_gz",
            ],
        ),
        (
            "sub_sub_folder.tar",
            [
                "sub_sub_folder.tar",
                "sub_sub_folder.tar/super_parent_file_tar",
                "sub_sub_folder.tar/sub_sub_folder_top_tar/middle_file_tar",
                "sub_sub_folder.tar/sub_sub_folder_top_tar/sub_sub_folder_bot_tar/child_file_tar",
            ],
        ),
        (
            "sub_sub_folder.tar.gz",
            [
                "sub_sub_folder.tar.gz",
                "sub_sub_folder.tar.gz/0",
                "sub_sub_folder.tar.gz/0/super_parent_file_tar_gz",
                "sub_sub_folder.tar.gz/0/sub_sub_folder_top_tar_gz/middle_file_tar_gz",
                (
                    "sub_sub_folder.tar.gz/"
                    "0/"
                    "sub_sub_folder_top_tar_gz/"
                    "sub_sub_folder_bot_tar_gz/"
                    "child_file_tar_gz"
                ),
            ],
        ),
        # Zip archive extraction tests
        ("archive.zip", ["archive.zip", "archive.zip/file.txt"]),
        ('".zip', ['".zip', '".zip"/"""/"""text"".txt']),
        (
            "testarchive.zip",
            [
                "testarchive.zip",
                "testarchive.zip/testfile01.txt",
                "testarchive.zip/testfile02.txt",
            ],
        ),
        (
            "testarchive_larger.zip",
            [
                "testarchive_larger.zip",
                "testarchive_larger.zip/morestuff/home.pdf",
                "testarchive_larger.zip/morestuff/onemore/pdf-annotated.tex",
                "testarchive_larger.zip/morestuff/onemore/python.png",
                "testarchive_larger.zip/testarchive/testfile01.txt",
                "testarchive_larger.zip/testarchive/testfile02.txt",
            ],
        ),
        # Pst archive extraction tests
        (
            "sample.pst",
            [
                "sample.pst",
                "sample.pst/sample/myInbox/2.eml",
                "sample.pst/sample/myInbox/2.eml/rtf-body.rtfrtf-body.rtf",
            ],
        ),
        # Pcap extraction test
        ("http.pcap", ["http.pcap"]),
        # Zstd extraction test
        ("file.txt.zst", ["file.txt.zst", "file.txt.zst/0"]),
        # XZ extraction test
        ("file.txt.xz", ["file.txt.xz", "file.txt.xz/0"]),
    ],
)
def test_extraction(file: str, expected_content: list[str]):
    upload_asset(file)

    # Test expected content
    fetch_files_from_api(
        search_string=build_search_string(
            search_string="*",
            field="full_name",
            field_value=expected_content,
        ),
        expected_no_of_files=len(expected_content),
    )
