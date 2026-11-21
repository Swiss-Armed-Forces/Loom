from typing import cast
from unittest.mock import MagicMock

from common.dependencies import get_file_repository
from common.services.query_builder import SCAN_PIT_KEEPALIVE, QueryParameters

from worker.index_file.infra.scan_query import build_scan_query


def test_a_sweep_acts_on_the_snapshot_its_caller_counted():
    """The number somebody was shown and agreed to is only an answer if the files the
    sweep acts on are the files that were counted."""
    file_repository = cast(MagicMock, get_file_repository())

    query = build_scan_query(
        file_repository, QueryParameters(query_id="pit-1", search_string="content:a")
    )

    assert query.query_id == "pit-1"
    file_repository.open_point_in_time.assert_not_called()
    # A page read's keepalive does not outlive publishing one message per match.
    assert query.keep_alive == SCAN_PIT_KEEPALIVE


def test_a_sweep_without_one_opens_its_own():
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.open_point_in_time.return_value = "pit-2"

    query = build_scan_query(
        file_repository, QueryParameters(search_string="content:a")
    )

    assert query.query_id == "pit-2"
    file_repository.open_point_in_time.assert_called_once_with(
        keep_alive=SCAN_PIT_KEEPALIVE
    )
