import pytest

from utils.fetch_from_api import build_search_string, fetch_files_from_api
from utils.upload_asset import upload_asset


@pytest.mark.parametrize(
    "archive, expected_file_count, expected_archive_content",
    [
        # Tar archive extraction tests
        ("single_file.tar", 2, ["single_file_tar"]),
        ("single_file.tar.gz", 3, ["single_file_tar_gz"]),
        ("hidden_file.tar", 2, [".hidden_file_tar"]),
        ("hidden_file.tar.gz", 3, [".hidden_file_tar_gz"]),
        ("empty_file.tar", 1, []),
        ("empty_file.tar.gz", 2, []),
        (
            "multi_file.tar",
            4,
            ["multi_file_1_tar", "multi_file_2_tar", "multi_file_3_tar"],
        ),
        (
            "multi_file.tar.gz",
            5,
            ["multi_file_1_tar_gz", "multi_file_2_tar_gz", "multi_file_3_tar_gz"],
        ),
        ("sub_folder.tar", 3, ["parent_file_tar", "sub_folder_tar/child_file_tar"]),
        (
            "sub_folder.tar.gz",
            4,
            ["parent_file_tar_gz", "sub_folder_tar_gz/child_file_tar_gz"],
        ),
        (
            "sub_sub_folder.tar",
            4,
            [
                "super_parent_file_tar",
                "sub_sub_folder_top_tar/middle_file_tar",
                "sub_sub_folder_top_tar/sub_sub_folder_bot_tar/child_file_tar",
            ],
        ),
        (
            "sub_sub_folder.tar.gz",
            5,
            [
                "super_parent_file_tar_gz",
                "sub_sub_folder_top_tar_gz/middle_file_tar_gz",
                "sub_sub_folder_top_tar_gz/sub_sub_folder_bot_tar_gz/child_file_tar_gz",
            ],
        ),
        # Zip archive extraction tests
        ("archive.zip", 2, ["file.txt"]),
        ('".zip', 2, ['"/"""/"""text"".txt']),
        ("testarchive.zip", 3, ["testfile01.txt", "testfile02.txt"]),
        (
            "testarchive_larger.zip",
            6,
            [
                "morestuff/home.pdf",
                "morestuff/onemore/pdf-annotated.tex",
                "morestuff/onemore/python.png",
                "testarchive/testfile01.txt",
                "testarchive/testfile02.txt",
            ],
        ),
        # Pst archive extraction tests
        (
            "sample.pst",
            3,
            [
                "sample.pst",
                "sample.pst/sample/myInbox/2.eml",
                "sample.pst/sample/myInbox/2.eml/rtf-body.rtfrtf-body.rtf",
            ],
        ),
        # binwalk extraction test
        (
            "test_installer.msi",
            4,
            [
                "test_installer.msi",
                "test_installer.msi/0x5000/5000.cab",
                "test_installer.msi/0x5000/wireguard.exe",
                "test_installer.msi/0x5000/wg.exe",
            ],
        ),
        # Pcap extraction test
        ("http.pcap", 2, ["http.pcap", "http.pcap/pcap_decoded"]),
        # Zstd extraction test
        ("file.txt.zst", 2, ["0"]),
    ],
)
def test_archive_extraction(
    archive: str, expected_file_count: int, expected_archive_content: list[str]
):
    upload_asset(archive)
    # Test that there are only those files
    fetch_files_from_api(search_string="*", expected_no_of_files=expected_file_count)

    # Test presence archive content:
    if len(expected_archive_content) > 0:
        fetch_files_from_api(
            search_string=build_search_string(
                search_string="*",
                field="full_name",
                field_value=expected_archive_content,
            ),
            expected_no_of_files=len(expected_archive_content),
        )
