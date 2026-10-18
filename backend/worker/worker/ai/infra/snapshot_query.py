from typing import NamedTuple

from common.file.file_repository import FileRepository
from common.models.cursor_pagination import SearchAfterCursor
from common.services.query_builder import AI_PIT_KEEPALIVE, QueryParameters


class SnapshotBoundQuery(NamedTuple):
    """A query bound to the one index snapshot a paging run reads.

    Attributes:
        query: Carries the point-in-time every page of the run is read against.
        resumed_from_cursor_pit: Whether that point-in-time came from the cursor
            rather than being opened here.  Elasticsearch answers a corrupted
            point-in-time with the same error as a malformed query, so this is what
            lets a caller tell a bad cursor apart from a bad query string.
    """

    query: QueryParameters
    resumed_from_cursor_pit: bool


def build_snapshot_bound_query(
    file_repository: FileRepository,
    search_string: str,
    after_cursor: SearchAfterCursor | None,
) -> SnapshotBoundQuery:
    """Bind a paging run to a single index snapshot.

    Both paginated AI searches sort on ``_score``, which BM25 computes from index-wide
    statistics — so every document's score moves whenever anything is indexed, including
    documents the search does not match.  A cursor stores that score as a literal value,
    which only means what it meant inside the snapshot it was minted in.  The cursor
    therefore carries the point-in-time, and only the first page of a run opens one.

    ``keep_alive`` is set explicitly because ``QueryParameters`` defaults to ten
    seconds, which a paging run outlives.
    """
    return SnapshotBoundQuery(
        query=QueryParameters(
            query_id=(
                after_cursor.pit
                if after_cursor is not None and after_cursor.pit is not None
                else file_repository.open_point_in_time(keep_alive=AI_PIT_KEEPALIVE)
            ),
            keep_alive=AI_PIT_KEEPALIVE,
            search_string=search_string,
        ),
        resumed_from_cursor_pit=after_cursor is not None
        and after_cursor.pit is not None,
    )
