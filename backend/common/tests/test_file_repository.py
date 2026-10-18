from types import SimpleNamespace
from typing import Any, Callable, NamedTuple
from unittest.mock import MagicMock, call

import pytest
from elasticsearch import Elasticsearch
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
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import DEFAULT_PIT_KEEPALIVE, QueryParameters


class _TestFileRepository(FileRepository):
    """FileRepository with the Elasticsearch connection injected.

    ``_elasticsearch`` is a plain property resolving the global get_connection(), and
    overriding it is all it takes to hand the repository a test double instead of
    patching the connection into place.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.elasticsearch_mock: Elasticsearch = MagicMock(spec=Elasticsearch)

    @property
    def _elasticsearch(self) -> Elasticsearch:
        return self.elasticsearch_mock


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

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q1", search_string="*")
    result = repo.get_full_paths_by_query(query=query, tree_node_directory_path="//s")

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

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q2", search_string="*")
    result = repo.get_full_paths_by_query(query=query, tree_node_directory_path="//s")

    assert result.next_page_cursor == expected_cursor
    assert len(result.nodes) == TREE_PATH_MAX_ELEMENT_COUNT


def test_get_full_paths_by_query_single_es_request():
    """get_full_paths_by_query issues exactly one ES request regardless of bucket
    count."""
    mock_search = MagicMock()
    buckets = [_make_terms_leaf_bucket(f"//s/f{i}.txt") for i in range(3)]
    search_obj = _make_terms_tree_response(mock_search, buckets)

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q3", search_string="*")
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

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q4", search_string="*")
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

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q5", search_string="*")
    result = repo.get_full_paths_by_query(
        query=query, tree_node_directory_path="//s", after=cursor
    )

    assert len(result.nodes) == TREE_PATH_MAX_ELEMENT_COUNT
    assert result.next_page_cursor is not None
    assert cursor not in [str(n.full_path) for n in result.nodes]


def test_get_full_paths_by_query_stops_when_no_bucket_advances_the_cursor():
    """A page that hands out nothing must not hand out a cursor either.

    Every bucket ES returned sorts at or before the cursor, so the highest of them would
    reproduce the very same window — the caller would page over empty results for good,
    one Celery round-trip and one model turn each time.
    """
    mock_search = MagicMock()
    cursor = "//s/zzz.txt"
    # A full window, every key below the cursor: the range filter on the multi-value
    # full_path.tree re-admits buckets whose documents have a deeper token past it.
    buckets = [
        _make_terms_leaf_bucket(f"//s/f{i}.txt")
        for i in range(TREE_PATH_MAX_ELEMENT_COUNT + 2)
    ]
    _make_terms_tree_response(mock_search, buckets)

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q6", search_string="*")
    result = repo.get_full_paths_by_query(
        query=query, tree_node_directory_path="//s", after=cursor
    )

    assert result.nodes == []
    assert result.next_page_cursor is None


def test_get_full_paths_by_query_drops_buckets_before_the_cursor():
    """The range filter on the multi-value full_path.tree admits a document when any of
    its tokens is past the cursor, and the bucket that document contributes to can sort
    before it: a file "//s/report.txt" and a folder "//s/report" are page neighbours
    ("." < "/"), so a document below the folder re-creates the folder's bucket after it
    was already handed out.
    """
    mock_search = MagicMock()
    cursor = "//s/report.txt"
    buckets = [
        # Re-admitted by //s/report/inner.pdf, but emitted on the previous page.
        _make_terms_bucket("//s/report"),
        _make_terms_leaf_bucket("//s/zeta.txt"),
    ]
    _make_terms_tree_response(mock_search, buckets)

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q6", search_string="*")
    result = repo.get_full_paths_by_query(
        query=query, tree_node_directory_path="//s", after=cursor
    )

    assert [str(n.full_path) for n in result.nodes] == ["//s/zeta.txt"]


def test_get_full_paths_by_query_page_size_bounds_the_page():
    """The AI browse tools page smaller than the folder view, so the page size cannot be
    the module constant."""
    mock_search = MagicMock()
    buckets = [_make_terms_leaf_bucket(f"//s/f{i}.txt") for i in range(4)]
    _make_terms_tree_response(mock_search, buckets)

    repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
    query = QueryParameters(query_id="q7", search_string="*")
    result = repo.get_full_paths_by_query(
        query=query, tree_node_directory_path="//s", page_size=2
    )

    assert len(result.nodes) == 2
    assert result.next_page_cursor == "//s/f1.txt"


class _FlatFilesFixture(NamedTuple):
    repo: FileRepository
    search: MagicMock
    factory: MagicMock


_FLAT_FILES_FILENAME = "f"
_FLAT_FILES_DIGEST = SearchAfterCursor.digest("*", _FLAT_FILES_FILENAME)


def _make_query() -> QueryParameters:
    return QueryParameters(query_id="q1", search_string="*")


def _make_flat_hit(
    path: str,
    score: float = 1.0,
    seen: bool | None = True,
    flagged: bool | None = False,
) -> MagicMock:
    """Build a MagicMock for a single leaf-file search hit.

    ``None`` removes the flag from the hit entirely, the way ES omits a field that was
    never indexed — on a plain MagicMock every attribute exists, so without this the
    getattr defaults in _build_flat_file_node are unreachable.
    """
    hit = MagicMock()
    hit.full_path = path
    hit.seen = seen
    hit.flagged = flagged
    if seen is None:
        del hit.seen
    if flagged is None:
        del hit.flagged
    hit.meta.id = path.replace("/", "_")
    hit.meta.sort = [score, path]
    return hit


def _make_flat_files_response(mock_search: MagicMock, hits: list) -> MagicMock:
    """Wire mock_search so that get_flat_files_by_query receives the given hits."""
    response_hits = MagicMock()
    response_hits.__iter__.return_value = iter(hits)
    response_hits.total = SimpleNamespace(
        value=len(hits),
        relation="eq" if len(hits) <= 10_000 else "gte",
    )

    search_obj = MagicMock()
    # Every builder call hands back the same object, so a test can assert on the
    # calls without walking the chain.
    for builder in ("query", "source", "sort", "extra", "index", "using"):
        getattr(search_obj, builder).return_value = search_obj
    search_obj.execute.return_value.hits = response_hits
    mock_search.return_value = search_obj
    return search_obj


@pytest.fixture(name="flat_files_repo")
def _flat_files_repo() -> Callable[[list], _FlatFilesFixture]:
    """Build a FileRepository wired to a mock search returning the given hits."""
    mock_search = MagicMock()

    def build(hits: list) -> _FlatFilesFixture:
        search_obj = _make_flat_files_response(mock_search, hits)
        repo = _TestFileRepository(MagicMock(), MagicMock(), search_factory=mock_search)
        return _FlatFilesFixture(repo=repo, search=search_obj, factory=mock_search)

    return build


def test_get_flat_files_by_query_no_cursor_when_result_set_is_exhausted(
    flat_files_repo,
):
    hits = [_make_flat_hit(f"//s/f{i}.txt") for i in range(5)]
    fixture = flat_files_repo(hits)

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    assert result.next_cursor is None
    assert len(result.nodes) == 5
    assert result.nodes[0].file_id == "__s_f0.txt"
    assert result.nodes[0].full_path == FilePurePath("//s/f0.txt")


def test_get_flat_files_by_query_reports_the_seen_and_flagged_state(flat_files_repo):
    hits = [
        _make_flat_hit("//s/unread.txt", seen=False, flagged=True),
        # ES omits fields that were never indexed; those default to seen and
        # unflagged rather than raising.
        _make_flat_hit("//s/missing.txt", seen=None, flagged=None),
    ]
    fixture = flat_files_repo(hits)

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    unread, missing = result.nodes
    assert (unread.is_unseen, unread.is_flagged) == (True, True)
    assert (missing.is_unseen, missing.is_flagged) == (False, False)


def test_get_flat_files_by_query_cursor_continues_the_relevance_ordering(
    flat_files_repo,
):
    """The cursor is the sort tuple of the last returned hit, so the next page resumes
    the score ordering instead of jumping to a lexicographic position.

    Relevance leads the sort, so this is the ordering the next page has to continue.
    """
    # Descending score, deliberately not in path order.
    hits = [
        _make_flat_hit(f"//s/f{i}.txt", score=100.0 - i)
        for i in range(TREE_PATH_MAX_ELEMENT_COUNT + 1)
    ]
    fixture = flat_files_repo(hits)

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    assert len(result.nodes) == TREE_PATH_MAX_ELEMENT_COUNT
    assert result.next_cursor is not None
    last = hits[TREE_PATH_MAX_ELEMENT_COUNT - 1]
    result.next_cursor.validate_for(
        expected_src="flat_files",
        expected_digest=_FLAT_FILES_DIGEST,
    )
    assert result.next_cursor.last_sort == last.meta.sort


def test_get_flat_files_by_query_sorts_by_relevance_then_path(flat_files_repo):
    """The should-clause boosting short_name is only worth its scoring cost while _score
    leads the sort; the path behind it makes the order total so search_after can resume
    it."""
    fixture = flat_files_repo([])

    fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    fixture.search.sort.assert_called_once_with(
        {"_score": {"order": "desc"}},
        {"full_path.keyword": {"order": "asc"}},
    )


def test_get_flat_files_by_query_returns_one_node_per_path(flat_files_repo):
    """Re-indexing a file under the same path leaves two live documents, and sorting on
    relevance rules out collapse — so the duplicate is dropped here."""
    fixture = flat_files_repo(
        [
            _make_flat_hit("//s/report.pdf", score=9.0),
            _make_flat_hit("//s/report.pdf", score=9.0),
            _make_flat_hit("//s/other.pdf", score=8.0),
        ]
    )

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    assert [str(n.full_path) for n in result.nodes] == [
        "//s/report.pdf",
        "//s/other.pdf",
    ]


def test_get_flat_files_by_query_drops_a_duplicate_of_the_cursor_path(flat_files_repo):
    """A duplicate pair split across a page boundary is the one case the per-page check
    cannot see, so the path the cursor carries is dropped with it."""
    fixture = flat_files_repo(
        [
            _make_flat_hit("//s/report.pdf", score=9.0),
            _make_flat_hit("//s/next.pdf", score=8.0),
        ]
    )

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(),
        filename=_FLAT_FILES_FILENAME,
        after=SearchAfterCursor(
            src="flat_files",
            last_sort=[9.0, "//s/report.pdf"],
            query_digest=_FLAT_FILES_DIGEST,
        ),
    )

    assert [str(n.full_path) for n in result.nodes] == ["//s/next.pdf"]


def test_get_flat_files_by_query_does_not_request_highlighting(flat_files_repo):
    """Highlighting every field is expensive and this search renders no snippets."""
    fixture = flat_files_repo([])

    fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME
    )

    fixture.factory.assert_called_once_with(_make_query(), False, False)


def test_get_flat_files_by_query_resumes_from_the_cursor(flat_files_repo):
    fixture = flat_files_repo([])
    sort = [12.5, "//s/f3.txt", "unique-3"]

    fixture.repo.get_flat_files_by_query(
        query=_make_query(),
        filename=_FLAT_FILES_FILENAME,
        after=SearchAfterCursor(
            src="flat_files", last_sort=sort, query_digest=_FLAT_FILES_DIGEST
        ),
    )

    fixture.search.extra.assert_any_call(search_after=sort)


@pytest.mark.parametrize(
    "cursor",
    [
        pytest.param(
            SearchAfterCursor(
                src="execute_query",
                last_sort=[1.0, "x"],
                query_digest=_FLAT_FILES_DIGEST,
            ),
            id="another-tools-cursor",
        ),
        pytest.param(
            SearchAfterCursor(
                src="flat_files",
                last_sort=[1.0, "x", "u"],
                query_digest="not-this-query",
            ),
            id="cursor-from-a-different-query",
        ),
    ],
)
def test_get_flat_files_by_query_rejects_a_foreign_cursor(
    flat_files_repo, cursor: SearchAfterCursor
):
    fixture = flat_files_repo([])

    with pytest.raises(InvalidPaginationCursorError):
        fixture.repo.get_flat_files_by_query(
            query=_make_query(),
            filename=_FLAT_FILES_FILENAME,
            after=cursor,
        )


def test_get_flat_files_by_query_pages_the_query_point_in_time(flat_files_repo):
    """_score is the primary sort key, and it drifts as documents are indexed and
    merged, so search_after only resumes where it stopped within one snapshot."""
    hits = [_make_flat_hit(f"//s/f{i}.txt") for i in range(3)]
    fixture = flat_files_repo(hits)
    query = _make_query()
    result = fixture.repo.get_flat_files_by_query(
        query=query, filename=_FLAT_FILES_FILENAME, page_size=2
    )

    fixture.search.extra.assert_any_call(
        pit={"id": query.query_id, "keep_alive": DEFAULT_PIT_KEEPALIVE}
    )
    assert result.next_cursor is not None
    result.next_cursor.validate_for(
        expected_src="flat_files",
        expected_digest=_FLAT_FILES_DIGEST,
    )
    assert result.next_cursor.pit == query.query_id


def test_get_flat_files_by_query_resumes_the_cursor_point_in_time(flat_files_repo):
    """A page has to read the snapshot the previous page read, so the cursor's point-in-
    time wins over whatever the query carries."""
    fixture = flat_files_repo([])

    fixture.repo.get_flat_files_by_query(
        query=_make_query(),
        filename=_FLAT_FILES_FILENAME,
        after=SearchAfterCursor(
            src="flat_files",
            last_sort=[1.0, "//s/f1.txt", "unique-1"],
            pit="pit-of-page-one",
            query_digest=_FLAT_FILES_DIGEST,
        ),
    )

    fixture.search.extra.assert_any_call(
        pit={"id": "pit-of-page-one", "keep_alive": DEFAULT_PIT_KEEPALIVE}
    )


def test_get_flat_files_by_query_page_size_bounds_the_page(flat_files_repo):
    hits = [_make_flat_hit(f"//s/f{i}.txt") for i in range(4)]
    fixture = flat_files_repo(hits)

    result = fixture.repo.get_flat_files_by_query(
        query=_make_query(), filename=_FLAT_FILES_FILENAME, page_size=3
    )

    # +1 over-fetch: the extra hit is what answers "is there a next page?".
    fixture.search.extra.assert_any_call(size=4)
    assert len(result.nodes) == 3
    assert result.next_cursor is not None


def test_get_stat_terms():
    # Not spec'd to Search: this stands in for the search *factory*, whose
    # signature is (query, full_highlight_context, with_highlight).
    mock_search = MagicMock()

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
        call(query, False, True),
        # pylint: disable=unnecessary-dunder-call
        call().__getitem__(slice(0, 0, None)),
        call().extra(track_total_hits=True),
        call().aggs.metric(
            "all_extension", "terms", field="extension", size=5, missing="(none)"
        ),
        call().index(),
        call()
        .index()
        .extra(pit={"id": "0123456789", "keep_alive": DEFAULT_PIT_KEEPALIVE}),
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
