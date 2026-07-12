import random
import re
import string
from unittest.mock import ANY, MagicMock
from uuid import uuid4

import pytest
from common.dependencies import (
    get_file_repository,
    get_file_storage_service,
    get_task_scheduling_service,
)
from common.file.file_repository import (
    TAG_LEN_MAX,
    TAG_LEN_MIN,
    File,
    FilePurePath,
    TreePathsNode,
    TreePathsResult,
)
from common.file.file_statistics import (
    AvailableStat,
    GroupedHistogramStatistics,
    GroupedStatisticsEntry,
    StatisticsEntry,
    TermsStatistics,
)
from common.models.es_repository import EsIdObject, _EsMeta
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from common.services.task_scheduling_service import UpdateFileRequest
from fastapi.testclient import TestClient

from api.models.statistics_model import (
    GroupedHistogramStatisticsModel,
    GroupedHitsPerGroupEntryModel,
    HitsPerGroupEntryModel,
    TermsStatisticsModel,
)
from api.models.tree_model import GetFilesTreeResponse
from api.routers.files import (
    CONTENT_PREVIEW_LENGTH,
    SOURCE_ID,
    AddTagsRequest,
    GetFilePreviewResponse,
    GetFilesCountResponse,
    GetFilesQuery,
    GetStatsQuery,
    UpdateFilesRequest,
)


