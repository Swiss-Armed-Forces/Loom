import logging
from uuid import UUID

from common.ai_context.tool_models import FilenameSearchEntry, SearchByFilenameResult
from common.dependencies import get_celery_app, get_file_repository
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.models.es_repository import PointInTimeExpiredError
from common.services.query_builder import QueryBuilderException
from elasticsearch import BadRequestError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.infra.snapshot_query import build_snapshot_bound_query
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=AiContextProcessingTask)
def search_by_filename_work_task(
    filename: str,
    search_string: str = "*",
    after_cursor: SearchAfterCursor | None = None,
) -> SearchByFilenameResult:
    file_repository = get_file_repository()
    query, resumed_from_cursor_pit = build_snapshot_bound_query(
        file_repository=file_repository,
        search_string=search_string,
        after_cursor=after_cursor,
    )

    try:
        result = file_repository.get_flat_files_by_query(
            query=query,
            filename=filename,
            after=after_cursor,
            # Explicit, so the number of entries a page spends on the model's context
            # does not follow whatever the folder view is tuned to.
            page_size=settings.tool.browse.page_size,
        )
    # The snapshot the cursor refers to is gone, so the cursor cannot be resumed. To
    # the agent that is the same situation as a cursor it cannot use, and the message
    # of that error already tells it to start again without one.
    except PointInTimeExpiredError as exc:
        logger.warning("search_by_filename: point-in-time expired: %s", exc)
        raise InvalidPaginationCursorError() from exc
    # search_string reaches here from the model, so a malformed query is the agent's
    # mistake and has to come back as a ValueError it can act on. The local Lucene
    # parser reports it as QueryBuilderException, Elasticsearch as BadRequestError.
    except (QueryBuilderException, BadRequestError) as exc:
        # ES answers a malformed point-in-time id and an unusable search_after tuple
        # with the same illegal_argument_exception as a malformed query, so without
        # these two checks a corrupted cursor would send the agent off to fix a query
        # string that is perfectly valid.
        if "search_after" in str(exc) or resumed_from_cursor_pit:
            logger.warning("search_by_filename: unusable cursor: %s", exc)
            raise InvalidPaginationCursorError() from exc
        logger.warning("search_by_filename: invalid query '%s': %s", search_string, exc)
        raise ValueError(
            f"Invalid Lucene query '{search_string}': {exc}. "
            "Use suggest_queries to generate a valid query string."
        ) from exc
    files = [
        FilenameSearchEntry(full_path=str(n.full_path), file_id=n.file_id)
        for n in result.nodes
        if n.file_id is not None
    ]

    return SearchByFilenameResult(
        query=filename,
        search_string=search_string,
        files=files,
        has_more=result.next_cursor is not None,
        next_cursor=result.next_cursor,
        total_count=result.total_count,
        count_relation=result.count_relation,
    )


@app.task(bind=True, base=AiContextProcessingTask)
def search_by_filename_tool_task(
    self: AiContextProcessingTask,
    filename: str,
    _context_id: UUID,
    search_string: str = "*",
    after_cursor: SearchAfterCursor | None = None,
) -> SearchByFilenameResult:
    return self.replace(
        search_by_filename_work_task.s(filename, search_string, after_cursor)
    )
