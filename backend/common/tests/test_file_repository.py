from unittest.mock import MagicMock, call

import pytest
from elasticsearch.dsl import Search
from elasticsearch.dsl.response import Response
from pydantic import RootModel

from common.file.file_repository import (
    TAG_LEN_MAX,
    TAG_LEN_MIN,
    FileRepository,
    Tag,
)
from common.file.file_statistics import GroupedStatisticsEntry, StatisticsEntry
from common.services.query_builder import QueryParameters


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
