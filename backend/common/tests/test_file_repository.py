from unittest.mock import MagicMock, call, patch

import pytest
from elasticsearch.dsl import Search
from elasticsearch.dsl.response import Response
from pydantic import RootModel

from common.file.file_repository import (
    TAG_LEN_MAX,
    TAG_LEN_MIN,
    TREE_PATH_MAX_ELEMENT_COUNT,
    File,
    FilePurePath,
    FileRepository,
    Tag,
)
from common.file.file_statistics import GroupedStatisticsEntry, StatisticsEntry
from common.services.lazybytes_service import LazyBytes
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


def _make_terms_bucket(
    path: str,
    doc_count: int = 1,
    unseen_doc_count: int = 0,
    flagged_doc_count: int = 0,
) -> MagicMock:
    """Build a MagicMock for a terms aggregation bucket.

    In a terms agg the bucket key is accessed as ``bucket.key`` directly, unlike the
    composite agg where it is ``bucket.key.path``.
    """
    bucket = MagicMock()
    bucket.key = path
    bucket.doc_count = doc_count
    bucket.unseen.doc_count = unseen_doc_count
    bucket.flagged.doc_count = flagged_doc_count
    bucket.first_hit.hits.hits = []
    return bucket


def _make_terms_leaf_bucket(path: str) -> MagicMock:
    """Terms bucket that represents a leaf file (top-hit path == bucket key)."""
    bucket = _make_terms_bucket(path)
    bucket.first_hit.hits.hits = [
        {
            "_id": path.replace("/", "_"),
            "_source": {"full_path": path, "seen": True, "flagged": False},
        }
    ]
    return bucket


def _make_terms_tree_response(mock_search: MagicMock, buckets: list) -> MagicMock:
    """Wire mock_search so that get_full_paths_by_query receives the given terms
    buckets.

    Returns the search_obj so tests can inspect call counts.
    """
    directory_agg = MagicMock()
    directory_agg.buckets = buckets

    response = MagicMock()
    response.aggregations.directory = directory_agg

    search_obj = MagicMock()
    search_obj.__getitem__ = MagicMock(return_value=search_obj)
    search_obj.aggs = MagicMock()
    search_obj.filter.return_value = search_obj
    search_obj.using.return_value.execute.return_value = response
    mock_search.return_value = search_obj
    return search_obj


def test_get_full_paths_by_query_no_cursor_when_fewer_than_max_buckets():
    """next_page_cursor is None when ES returns fewer than TREE_PATH_MAX_ELEMENT_COUNT +
    1 buckets (data exhausted after first page)."""
    mock_search = MagicMock()
    buckets = [_make_terms_leaf_bucket(f"//s/f{i}.txt") for i in range(5)]
    _make_terms_tree_response(mock_search, buckets)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q1", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s"
        )

    assert result.next_page_cursor is None
    assert len(result.nodes) == 5


def test_get_full_paths_by_query_cursor_when_more_than_max_buckets():
    """next_page_cursor is the last returned node's path when ES returns
    TREE_PATH_MAX_ELEMENT_COUNT + 1 buckets (more pages exist)."""
    mock_search = MagicMock()
    buckets = [
        _make_terms_leaf_bucket(f"//s/f{i}.txt")
        for i in range(TREE_PATH_MAX_ELEMENT_COUNT + 1)
    ]
    expected_cursor = f"//s/f{TREE_PATH_MAX_ELEMENT_COUNT - 1}.txt"
    _make_terms_tree_response(mock_search, buckets)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q2", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s"
        )

    assert result.next_page_cursor == expected_cursor
    assert len(result.nodes) == TREE_PATH_MAX_ELEMENT_COUNT


def test_get_full_paths_by_query_single_es_request():
    """get_full_paths_by_query issues exactly one ES request regardless of bucket
    count."""
    mock_search = MagicMock()
    buckets = [_make_terms_leaf_bucket(f"//s/f{i}.txt") for i in range(3)]
    search_obj = _make_terms_tree_response(mock_search, buckets)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q3", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        repo.get_full_paths_by_query(query=query, tree_node_directory_path="//s")

    assert search_obj.using.return_value.execute.call_count == 1


def test_get_full_paths_by_query_cursor_bucket_excluded_on_next_page():
    """When after=cursor is supplied, the cursor bucket is excluded even if ES returns
    it again (its deeper-path tokens satisfy the range filter)."""
    mock_search = MagicMock()
    cursor = "//s/f0.txt"
    buckets = [
        _make_terms_leaf_bucket(cursor),  # reappearing cursor — must be dropped
        _make_terms_leaf_bucket("//s/f1.txt"),
        _make_terms_leaf_bucket("//s/f2.txt"),
    ]
    _make_terms_tree_response(mock_search, buckets)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q4", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s", after=cursor
        )

    paths = [str(n.full_path) for n in result.nodes]
    assert cursor not in paths
    assert len(result.nodes) == 2


def test_get_full_paths_by_query_cursor_still_detected_after_cursor_exclusion():
    """Regression: when ES re-admits the cursor bucket (multi-value range filter),
    excluding it must not consume the extra slot used to detect a next page.

    With `after` set, `size` must be TREE_PATH_MAX_ELEMENT_COUNT + 2 so that after the
    cursor bucket is dropped, N+1 real buckets remain and next_page_cursor is set.
    """
    mock_search = MagicMock()
    cursor = "//s/f0.txt"
    # ES returns: cursor bucket + TREE_PATH_MAX_ELEMENT_COUNT real buckets + 1 extra.
    # The extra bucket signals there is a further page.
    buckets = [_make_terms_leaf_bucket(cursor)] + [
        _make_terms_leaf_bucket(f"//s/f{i}.txt")
        for i in range(1, TREE_PATH_MAX_ELEMENT_COUNT + 2)
    ]
    _make_terms_tree_response(mock_search, buckets)

    repo = FileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q5", search_string="*")
    with patch("common.models.es_repository.get_connection", return_value=MagicMock()):
        result = repo.get_full_paths_by_query(
            query=query, tree_node_directory_path="//s", after=cursor
        )

    assert len(result.nodes) == TREE_PATH_MAX_ELEMENT_COUNT
    assert result.next_page_cursor is not None
    assert cursor not in [str(n.full_path) for n in result.nodes]


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


def _make_file(full_name: str) -> File:
    return File(
        storage_data=LazyBytes(service_id="000000000000000000000000"),
        full_name=FilePurePath(full_name),
        source="api-upload",
        parent_id=None,
        sha256="abc123",
        size=0,
    )


@pytest.mark.parametrize(
    "full_name, expected_full_path",
    [
        # Relative path: source prefix prepended
        ("dir/file.txt", "//api-upload/dir/file.txt"),
        # Leading single slash: must not drop the source prefix
        ("/file.txt", "//api-upload/file.txt"),
        ("/subdir/file.txt", "//api-upload/subdir/file.txt"),
        # Already a full path (double-slash prefix): used as-is
        ("//api-upload/dir/file.txt", "//api-upload/dir/file.txt"),
    ],
)
def test_file_full_path(full_name: str, expected_full_path: str):
    """Regression: full_path must always start with //source/, even when full_name is an
    absolute path with a leading slash."""
    file = _make_file(full_name)
    assert str(file.full_path) == expected_full_path
