from unittest.mock import MagicMock, call, patch

from elasticsearch.dsl import Search
from elasticsearch.dsl.response import Response

from common.file.file_repository import FileRepository, Stat
from common.file.file_statistics import StatisticsEntry
from common.services.query_builder import QueryParameters


def test_get_stat_generic():
    repo = FileRepository(MagicMock(), MagicMock())
    mock_search = MagicMock(spec=Search)

    test_response = Response(
        search=mock_search,
        response={
            "hits": "test",  # required for dsl inner workings
            "aggregations": {
                "total_no_of_files": {
                    "value": 40,
                },
                "all_extensions": {
                    "buckets": [
                        {
                            "key": ".txt",
                            "doc_count": 39,
                        },
                        {
                            "key": ".pdf",
                            "doc_count": 1,
                        },
                    ]
                },
            },
        },
    )

    with patch.object(repo, "_get_search_by_query", new=mock_search):
        # Make the search object return itself when sliced
        mock_search.return_value.__getitem__.return_value = mock_search.return_value
        mock_search.return_value.index().extra().execute.return_value = test_response
        query = QueryParameters(query_id="0123456789", search_string="*", languages=[])
        stats = repo.get_stat_generic(query=query, stat=Stat.EXTENSIONS)

        calls = [
            call(query=query),
            # pylint: disable=unnecessary-dunder-call
            call().__getitem__(slice(0, 0, None)),
            call().aggs.metric("total_no_of_files", "value_count", field="size"),
            call().aggs.metric(
                *["all_extensions", "terms"],
                **{"field": "extension", "size": 100},
            ),
            call().index(),
            call().index().extra(pit={"id": "0123456789", "keep_alive": "10s"}),
            call().index().extra().execute(),
        ]
        mock_search.assert_has_calls(calls)
        assert stats.stat == Stat.EXTENSIONS.value
        assert stats.total_no_of_files == 40
        assert stats.data == [
            StatisticsEntry(name=".txt", hits_count=39),
            StatisticsEntry(name=".pdf", hits_count=1),
        ]
        assert stats.key == "extension"


def test_get_stat_summary():
    repo = FileRepository(MagicMock(), MagicMock())
    mock_search = MagicMock(spec=Search)

    test_response = Response(
        search=mock_search,
        response={
            "hits": "test",  # required for dsl inner workings
            "aggregations": {
                "total_no_of_files": {"value": 40},
                "avg_file_size": {"value": 192},
                "max_file_size": {"value": 256},
                "min_file_size": {"value": 128},
            },
        },
    )

    with patch.object(repo, "_get_search_by_query", new=mock_search):
        # Make the search object return itself when sliced
        mock_search.return_value.__getitem__.return_value = mock_search.return_value
        mock_search.return_value.index().extra().execute.return_value = test_response
        query = QueryParameters(query_id="0123456789", search_string="*", languages=[])
        stats = repo.get_stat_summary(query=query)

        calls = [
            call(query=query),
            # pylint: disable=unnecessary-dunder-call
            call().__getitem__(slice(0, 0, None)),
            call().aggs.metric("avg_file_size", "avg", field="size"),
            call().aggs.metric("max_file_size", "max", field="size"),
            call().aggs.metric("min_file_size", "min", field="size"),
            call().aggs.metric("total_no_of_files", "value_count", field="size"),
            call().index(),
            call().index().extra(pit={"id": "0123456789", "keep_alive": "10s"}),
            call().index().extra().execute(),
        ]
        mock_search.assert_has_calls(calls, any_order=False)
        assert stats.total_no_of_files == 40
        assert stats.min_file_size == 128
        assert stats.max_file_size == 256
        assert stats.avg_file_size == 192
