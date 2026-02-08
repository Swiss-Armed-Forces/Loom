import random
import re
import string
from pathlib import PurePath
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from bson import ObjectId
from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_lazybytes_service,
    get_task_scheduling_service,
)
from common.file.file_repository import TAG_LEN_MAX, TAG_LEN_MIN, File, Stat
from common.file.file_statistics import (
    StatisticsEntry,
    StatisticsGeneric,
    StatisticsSummary,
)
from common.models.es_repository import EsIdObject, _EsMeta
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from fastapi.testclient import TestClient

from api.models.statistics_model import (
    GenericStatisticsModel,
    HitsPerGroupEntryModel,
    SummaryStatisticsModel,
)
from api.routers.files import (
    CONTENT_PREVIEW_LENGTH,
    SOURCE_ID,
    FileUploadResponse,
    GetFilePreviewResponse,
    GetFilesCountResponse,
    GetFilesQuery,
    UpdateFileRequest,
    UpdateFilesRequest,
)


def test_upload_file(client: TestClient):
    file_content = "this is just a testfile with a bit of content"
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=len(file_content),
    )
    file_content_mock = MagicMock(spec=LazyBytes)
    get_file_scheduling_service().index_file.return_value = file
    get_lazybytes_service().from_file.return_value = file_content_mock

    response = client.post(
        "/v1/files/", files={"file": (file.short_name, file_content)}
    )

    assert response.status_code == 200
    file_upload_response = FileUploadResponse.model_validate(response.json())
    assert file_upload_response.file_id == file.id_
    get_file_scheduling_service().index_file.assert_called_once_with(
        file.short_name, file_content_mock, SOURCE_ID
    )


def test_get_files_searches_in_repository(client: TestClient):
    file1 = EsIdObject(
        es_meta=_EsMeta(
            highlight={
                "field": ["just <em>highlighted</em>"],
            }
        ),
        sort_value="1",
        sort=[1.000048, "becfc1f5-559c-484e-be76-e080ed92f5f2"],
    )
    file2 = EsIdObject(
        es_meta=_EsMeta(
            highlight={
                "field": ["just <em>highlighted</em>"],
            }
        ),
        sort_value="2",
        sort=[1.0000475, "550451f9-131b-4562-90af-cbffd0f709d5"],
    )
    file3 = EsIdObject(
        es_meta=_EsMeta(
            highlight={
                "field": ["just <em>highlighted</em>"],
            }
        ),
        sort_value="3",
        sort=[1.000034, "08a5d481-94be-4395-afd5-d1f670926849"],
    )

    get_file_repository().get_id_generator_by_query.return_value = [file1, file2, file3]

    query = GetFilesQuery(
        query_id="0123456789",
    )

    response = client.get(
        "/v1/files/",
        params=query.model_dump(),
    )
    assert response.status_code == 200
    get_file_repository().get_id_generator_by_query.assert_called_once_with(
        query=query, sort_params=query, pagination_params=query
    )


def test_get_files_count_searches_in_repository(client: TestClient):
    get_file_repository().count_by_query.return_value = 3

    query = QueryParameters(
        query_id="0123456789",
    )

    response = client.get(
        "/v1/files/count",
        params=query.model_dump(),
    )
    assert response.status_code == 200
    assert GetFilesCountResponse.model_validate(response.json()).total_files == 3
    get_file_repository().count_by_query.assert_called_once_with(query=query)


def test_update_hidden_state_file_by_id(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )

    request = UpdateFileRequest(hidden=True)

    get_file_repository().get_by_id.return_value = file

    response = client.put(f"v1/files/{file.id_}", json=request.model_dump())

    assert response.status_code == 200
    get_file_repository().update.assert_called_once_with(file, include={"hidden"})


def test_update_hidden_state_files_by_query(client: TestClient):
    request = UpdateFilesRequest(
        query=QueryParameters(query_id="0123456789"), hidden=True
    )

    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )

    get_file_repository().get_generator_by_query.return_value = [file]

    response = client.put("v1/files/", json=request.model_dump())

    assert response.status_code == 200
    get_task_scheduling_service().dispatch_set_hidden_state.assert_called_once_with(
        query=request.query, hidden=request.hidden
    )


VALID_TAG_NAMES = [
    "tag",
    "tag123",
    'Tag with Quote"',
    "tag with spaces",
    "Tag with spaces",
    "tag-with-dash",
    "Tag-with-dash",
    "tag_with_underscore",
    "Tag_with_underscore",
    "Tag with umlaut äöü",
    "Tag with special @#$%",
    "1234567890",
    "Tag with backslash \\",
    "Tag with unicode 💩",
    "X" * (TAG_LEN_MAX),
    "X" * (TAG_LEN_MIN),
]


@pytest.mark.parametrize(
    "tag_name",
    VALID_TAG_NAMES,
)
def test_add_valid_tag(client: TestClient, tag_name: str):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )
    get_file_repository().get_by_id.return_value = file

    response = client.post(f"/v1/files/{file.id_}/tags/{tag_name}")

    assert response.status_code == 200
    get_file_repository().update.assert_called_once_with(file, include={"tags"})


INVALID_TAG_NAMES = [
    "X" * (TAG_LEN_MAX + 1),  # too long
]


