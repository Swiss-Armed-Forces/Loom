from typing import cast
from unittest.mock import MagicMock

from common.dependencies import get_file_repository
from common.services.query_builder import QueryBuilder, QueryParameters

from worker.periodic.tasks.fail_exhausted_files import fail_exhausted_files


def _sweep_query() -> QueryParameters:
    """Run the sweep over an empty result set and hand back the query it built."""
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.open_point_in_time.return_value = "pit-1"
    file_repository.get_id_generator_by_query.return_value = iter(())

    fail_exhausted_files()

    return cast(
        QueryParameters,
        file_repository.get_id_generator_by_query.call_args.kwargs["query"],
    )


def test_the_sweep_asks_a_question_elasticsearch_can_parse():
    """`reindex_count:>=N` is range syntax the sweep would only fail on at runtime,
    nightly, against a live index."""
    QueryBuilder().parse_and_transform(_sweep_query())
