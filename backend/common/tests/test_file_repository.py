from unittest.mock import MagicMock, call, patch

import pytest
from elasticsearch.dsl import Search
from elasticsearch.dsl.response import Response
from pydantic import RootModel

from common.file.file_repository import (
    TAG_LEN_MAX,
    TAG_LEN_MIN,
    TREE_PATH_COMPOSITE_PAGE_SIZE,
    TREE_PATH_MAX_ELEMENT_COUNT,
    FilePurePath,
    FileRepository,
    Tag,
)
from common.file.file_statistics import GroupedStatisticsEntry, StatisticsEntry
from common.services.query_builder import QueryParameters


def _make_bucket(
    path: str,
    doc_count: int = 1,
    unseen_doc_count: int = 0,
    flagged_doc_count: int = 0,
) -> MagicMock:
    """Build a MagicMock for a composite aggregation bucket with no top hit."""
    bucket = MagicMock()
    bucket.key.path = path
    bucket.doc_count = doc_count
    bucket.unseen.doc_count = unseen_doc_count
    bucket.flagged.doc_count = flagged_doc_count
    bucket.first_hit.hits.hits = []
    return bucket


def _set_bucket_hit(
    bucket: MagicMock,
    full_path: str,
    file_id: str,
    seen: bool | None = True,
    flagged: bool | None = False,
) -> MagicMock:
    """Attach a top-hit entry to a bucket (marking it as a leaf file)."""
    source: dict = {"full_path": full_path}
    if seen is not None:
        source["seen"] = seen
    if flagged is not None:
        source["flagged"] = flagged
    bucket.first_hit.hits.hits = [{"_id": file_id, "_source": source}]
    return bucket


def test_parse_tree_bucket_directory():
    """A bucket whose top hit path differs from the bucket key is a directory."""
    bucket = _make_bucket("//source/docs", doc_count=3, unseen_doc_count=1)
    _set_bucket_hit(bucket, "//source/docs/file.txt", "abc")
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.full_path == FilePurePath("//source/docs")
    assert node.file_id is None
    assert node.is_unseen is False
    assert node.is_flagged is False
    assert node.unseen_count == 1
    assert node.flagged_count == 0
    assert node.file_count == 3


def test_parse_tree_bucket_leaf():
    """A bucket whose top hit path equals the bucket key is a leaf file."""
    bucket = _make_bucket("//source/file.txt")
    _set_bucket_hit(bucket, "//source/file.txt", "xyz", seen=True, flagged=False)
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.file_id == "xyz"
    assert node.is_unseen is False
    assert node.is_flagged is False
    assert node.unseen_count == 0
    # file_count must not count the leaf node itself
    assert node.file_count == 0


def test_parse_tree_bucket_unseen_leaf():
    """An unseen leaf contributes 1 to unseen_count which must be subtracted."""
    bucket = _make_bucket("//source/new.pdf", unseen_doc_count=1)
    _set_bucket_hit(bucket, "//source/new.pdf", "u1", seen=False, flagged=False)
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.is_unseen is True
    assert node.file_id == "u1"
    # unseen_count must not double-count the node itself
    assert node.unseen_count == 0


def test_parse_tree_bucket_flagged_leaf():
    """A flagged leaf contributes 1 to flagged_count which must be subtracted."""
    bucket = _make_bucket("//source/flagged.pdf", flagged_doc_count=1)
    _set_bucket_hit(bucket, "//source/flagged.pdf", "f1", seen=True, flagged=True)
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.is_flagged is True
    # flagged_count must not double-count the node itself
    assert node.flagged_count == 0


def test_parse_tree_bucket_missing_seen_field():
    """A bucket missing the 'seen' field in _source defaults is_unseen to False."""
    bucket = _make_bucket("//source/noseen.pdf")
    _set_bucket_hit(bucket, "//source/noseen.pdf", "ns1", seen=None, flagged=False)
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.is_unseen is False
    assert node.file_id == "ns1"