@pytest.mark.parametrize(
    "tag_name",
    INVALID_TAG_NAMES,
)
def test_add_invalid_tag(client: TestClient, tag_name: str):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )
    get_file_repository().get_by_id.return_value = file

    response = client.post(f"/v1/files/{file.id_}/tags/{tag_name}")

    assert response.status_code == 422
    get_file_repository().update.assert_not_called()


def test_delete_tag(client: TestClient):
    tag = "testtag"
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        tags=[tag],
    )
    get_file_repository().get_by_id.return_value = file

    response = client.delete(f"/v1/files/{file.id_}/tags/{tag}")

    assert response.status_code == 200
    get_file_repository().update.assert_called_once_with(file, include={"tags"})


def test_delete_not_existing_tag(client: TestClient):
    tag = "testtag"
    file = File(
        full_name="/path/to/file.txt",
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )
    get_file_repository().get_by_id.return_value = file

    response = client.delete(f"/v1/files/{file.id_}/tags/{tag}")

    assert response.status_code == 404


def test_get_thumbnail(client: TestClient):
    thumbnail_content = b"just a random thumbnail"
    thumbnail_file_id = str(ObjectId())
    file = File(
        full_name="/path/to/file.txt",
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )

    get_file_repository().get_by_id.return_value = file
    get_file_storage_service().open_download_iterator.return_value = iter(
        re.split(rb"(\s+)", thumbnail_content)
    )

    response = client.get(f"/v1/files/{file.id_}/thumbnail/{thumbnail_file_id}")

    assert response.status_code == 200
    assert response.content == thumbnail_content


def test_get_full(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )
    get_file_repository().get_by_id_with_query.return_value = file
    query = QueryParameters(query_id="0123456789")

    response = client.get(f"/v1/files/{file.id_}", params=query.model_dump())

    assert response.status_code == 200
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file.id_, query=query, full_highlight_context=True
    )


def test_get_full_file_is_none(client: TestClient):
    get_file_repository().get_by_id_with_query.return_value = None
    query = QueryParameters(query_id="0123456789")
    file_id = uuid4()
    response = client.get(f"/v1/files/{file_id}", params=query.model_dump())

    assert response.status_code == 404
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file_id, query=query, full_highlight_context=True
    )


def test_get_preview(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )
    get_file_repository().get_by_id_with_query.return_value = file
    query = QueryParameters(query_id="0123456789")

    response = client.get(
        f"/v1/files/{file.id_}/preview",
        params=query.model_dump(),
    )

    assert response.status_code == 200
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file.id_, query=query, full_highlight_context=False
    )


def test_get_preview_content_truncated(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        content="".join(
            random.choices(string.ascii_letters, k=CONTENT_PREVIEW_LENGTH + 1)
        ),
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )
    get_file_repository().get_by_id_with_query.return_value = file
    query = QueryParameters(query_id="0123456789")

    response = client.get(f"/v1/files/{file.id_}/preview", params=query.model_dump())
    preview_model = GetFilePreviewResponse.model_validate(response.json())

    assert response.status_code == 200
    assert preview_model.content_preview_is_truncated is True
    assert len(preview_model.content) <= CONTENT_PREVIEW_LENGTH


def test_get_preview_file_is_none(client: TestClient):
    get_file_repository().get_by_id_with_query.return_value = None
    query = QueryParameters(query_id="0123456789")
    file_id = uuid4()
    response = client.get(f"/v1/files/{file_id}/preview", params=query.model_dump())

    assert response.status_code == 404
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file_id, query=query, full_highlight_context=False
    )


def test_stat_summary(client: TestClient):
    get_file_repository().get_stat_summary.return_value = StatisticsSummary(
        avg_file_size=16384,
        min_file_size=1024,
        max_file_size=32768,
        total_no_of_files=40,
    )
    query = QueryParameters(query_id="0123456789")

    response = client.get("/v1/files/stats/summary", params=query.model_dump())
    assert response.status_code == 200
    stats = SummaryStatisticsModel.model_validate(response.json())
    assert stats.avg == 16384
    assert stats.min == 1024
    assert stats.max == 32768
    assert stats.count == 40

    get_file_repository().get_stat_summary.assert_called_once_with(query=query)


def test_stat_generic_exists(client: TestClient):
    get_file_repository().get_stat_generic.return_value = StatisticsGeneric(
        data=[
            StatisticsEntry(
                name=".pdf",
                hits_count=39,
            ),
            StatisticsEntry(
                name=".txt",
                hits_count=1,
            ),
        ],
        total_no_of_files=40,
        stat=Stat.EXTENSIONS.value,
        key="extension",
    )
    query = QueryParameters(query_id="0123456789")

    response = client.get(
        "/v1/files/stats/generic/extensions", params=query.model_dump()
    )
    assert response.status_code == 200
    stats = GenericStatisticsModel.model_validate(response.json())
    assert stats.file_count == 40
    assert stats.stat == Stat.EXTENSIONS.value
    assert stats.data == [
        HitsPerGroupEntryModel(
            name=".pdf",
            hits_count=39,
        ),
        HitsPerGroupEntryModel(
            name=".txt",
            hits_count=1,
        ),
    ]

    get_file_repository().get_stat_generic.assert_called_once_with(
        query=query, stat=Stat.EXTENSIONS
    )


def test_stat_generic_not_exists(client: TestClient):
    response = client.get("/v1/files/stats/generic/DOESNT_EXIST?search_string=*")
    assert response.status_code == 422
