from pathlib import PurePath

from bson import ObjectId
from common.dependencies import get_file_repository, get_task_scheduling_service
from common.file.file_repository import File
from fastapi.testclient import TestClient

from api.models.query_model import QueryModel
from api.routers.tags import AddTagRequest

ENDPOINT = "/v1/files/tags/"


def test_add_tags(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )

    set_tag_request = AddTagRequest(tags=["test"], query=QueryModel(search_string="*"))

    get_file_repository().get_generator_by_query.return_value = [file]

    response = client.post(ENDPOINT, json=set_tag_request.model_dump())

    assert response.status_code == 200
    get_task_scheduling_service().dispatch_add_tags.assert_called_once_with(
        set_tag_request.query.to_query_parameters(), set_tag_request.tags
    )


def test_delete_tags(client: TestClient):
    tag = "test"
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )

    get_file_repository().get_generator_by_tag.return_value = [file]

    response = client.delete(f"{ENDPOINT}{tag}")

    assert response.status_code == 200
    get_task_scheduling_service().dispatch_remove_tag.assert_called_once_with(tag=tag)


def test_get_tags(client: TestClient):
    response = client.get(f"{ENDPOINT}")
    assert response.status_code == 200
    get_file_repository().get_all_tags.assert_called_once_with()
