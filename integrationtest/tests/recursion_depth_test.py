import json

from utils.fetch_from_api import get_file_by_name
from utils.upload_asset import upload_asset


def test_recursion_depth_field():
    """Verify recursion_depth is stored correctly for root files and their attachments.

    archive.zip contains file.txt at one level of nesting, so:
    - archive.zip should have recursion_depth=0
    - file.txt (extracted from the archive) should have recursion_depth=1
    """
    upload_asset("archive.zip")

    parent = get_file_by_name("archive.zip")
    child = get_file_by_name("file.txt")

    assert json.loads(parent.raw).get("recursion_depth", 0) == 0
    assert json.loads(child.raw).get("recursion_depth", 0) == 1
