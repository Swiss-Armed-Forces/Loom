"""Shared setup for the dispatch tasks that sweep a whole query."""

from common.file.file_repository import FileRepository
from common.models.es_repository import PointInTimeExpiredError
from common.services.query_builder import SCAN_PIT_KEEPALIVE, QueryParameters

# What every sweeping task declares as autoretry_for. A lapsed point-in-time is
# transient for a sweep that opened its own: it succeeds against a fresh snapshot, and
# retrying restarts the scan from the beginning, which is the only correct way to
# finish it — resuming across snapshots would skip or duplicate files. A sweep given
# its caller's snapshot has no fresh one to fall back on, so its retries fail the same
# way and the task ends unfinished. That is the right answer there: the files it would
# act on are the files somebody was shown and agreed to, and opening another snapshot
# would widen that set behind their back.
SCAN_RETRY_FOR: tuple[type[BaseException], ...] = (PointInTimeExpiredError,)


def build_scan_query(
    file_repository: FileRepository, query: QueryParameters
) -> QueryParameters:
    """Give the query a snapshot sized for a whole-index sweep, unless it brought one.

    A ``query_id`` on the query is the snapshot its caller counted, and the sweep acts
    on it: whoever started the action was shown how many files it covers — the number
    the approval panel carries, the number the search UI shows above its results — and
    that number is only an answer if the files acted on are the files that were
    counted. ``keep_alive`` is raised to a sweep's regardless, because the snapshot now
    has to outlive publishing one Celery message per match rather than one page read.

    Without one the sweep opens its own, for which both halves of the snapshot's
    lifetime are set here: open_point_in_time gives it its initial one, and keep_alive
    is what every page extends it by.
    """
    return QueryParameters(
        query_id=(
            query.query_id
            if query.query_id is not None
            else file_repository.open_point_in_time(keep_alive=SCAN_PIT_KEEPALIVE)
        ),
        keep_alive=SCAN_PIT_KEEPALIVE,
        search_string=query.search_string,
    )