def test_upload_file(client: TestClient):
    file_content = "this is just a testfile with a bit of content"
    file = File(
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=len(file_content),
    )
    file_content_mock = MagicMock(spec=LazyBytes)
    get_file_storage_service().from_file.return_value = file_content_mock

    response = client.post("/v1/files", files={"file": (file.short_name, file_content)})

    assert response.status_code == 202
    get_task_scheduling_service().dispatch_index_file.assert_called_once_with(
        full_name=file.short_name,
        file_content=file_content_mock,
        source_id=SOURCE_ID,
        parent_id=None,
        uploaded_datetime=ANY,
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
        "/v1/files",
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


def test_update_file_by_id(client: TestClient):
    file = File(
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
    )

    request = UpdateFileRequest(hidden=True, flagged=True, seen=True)

    response = client.put(f"v1/files/{file.id_}", json=request.model_dump())

    assert response.status_code == 202
    get_task_scheduling_service().update_by_id.assert_called_once_with(
        file.id_, request
    )


def test_update_file_by_id_not_found(client: TestClient):
    get_file_repository().get_by_id.return_value = None

    request = UpdateFileRequest(hidden=True, flagged=True, seen=True)

    response = client.put(f"v1/files/{uuid4()}", json=request.model_dump())

    assert response.status_code == 404
    get_task_scheduling_service().update_by_id.assert_not_called()


def test_update_files_by_query(client: TestClient):
    request = UpdateFilesRequest(
        query=QueryParameters(query_id="0123456789"),
        request=UpdateFileRequest(hidden=True, flagged=True, seen=True),
    )

    file = File(
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
    )

    get_file_repository().get_generator_by_query.return_value = [file]

    response = client.put("v1/files", json=request.model_dump())

    assert response.status_code == 202
    get_task_scheduling_service().dispatch_update.assert_called_once_with(
        query=request.query, request=request.request
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
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
    )
    get_file_repository().get_by_id.return_value = file

    tags_request = AddTagsRequest(tags=[tag_name])
    response = client.post(f"/v1/files/{file.id_}/tags", json=tags_request.model_dump())

    assert response.status_code == 202
    get_task_scheduling_service().dispatch_add_tags_to_file.assert_called_once_with(
        file_id=file.id_, tags=[tag_name]
    )


def test_delete_tag(client: TestClient):
    tag = "testtag"
    file = File(
        full_name="/path/to/file.txt",
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
    )
    get_file_repository().get_by_id.return_value = file

    response = client.delete(f"/v1/files/{file.id_}/tags/{tag}")

    assert response.status_code == 202
    get_task_scheduling_service().dispatch_remove_tag_from_file.assert_called_once_with(
        file_id=file.id_, tag=tag
    )


def test_get_thumbnail(client: TestClient):
    thumbnail_content = b"just a random thumbnail"
    thumbnail_data = LazyBytes(service_id=str(uuid4()))
    file = File(
        full_name="/path/to/file.txt",
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
        thumbnail_data=thumbnail_data,
    )

    get_file_repository().get_by_id.return_value = file
    get_file_storage_service().load_generator.return_value = iter(
        re.split(rb"(\s+)", thumbnail_content)
    )

    response = client.get(f"/v1/files/{file.id_}/thumbnail/{thumbnail_data.service_id}")

    assert response.status_code == 200
    assert response.content == thumbnail_content


def test_get_full(client: TestClient):
    file = File(
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
        thumbnail_data=LazyBytes(service_id=str(uuid4())),
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
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        sha256="",
        size=0,
        thumbnail_data=LazyBytes(service_id=str(uuid4())),
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
        full_name=FilePurePath("/path/to/file.txt"),
        storage_data=LazyBytes(service_id=str(uuid4())),
        source="test",
        content="".join(
            random.choices(string.ascii_letters, k=CONTENT_PREVIEW_LENGTH + 1)
        ),
        sha256="",
        size=0,
        thumbnail_data=LazyBytes(service_id=str(uuid4())),
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


def test_stat_terms_exists(client: TestClient):
    get_file_repository().get_stat_terms.return_value = TermsStatistics(
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
        stat="extension",
        key="extension",
    )
    base_query = QueryParameters(query_id="0123456789")
    expected_query = GetStatsQuery(query_id="0123456789")

    response = client.get(
        "/v1/files/stats/terms/extension", params=base_query.model_dump()
    )
    assert response.status_code == 200
    stats = TermsStatisticsModel.model_validate(response.json())
    assert stats.file_count == 40
    assert stats.stat == "extension"
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

    get_file_repository().get_stat_terms.assert_called_once_with(
        query=expected_query, stat="extension", size=5
    )


def test_stat_terms_not_exists(client: TestClient):
    response = client.get("/v1/files/stats/terms/DOESNT_EXIST?search_string=*")
    assert response.status_code == 422


def test_stat_terms_rejects_date_stat(client: TestClient):
    # date stats are not valid for the terms endpoint — must return 422
    response = client.get("/v1/files/stats/terms/uploaded_datetime?search_string=*")
    assert response.status_code == 422


def test_stat_terms_rejects_number_stat(client: TestClient):
    # number stats are not valid for the terms endpoint — must return 422
    response = client.get("/v1/files/stats/terms/size?search_string=*")
    assert response.status_code == 422


def test_stat_histogram_valid(client: TestClient):
    get_file_repository().get_stat_histogram.return_value = TermsStatistics(
        data=[
            StatisticsEntry(name="2024-01-01T00:00:00.000Z", hits_count=5),
        ],
        total_no_of_files=5,
        stat="uploaded_datetime",
        key="uploaded_datetime",
    )
    query = QueryParameters(query_id="0123456789")

    response = client.get(
        "/v1/files/stats/histogram/uploaded_datetime",
        params=query.model_dump(),
    )
    assert response.status_code == 200
    stats = TermsStatisticsModel.model_validate(response.json())
    assert stats.stat == "uploaded_datetime"
    assert stats.file_count == 5
    get_file_repository().get_stat_histogram.assert_called_once_with(
        query=query, stat="uploaded_datetime"
    )


def test_stat_histogram_not_exists(client: TestClient):
    response = client.get("/v1/files/stats/histogram/DOESNT_EXIST?search_string=*")
    assert response.status_code == 422


def test_stat_histogram_rejects_terms_stat(client: TestClient):
    # 'extension' is a terms stat, not a histogram stat — must return 422
    response = client.get("/v1/files/stats/histogram/extension?search_string=*")
    assert response.status_code == 422


def test_stat_histogram_grouped_valid(client: TestClient):
    get_file_repository().get_stat_histogram_grouped.return_value = (
        GroupedHistogramStatistics(
            stat="uploaded_datetime",
            group_by="extension",
            key="uploaded_datetime",
            histogram_type="date",
            data=[
                GroupedStatisticsEntry(
                    name="2024-01-01T00:00:00.000Z",
                    groups={".pdf": 5, ".txt": 2},
                    hits_count=7,
                )
            ],
            total_no_of_files=7,
        )
    )
    query = QueryParameters(query_id="0123456789")

    response = client.get(
        "/v1/files/stats/histogram/uploaded_datetime/grouped/extension",
        params=query.model_dump(),
    )
    assert response.status_code == 200
    stats = GroupedHistogramStatisticsModel.model_validate(response.json())
    assert stats.stat == "uploaded_datetime"
    assert stats.group_by == "extension"
    assert stats.file_count == 7
    assert stats.data == [
        GroupedHitsPerGroupEntryModel(
            name="2024-01-01T00:00:00.000Z",
            groups={".pdf": 5, ".txt": 2},
            hits_count=7,
        )
    ]
    get_file_repository().get_stat_histogram_grouped.assert_called_once_with(
        query=query, stat="uploaded_datetime", group_by="extension"
    )


def test_stat_histogram_grouped_non_date_stat(client: TestClient):
    # 'extension' is a terms stat, not date_histogram — must return 422
    response = client.get(
        "/v1/files/stats/histogram/extension/grouped/extension?search_string=*"
    )
    assert response.status_code == 422


def test_get_available_stats_by_type(client: TestClient):
    terms_response = client.get("/v1/files/stats/terms")
    assert terms_response.status_code == 200
    terms_stats = [AvailableStat.model_validate(s) for s in terms_response.json()]
    terms_ids = {s.id for s in terms_stats}
    assert "extension" in terms_ids
    assert "uploaded_datetime" not in terms_ids
    assert "size" not in terms_ids

    histogram_response = client.get("/v1/files/stats/histogram")
    assert histogram_response.status_code == 200
    histogram_stats = [
        AvailableStat.model_validate(s) for s in histogram_response.json()
    ]
    histogram_ids = {s.id for s in histogram_stats}
    assert "uploaded_datetime" in histogram_ids
    assert "size" in histogram_ids
    assert "extension" not in histogram_ids

    assert client.get("/v1/files/stats/unknown").status_code == 422


def test_get_files_tree_returns_nodes_and_cursor(client: TestClient):
    node = TreePathsNode(
        full_path=FilePurePath("//source/folder"),
        file_count=5,
        file_id=None,
    )
    get_file_repository().get_full_paths_by_query.return_value = TreePathsResult(
        nodes=[node],
        next_page_cursor="//source/folder",
    )

    response = client.get(
        "/v1/files/tree",
        params={"query_id": "abc123", "node_path": "/"},
    )

    assert response.status_code == 200
    body = GetFilesTreeResponse.model_validate(response.json())
    assert len(body.nodes) == 1
    assert body.nodes[0].full_path == FilePurePath("//source/folder")
    assert body.nodes[0].file_count == 5
    assert body.nodes[0].file_id is None
    assert body.next_page_cursor == "//source/folder"
    get_file_repository().get_full_paths_by_query.assert_called_once_with(
        query=ANY,
        tree_node_directory_path="/",
        files_only=False,
        after=None,
    )


def test_get_files_tree_passes_after_cursor(client: TestClient):
    get_file_repository().get_full_paths_by_query.return_value = TreePathsResult(
        nodes=[],
        next_page_cursor=None,
    )

    response = client.get(
        "/v1/files/tree",
        params={
            "query_id": "abc123",
            "node_path": "//source",
            "after": "//source/z.pdf",
        },
    )

    assert response.status_code == 200
    body = GetFilesTreeResponse.model_validate(response.json())
    assert body.next_page_cursor is None
    get_file_repository().get_full_paths_by_query.assert_called_once_with(
        query=ANY,
        tree_node_directory_path="//source",
        files_only=False,
        after="//source/z.pdf",
    )


def test_get_files_tree_spine_returns_nodes(client: TestClient):
    node_a = TreePathsNode(
        full_path=FilePurePath("//source/folder"),
        file_count=3,
        file_id=None,
    )
    node_b = TreePathsNode(
        full_path=FilePurePath("//source/folder/file.txt"),
        file_count=0,
        file_id="abc-123",
    )
    get_file_repository().get_spine_by_path.return_value = [node_a, node_b]

    response = client.get(
        "/v1/files/tree/spine",
        params={
            "query_id": "abc123",
            "full_path": "//source/folder/file.txt",
        },
    )

    assert response.status_code == 200
    body = GetFilesTreeResponse.model_validate(response.json())
    assert len(body.nodes) == 2
    assert body.nodes[0].full_path == FilePurePath("//source/folder")
    assert body.nodes[1].full_path == FilePurePath("//source/folder/file.txt")
    assert body.next_page_cursor is None
    get_file_repository().get_spine_by_path.assert_called_once_with(
        query=ANY,
        full_path="//source/folder/file.txt",
    )


def test_get_files_tree_spine_empty_for_no_results(client: TestClient):
    get_file_repository().get_spine_by_path.return_value = []

    response = client.get(
        "/v1/files/tree/spine",
        params={
            "query_id": "abc123",
            "full_path": "//source/nonexistent/path.txt",
        },
    )

    assert response.status_code == 200
    body = GetFilesTreeResponse.model_validate(response.json())
    assert body.nodes == []
    assert body.next_page_cursor is None
