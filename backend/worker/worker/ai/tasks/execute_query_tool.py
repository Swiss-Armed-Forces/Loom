import logging
from uuid import UUID

from common.ai_context.tool_models import (
    ExecuteQueryResult,
    ExecuteQueryResultFile,
)
from common.dependencies import get_celery_app, get_file_repository
from common.file.file_repository import File
from common.llm.prompt_sanitizer import sanitize_document_text
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.models.es_repository import (
    LeadingSnippetHighlight,
    PaginationParameters,
    PointInTimeExpiredError,
    SortingParameters,
)
from common.services.query_builder import QueryBuilderException
from common.utils.lucene import escape_lucene_phrase
from elasticsearch import BadRequestError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.ai.infra.snapshot_query import build_snapshot_bound_query
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()

_MAX_CONTENT_CHARS = 2000
# _to_result_file reads no _source field at all — highlights and score come from
# the hit metadata — but the repository builds a full File, so every field File
# requires has to be fetched. Derived rather than written out so that adding a
# required field to File cannot break this tool at runtime.
_SOURCE_INCLUDES = [
    name for name, field in File.model_fields.items() if field.is_required()
]
# The snippet shown when the query matched nothing inside content. Asking ES for
# the leading characters keeps content out of _source, which is capped at
# TIKA_MAX_TEXT_SIZE (2 MiB) per document and would otherwise be shipped in full
# for every hit of every page just to be cut down to _MAX_CONTENT_CHARS.
_CONTENT_FALLBACK_HIGHLIGHT = LeadingSnippetHighlight(
    field="content", max_chars=_MAX_CONTENT_CHARS
)


def _to_result_file(file: File) -> ExecuteQueryResultFile:
    """Render one hit for the model, capped so a page stays a bounded payload.

    The snippet always comes from the highlights: matched fragments where the query
    matched, and otherwise the leading characters of content, which ES returns for
    an unmatched field thanks to _CONTENT_FALLBACK_HIGHLIGHT.
    """
    snippets: list[str] = []
    if file.es_meta.highlight:
        for snippet_list in file.es_meta.highlight.values():
            snippets.extend(snippet_list)

    # Both steps apply to the joined highlights, which is the only text that reaches
    # the model: fragments are collected from every highlighted field, so without the
    # cap one hit fills the page on its own, and without the sanitising a document can
    # put role tokens and document delimiters into the prompt. There is no _source
    # fallback to sanitise instead — _SOURCE_INCLUDES carries only the required File
    # fields, and content is not one of them.
    content_text = sanitize_document_text(" ... ".join(snippets))[:_MAX_CONTENT_CHARS]

    return ExecuteQueryResultFile(
        file_id=str(file.id_),
        text=content_text,
        score=file.es_meta.score,
    )


@app.task(base=AiContextProcessingTask)
def execute_query_work_task(
    query_string: str,
    folder_path: str | None = None,
    after_cursor: SearchAfterCursor | None = None,
) -> ExecuteQueryResult:
    file_repository = get_file_repository()
    search_string = (
        f'full_path.tree:"{escape_lucene_phrase(folder_path)}" AND ({query_string})'
        if folder_path
        else query_string
    )
    # search_string already folds in folder_path, so a cursor replayed with a
    # different folder_path no longer resumes against an unfiltered query.
    digest = SearchAfterCursor.digest(search_string)
    if after_cursor is not None:
        after_cursor.validate_for(
            expected_src="execute_query",
            expected_digest=digest,
        )
    query, resumed_from_cursor_pit = build_snapshot_bound_query(
        file_repository=file_repository,
        search_string=search_string,
        after_cursor=after_cursor,
    )

    try:
        result = file_repository.get_page_by_query(
            query=query,
            pagination_params=PaginationParameters(
                page_size=settings.tool.execute_query.page_size,
                sort_id=after_cursor.last_sort if after_cursor is not None else [],
            ),
            # Without an explicit sort the repository default is _score
            # ascending, which would hand the model the least relevant matches
            # first and bury the useful ones on the last page.
            sort_params=SortingParameters(
                sort_by_field="_score", sort_direction="desc"
            ),
            source_includes=_SOURCE_INCLUDES,
            leading_snippet_highlight=_CONTENT_FALLBACK_HIGHLIGHT,
        )
    # The snapshot the cursor refers to is gone, so the cursor cannot be resumed. To
    # the agent that is the same situation as a cursor it cannot use, and the message
    # of that error already tells it to start again without one.
    except PointInTimeExpiredError as exc:
        logger.warning("execute_query: point-in-time expired: %s", exc)
        raise InvalidPaginationCursorError() from exc
    # A malformed query string fails in the local Lucene parser
    # (QueryBuilderException); one that parses but that Elasticsearch rejects fails
    # as BadRequestError. Both are the agent's mistake, so both must reach it as a
    # ValueError it can recover from rather than as an opaque backend error.
    except (QueryBuilderException, BadRequestError) as exc:
        if "search_after" in str(exc):
            logger.warning("execute_query: invalid cursor '%s': %s", after_cursor, exc)
            raise InvalidPaginationCursorError() from exc
        # ES answers a malformed point-in-time id with the same
        # illegal_argument_exception as a malformed query, so a corrupted cursor
        # would otherwise be reported as a broken Lucene query and send the
        # caller off to suggest_queries for a query that is perfectly valid.
        if resumed_from_cursor_pit:
            logger.warning("execute_query: unusable cursor point-in-time: %s", exc)
            raise InvalidPaginationCursorError() from exc
        logger.warning("execute_query: invalid query '%s': %s", query_string, exc)
        raise ValueError(
            f"Invalid Lucene query '{query_string}': {exc}. "
            "Use suggest_queries to generate a valid query string."
        ) from exc

    files = [_to_result_file(file) for file in result.objs]

    next_cursor: SearchAfterCursor | None = None
    if result.next_sort_id is not None and result.has_more:
        # PagedSearchResult guarantees a sort id whenever it reports a further
        # page; the check is what tells mypy the same.
        next_cursor = SearchAfterCursor(
            src="execute_query",
            # The snapshot this page was read against, so the next one reads the same.
            pit=query.query_id,
            last_sort=result.next_sort_id,
            query_digest=digest,
        )

    return ExecuteQueryResult(
        files=files,
        total_count=result.total_hits,
        count_relation=result.count_relation,
        has_more=result.has_more,
        next_cursor=next_cursor,
    )


@app.task(bind=True, base=AiContextProcessingTask)
def execute_query_tool_task(
    self: AiContextProcessingTask,
    query_string: str,
    _context_id: UUID,
    folder_path: str | None = None,
    after_cursor: SearchAfterCursor | None = None,
) -> ExecuteQueryResult:
    return self.replace(
        execute_query_work_task.s(query_string, folder_path, after_cursor)
    )
