import random
import re
import string
from pathlib import PurePath
from unittest.mock import MagicMock
from uuid import uuid4

from bson import ObjectId
from common.dependencies import (
    get_file_repository,
    get_file_scheduling_service,
    get_file_storage_service,
    get_lazybytes_service,
    get_task_scheduling_service,
)
from common.file.file_repository import File, Stat
from common.file.file_statistics import (
    StatisticsEntry,
    StatisticsGeneric,
    StatisticsSummary,
)
from common.models.es_repository import EsIdObject, _EsMeta
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from fastapi.testclient import TestClient

from api.models.query_model import QueryModel
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
    file_upload_response = FileUploadResponse(**response.json())
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
    get_file_repository().count_by_query.return_value = 3

    search_string = "this is a query"

    query = GetFilesQuery(
        search_string=search_string,
        languages=None,
        sort_by_field="_score",
        sort_direction="asc",
        page_size=10,
        sort_id=None,
    )

    response = client.get(
        "/v1/files/",
        params={"search_string": search_string, "page_size": query.page_size},
    )
    assert response.status_code == 200
    get_file_repository().get_id_generator_by_query.assert_called_once_with(
        query=query, sort_params=query, pagination_params=query
    )
    get_file_repository().count_by_query.assert_called_once_with(query=query)


def test_get_files_searches_in_repository_with_ascending_sort(client: TestClient):
    search_string = "this is a query"
    sort_by_field = "foo"
    sort_direction = "asc"
    query = GetFilesQuery(
        search_string=search_string,
        sort_by_field=sort_by_field,
        sort_direction=sort_direction,
    )

    client.get(
        "/v1/files/",
        params={
            "search_string": search_string,
            "sort_by_field": sort_by_field,
            "sort_direction": sort_direction,
        },
    )
    get_file_repository().get_id_generator_by_query.assert_called_once_with(
        query=query, sort_params=query, pagination_params=query
    )


def test_get_files_searches_in_repository_with_descending_sort(client: TestClient):
    search_string = "this is a query"
    sort_by_field = "foo"
    sort_direction = "desc"
    query = GetFilesQuery(
        search_string=search_string,
        sort_by_field=sort_by_field,
        sort_direction=sort_direction,
    )
    client.get(
        "/v1/files/",
        params={
            "search_string": search_string,
            "sort_by_field": sort_by_field,
            "sort_direction": sort_direction,
        },
    )
    get_file_repository().get_id_generator_by_query.assert_called_once_with(
        query=query, sort_params=query, pagination_params=query
    )


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
    file.hidden = True

    get_file_repository().update.assert_called_once_with(file, include={"hidden"})


def test_update_hidden_state_files_by_query(client: TestClient):
    request = UpdateFilesRequest(query=QueryModel(search_string="*"), hidden=True)

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
        request.query.to_query_parameters(), request.hidden
    )


def test_add_tag(client: TestClient):
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
    )
    tag = "testtag"
    get_file_repository().get_by_id.return_value = file

    response = client.post(f"/v1/files/{file.id_}/tags/{tag}")

    assert response.status_code == 200
    get_file_repository().update.assert_called_once_with(file, include={"tags"})


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

    response = client.get(f"/v1/files/{file.id_}/thumbnail")

    assert response.status_code == 200
    assert response.content == thumbnail_content


def test_get_full(client: TestClient):
    search_string = "file"
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )
    get_file_repository().get_by_id_with_query.return_value = file
    query = QueryParameters(search_string=search_string)

    response = client.get(
        f"/v1/files/{file.id_}",
        params={
            "search_string": search_string,
        },
    )

    assert response.status_code == 200
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file.id_, query=query, full_highlight_context=True
    )


def test_get_full_file_is_none(client: TestClient):
    get_file_repository().get_by_id_with_query.return_value = None
    query = QueryParameters(search_string="*")
    file_id = uuid4()
    response = client.get(f"/v1/files/{file_id}")

    assert response.status_code == 404
    get_file_repository().get_by_id_with_query.assert_called_once_with(
        id_=file_id, query=query, full_highlight_context=True
    )


def test_get_preview(client: TestClient):
    search_string = "file"
    file = File(
        full_name=PurePath("/path/to/file.txt"),
        storage_id=str(ObjectId()),
        source="test",
        sha256="",
        size=0,
        thumbnail_file_id=str(ObjectId()),
    )
    get_file_repository().get_by_id_with_query.return_value = file
    query = QueryParameters(search_string=search_string)

    response = client.get(
        f"/v1/files/{file.id_}/preview",
        params={
            "search_string": search_string,
        },
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

    response = client.get(f"/v1/files/{file.id_}/preview")
    preview_model = GetFilePreviewResponse(**response.json())

    assert response.status_code == 200
    assert preview_model.content_preview_is_truncated is True
    assert len(preview_model.content) <= CONTENT_PREVIEW_LENGTH


def test_get_preview_file_is_none(client: TestClient):
    get_file_repository().get_by_id_with_query.return_value = None
    query = QueryParameters(search_string="*")
    file_id = uuid4()
    response = client.get(f"/v1/files/{file_id}/preview")

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

    response = client.get("/v1/files/stats/summary?search_string=*")
    assert response.status_code == 200
    stats = SummaryStatisticsModel(**response.json())
    assert stats.avg == 16384
    assert stats.min == 1024
    assert stats.max == 32768
    assert stats.count == 40

    query = QueryParameters(search_string="*", languages=None)
    get_file_repository().get_stat_summary.assert_called_once_with(query)


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

    response = client.get("/v1/files/stats/generic/extensions?search_string=*")
    assert response.status_code == 200
    stats = GenericStatisticsModel(**response.json())
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

    query = QueryParameters(search_string="*", languages=None)
    get_file_repository().get_stat_generic.assert_called_once_with(
        query, stat=Stat.EXTENSIONS
    )


def test_stat_generic_not_exists(client: TestClient):
    response = client.get("/v1/files/stats/generic/DOESNT_EXIST?search_string=*")
    assert response.status_code == 422
