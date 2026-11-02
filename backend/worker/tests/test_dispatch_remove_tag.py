from typing import cast
from unittest.mock import MagicMock

import pytest
from common.dependencies import get_file_repository
from common.services.query_builder import QueryBuilder, QueryParameters

from worker.index_file.dispatch_tasks import dispatch_remove_tag


def _sweep_query(tag: str) -> QueryParameters:
    """Run the sweep over an empty result set and hand back the query it built."""
    file_repository = cast(MagicMock, get_file_repository())
    file_repository.open_point_in_time.return_value = "pit-1"
    file_repository.get_generator_by_query.return_value = iter(())

    dispatch_remove_tag(tag=tag)

    return cast(
        QueryParameters,
        file_repository.get_generator_by_query.call_args.kwargs["query"],
    )


@pytest.mark.parametrize("tag", ['Tag with Quote"', "Tag with backslash \\"])
def test_remove_tag_sweeps_for_a_tag_the_model_accepts(tag: str):
    """A tag is only length-constrained, so a quote or a backslash in one is a legal tag
    that would otherwise end the phrase and leave the sweep unable to find its files."""
    query = _sweep_query(tag)

    QueryBuilder().parse_and_transform(query)