def test_parse_tree_bucket_missing_flagged_field():
    """A bucket missing the 'flagged' field in _source defaults is_flagged to False."""
    bucket = _make_bucket("//source/noflag.pdf")
    _set_bucket_hit(bucket, "//source/noflag.pdf", "nf1", seen=True, flagged=None)
    node = FileRepository._parse_tree_bucket(bucket)  # pylint: disable=protected-access
    assert node.is_flagged is False
    assert node.file_id == "nf1"


def _make_tree_response(
    mock_search: MagicMock,
    buckets: list,
    after_key_path: str | None = None,
) -> None:
    """Wire mock_search so that get_full_paths_by_query receives the given buckets."""
    directory_agg = MagicMock()
    directory_agg.buckets = buckets
    if after_key_path is not None:
        directory_agg.after_key = {"path": after_key_path}

    response = MagicMock()
    response.aggregations.directory = directory_agg

    # search_factory receives (query, full_highlight_context) and must return a
    # Search-like object whose full chain ends in .using(...).execute()
    search_obj = MagicMock()
    search_obj.__getitem__ = MagicMock(return_value=search_obj)
    search_obj.aggs = MagicMock()
    # .filter() is called for non-root node paths; return self so the chain works.
    search_obj.filter.return_value = search_obj
    search_obj.using.return_value.execute.return_value = response
    mock_search.return_value = search_obj


def _make_leaf_bucket(path: str) -> MagicMock:
    return _set_bucket_hit(_make_bucket(path), path, path.replace("/", "_"))


def test_get_full_paths_by_query_no_cursor_when_fewer_than_max_buckets():
    """next_page_cursor is None when raw_buckets < TREE_PATH_COMPOSITE_PAGE_SIZE (data
    exhausted)."""
    mock_search = MagicMock()
    buckets = [_make_leaf_bucket(f"//s/f{i}.txt") for i in range(5)]
    _make_tree_response(mock_search, buckets, after_key_path="//s/f4.txt")

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q1", search_string="*")
    # get_connection is a global DSL registry call with no injection point.
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s"
        )

    assert result.next_page_cursor is None


def test_get_full_paths_by_query_cursor_when_exactly_max_buckets():
    """next_page_cursor is set when we collect exactly TREE_PATH_MAX_ELEMENT_COUNT
    nodes."""
    mock_search = MagicMock()
    buckets = [
        _make_leaf_bucket(f"//s/f{i}.txt") for i in range(TREE_PATH_MAX_ELEMENT_COUNT)
    ]
    after_key = f"//s/f{TREE_PATH_MAX_ELEMENT_COUNT - 1}.txt"
    _make_tree_response(mock_search, buckets, after_key_path=after_key)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q2", search_string="*")
    # get_connection is a global DSL registry call with no injection point.
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s"
        )

    assert result.next_page_cursor == after_key


def test_get_full_paths_by_query_loops_past_all_filtered_page():
    """The loop advances past a full page where every bucket is filtered out.

    When the first ES page is full (TREE_PATH_COMPOSITE_PAGE_SIZE buckets) but all are
    excluded by the depth filter, the loop must issue a second request.  When that
    second page is empty (data exhausted) the result has no nodes and no cursor.
    """
    # All buckets are deeper than //s (depth 2), so the Python-side depth filter
    # for tree_node_directory_path="//s" will exclude all of them.
    filtered_buckets = [
        _make_leaf_bucket(f"//s/sub/f{i}.txt")
        for i in range(TREE_PATH_COMPOSITE_PAGE_SIZE)
    ]
    after_key_path = f"//s/sub/f{TREE_PATH_COMPOSITE_PAGE_SIZE - 1}.txt"

    search_obj = MagicMock()
    search_obj.__getitem__ = MagicMock(return_value=search_obj)
    search_obj.aggs = MagicMock()
    search_obj.filter.return_value = search_obj

    # First response: full page of filtered buckets with an after_key.
    resp1_dir = MagicMock()
    resp1_dir.buckets = filtered_buckets
    resp1_dir.after_key = {"path": after_key_path}
    resp1 = MagicMock()
    resp1.aggregations.directory = resp1_dir

    # Second response: empty page — signals data exhausted.
    resp2_dir = MagicMock()
    resp2_dir.buckets = []
    resp2_dir.after_key = None
    resp2 = MagicMock()
    resp2.aggregations.directory = resp2_dir

    search_obj.using.return_value.execute.side_effect = [resp1, resp2]

    mock_search = MagicMock()
    mock_search.return_value = search_obj

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q3", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s"
        )

    assert result.nodes == []
    assert result.next_page_cursor is None
    assert search_obj.using.return_value.execute.call_count == 2


