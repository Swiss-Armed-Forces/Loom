from typing import Any
from unittest.mock import MagicMock

import pytest
from elasticsearch import Elasticsearch

from common.file.file_repository import FileRepository
from common.services.query_builder import QueryParameters


class _KnnFileRepository(FileRepository):
    """FileRepository whose kNN search is a recording mock that returns no hits.

    ``get_embedding_generator_by_knn`` builds its search from ``_document_type.search``
    rather than from the injectable search factory, so the document type is what has to
    be stood in for -- and the connection it is handed along with it, which otherwise
    resolves the global ``get_connection()``. With no hits the request it built is the
    only observable, which is what the tests below are about.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.elasticsearch_mock: Elasticsearch = MagicMock(spec=Elasticsearch)
        self.search_mock = MagicMock()
        for builder in ("query", "source", "sort", "extra", "index", "knn"):
            getattr(self.search_mock, builder).return_value = self.search_mock
        self.search_mock.execute.return_value.hits = []

    @property
    def _elasticsearch(self) -> Elasticsearch:
        return self.elasticsearch_mock

    @property
    def _document_type(self) -> Any:
        document_type = MagicMock()
        document_type.search.return_value = self.search_mock
        return document_type


# The query builder is stubbed, so what reaches Elasticsearch is the filter clause it
# returns rather than any parse of this.
SOVA_QUERY = "sova"


@pytest.fixture(name="knn_repo")
def _knn_repo() -> _KnnFileRepository:
    query_builder = MagicMock()
    query_builder.build.return_value = SOVA_QUERY
    return _KnnFileRepository(query_builder, MagicMock())


def _run_knn(repo: _KnnFileRepository, vectors: int = 2) -> None:
    list(
        repo.get_embedding_generator_by_knn(
            query=QueryParameters(query_id="q1", search_string=SOVA_QUERY),
            embedding_vectors=[[1.0]] * vectors,
            files_k=7,
            chunks_per_file=3,
        )
    )


def test_get_embedding_generator_by_knn_tracks_scores(knn_repo: _KnnFileRepository):
    """``file_score`` is the hit score, and nothing computes one under a sort that does
    not name ``_score`` -- which is every scan, leaving every hit at 0.0."""
    _run_knn(knn_repo)

    knn_repo.search_mock.extra.assert_any_call(track_scores=True)


def test_get_embedding_generator_by_knn_excludes_the_heavy_source_fields(
    knn_repo: _KnnFileRepository,
):
    """The index keeps the chunk vectors inside ``_source``, so an unfiltered hit ships
    the file's whole text and every vector of it, once per clause that reached it."""
    _run_knn(knn_repo)

    knn_repo.search_mock.source.assert_called_once_with(
        excludes=["content", "embeddings"]
    )
    for knn_call in knn_repo.search_mock.knn.call_args_list:
        assert knn_call.kwargs["inner_hits"]["_source"] == {
            "excludes": ["embeddings.vector"]
        }
