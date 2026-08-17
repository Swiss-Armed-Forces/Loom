import logging
from uuid import UUID

from common.ai_context.tool_models import (
    ExecuteQueryResult,
    ExecuteQueryResultFile,
    ToolSource,
)
from common.dependencies import get_celery_app, get_file_repository
from common.models.es_repository import PaginationParameters
from common.services.query_builder import QueryParameters
from elasticsearch import BadRequestError

from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.utils.prompt_sanitizer import sanitize_document_text

logger = logging.getLogger(__name__)

app = get_celery_app()

EXECUTE_QUERY_MAX_RESULTS = 10
_MAX_CONTENT_CHARS = 2000


@app.task(base=AiContextProcessingTask)
def execute_query_work_task(
    query_string: str, folder_path: str | None = None
) -> ExecuteQueryResult:
    file_repository = get_file_repository()
    search_string = (
        f'full_path.tree:"{folder_path}" AND ({query_string})'
        if folder_path
        else query_string
    )
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
        search_string=search_string,
    )
    try:
        result = file_repository.get_by_query(
            query=query,
            pagination_params=PaginationParameters(page_size=EXECUTE_QUERY_MAX_RESULTS),
        )
    except BadRequestError as exc:
        logger.warning("execute_query: invalid query '%s': %s", query_string, exc)
        raise ValueError(
            f"Invalid Lucene query '{query_string}': {exc}. "
            "Use suggest_queries to generate a valid query string."
        ) from exc

    files = []
    sources = []
    for file in result.objs:
        highlight_text = ""
        if file.es_meta.highlight:
            snippets = []
            for snippet_list in file.es_meta.highlight.values():
                snippets.extend(snippet_list)
            highlight_text = " ... ".join(snippets)

        content_text = highlight_text or (
            sanitize_document_text(str(file.content))[:_MAX_CONTENT_CHARS]
            if file.content
            else ""
        )
        files.append(
            ExecuteQueryResultFile(
                file_id=str(file.id_),
                text=content_text,
                score=file.es_meta.score,
            )
        )
        sources.append(ToolSource(file_id=file.id_, text=content_text))

    return ExecuteQueryResult(files=files, sources=sources)


@app.task(bind=True, base=AiContextProcessingTask)
def execute_query_tool_task(
    self: AiContextProcessingTask,
    query_string: str,
    _context_id: UUID,
    folder_path: str | None = None,
) -> ExecuteQueryResult:
    return self.replace(execute_query_work_task.s(query_string, folder_path))