def test_get_stat_terms():
    mock_search = MagicMock(spec=Search)

    test_response = Response(
        search=mock_search,
        response={
            "hits": {"total": {"value": 40, "relation": "eq"}, "hits": []},
            "aggregations": {
                "all_extension": {
                    "buckets": [
                        {"key": ".txt", "doc_count": 39},
                        {"key": ".pdf", "doc_count": 1},
                    ]
                },
            },
        },
    )

    # Make the search object return itself when sliced and after .extra()
    mock_search.return_value.__getitem__.return_value = mock_search.return_value
    mock_search.return_value.extra.return_value = mock_search.return_value
    mock_search.return_value.index().extra().execute.return_value = test_response
    query = QueryParameters(query_id="0123456789", search_string="*")
    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    stats = repo.get_stat_terms(query=query, stat="extension")

    calls = [
        call(query, False),
        # pylint: disable=unnecessary-dunder-call
        call().__getitem__(slice(0, 0, None)),
        call().extra(track_total_hits=True),
        call().aggs.metric(
            "all_extension", "terms", field="extension", size=5, missing="(none)"
        ),
        call().index(),
        call().index().extra(pit={"id": "0123456789", "keep_alive": "10s"}),
        call().index().extra().execute(),
    ]
    mock_search.assert_has_calls(calls)
    assert stats.stat == "extension"
    assert stats.total_no_of_files == 40
    assert stats.data == [
        StatisticsEntry(name=".txt", hits_count=39),
        StatisticsEntry(name=".pdf", hits_count=1),
    ]
    assert stats.key == "extension"


def test_get_stat_date_histogram_grouped():
    mock_search = MagicMock(spec=Search)

    test_response = Response(
        search=mock_search,
        response={
            "hits": "test",  # required for dsl inner workings
            "aggregations": {
                "total_no_of_files": {"value": 7},
                "min_val": {"value": 1704067200000},
                "max_val": {"value": 1704067200000},
                "grouped_uploaded_datetime": {
                    "buckets": [
                        {
                            "key_as_string": "2024-01-01T00:00:00.000Z",
                            "key": 1704067200000,
                            "doc_count": 7,
                            "by_extension": {
                                "buckets": [
                                    {"key": ".pdf", "doc_count": 5},
                                    {"key": ".txt", "doc_count": 2},
                                ]
                            },
                        }
                    ]
                },
            },
        },
    )

    mock_search.return_value.__getitem__.return_value = mock_search.return_value
    mock_search.return_value.index().extra().execute.return_value = test_response
    query = QueryParameters(query_id="0123456789", search_string="*")
    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    stats = repo.get_stat_histogram_grouped(
        query=query, stat="uploaded_datetime", group_by="extension"
    )

    assert stats.stat == "uploaded_datetime"
    assert stats.group_by == "extension"
    assert stats.total_no_of_files == 7
    assert stats.min_value == 1704067200000.0
    assert stats.max_value == 1704067200000.0
    assert len(stats.data) == 1
    assert stats.data[0] == GroupedStatisticsEntry(
        name="2024-01-01T00:00:00.000Z",
        groups={".pdf": 5, ".txt": 2},
        hits_count=7,
    )


TestTagType = RootModel[Tag]

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
def test_valid_tag_names(tag_name: str):
    tag = TestTagType(tag_name)
    assert tag.root == tag_name


INVALID_TAG_NAMES = [
    123,  # not a string
    {},  # not a string
    "",  # empty
    "X" * (TAG_LEN_MAX + 1),  # too long
    "X" * (TAG_LEN_MIN - 1),  # too short
]


@pytest.mark.parametrize(
    "tag_name",
    INVALID_TAG_NAMES,
)
def test_invalid_tag_names(tag_name: str):
    # Test with empty tag name
    with pytest.raises(ValueError):
        TestTagType(tag_name)
