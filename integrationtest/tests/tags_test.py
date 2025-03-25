import pytest
import requests
from api.models.query_model import QueryModel
from api.routers.tags import AddTagRequest, AllTags
from common.file.file_repository import TAG_LEN_MAX

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT, TAGS_ENDPOINT
from utils.fetch_from_api import fetch_files_from_api, get_file_preview_by_name
from utils.upload_asset import upload_asset, upload_many_assets


def _add_tag(file_id: str, tag: str):
    response = requests.post(
        f"{FILES_ENDPOINT}/{file_id}/tags/{tag}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _add_tags(set_tag_request: AddTagRequest):
    response = requests.post(
        f"{TAGS_ENDPOINT}/",
        json=set_tag_request.model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _delete_tag(file_id: str, tag: str):
    response = requests.delete(
        f"{FILES_ENDPOINT}/{file_id}/tags/{tag}", timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()


def _get_all_tags() -> AllTags:
    response = requests.get(f"{TAGS_ENDPOINT}/", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return AllTags(tag for tag in response.json())


def _delete_tags(tag_to_delete: str):
    response = requests.delete(
        f"{TAGS_ENDPOINT}/{tag_to_delete}",
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()


def test_indexing_does_not_add_tags():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")

    assert not file.tags


def test_add_tag():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")

    tag = "test_tag"

    _add_tag(str(file.file_id), tag)

    file = get_file_preview_by_name("basic_email.eml")
    assert file.tags == [tag]


def test_add_tag_by_query():
    tag_name = "test"
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    set_tag_request = AddTagRequest(
        tags=[tag_name], query=QueryModel(search_string="*")
    )
    _add_tags(set_tag_request)

    fetch_files_from_api(
        "*", expected_no_of_files=len(assets), wait_for_celery_idle=True
    )

    for file in assets:
        file_preview = get_file_preview_by_name(file)
        assert tag_name in file_preview.tags


def test_add_tags_by_query():
    tags = ["test", "test-1", "testö3!"]
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    set_tag_request = AddTagRequest(tags=tags, query=QueryModel(search_string="*"))
    _add_tags(set_tag_request)

    fetch_files_from_api(
        "*", expected_no_of_files=len(assets), wait_for_celery_idle=True
    )

    for file in assets:
        file_preview = get_file_preview_by_name(file)
        for tag_name in tags:
            assert tag_name in file_preview.tags


def test_delete_tag():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")
    file_id = str(file.file_id)
    keep_tag = "keep_tag"
    wrong_tag = "wrong_tag"

    _add_tag(file_id, keep_tag)
    _add_tag(file_id, wrong_tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert len(file.tags) == 2

    _delete_tag(file_id, wrong_tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert file.tags == [keep_tag]

    _delete_tag(file_id, keep_tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert not file.tags
    _add_tag(file_id, keep_tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert file.tags == [keep_tag]


def test_delete_tags():
    tag_name = "test"
    assets = ["basic_email.eml", "text.txt"]

    upload_many_assets(assets)
    fetch_files_from_api("*", expected_no_of_files=len(assets))

    set_tag_request = AddTagRequest(
        tags=[tag_name], query=QueryModel(search_string="*")
    )
    _add_tags(set_tag_request)

    fetch_files_from_api(
        "tags:test", expected_no_of_files=len(assets), wait_for_celery_idle=True
    )

    _delete_tags(tag_name)

    fetch_files_from_api(
        "*", expected_no_of_files=len(assets), wait_for_celery_idle=True
    )

    for file in assets:
        file_preview = get_file_preview_by_name(file)
        assert tag_name not in file_preview.tags


def test_add_tag_is_idempotent():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")
    file_id = str(file.file_id)

    tag = "test_tag"

    _add_tag(file_id, tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert file.tags == [tag]

    _add_tag(file_id, tag)
    file = get_file_preview_by_name("basic_email.eml")
    assert file.tags == [tag]


@pytest.mark.parametrize(
    "invalid_name",
    [
        "X" * (TAG_LEN_MAX + 1),  # too long
    ],
)
def test_set_tag_fails_with_invalid_tag_name(invalid_name: str):
    # Test with empty tag name
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")

    tag_with_invalid_name = invalid_name

    with pytest.raises(requests.HTTPError) as exc_info:
        _add_tag(str(file.file_id), tag_with_invalid_name)
    assert exc_info.value.response.status_code == 400


def test_all_tags():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")

    tag = "test_tag"

    _add_tag(str(file.file_id), tag)

    all_tags = _get_all_tags()
    assert all_tags == [tag]


def test_all_tags_with_multiple_tags():
    upload_asset("basic_email.eml")
    file = get_file_preview_by_name("basic_email.eml")

    tag1 = "test_tag1"
    tag2 = "test_tag2"

    _add_tag(str(file.file_id), tag1)
    _add_tag(str(file.file_id), tag2)

    all_tags = _get_all_tags()
    assert all_tags == [tag1, tag2]


def test_all_tags_with_multiple_files_and_multiple_tags():
    upload_asset("basic_email.eml")
    file1 = get_file_preview_by_name("basic_email.eml")

    tag1 = "test_tag1"

    _add_tag(str(file1.file_id), tag1)

    upload_asset("1.png")
    file2 = get_file_preview_by_name("1.png")
    tag2 = "test_tag2"

    _add_tag(str(file2.file_id), tag2)

    all_tags = _get_all_tags()

    assert len(all_tags) == 2
    assert tag1 in all_tags
    assert tag2 in all_tags
