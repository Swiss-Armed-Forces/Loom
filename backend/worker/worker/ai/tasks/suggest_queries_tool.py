import logging
from uuid import UUID

from celery import chord, group
from common.ai_context.tool_models import QuerySuggestion, SuggestQueriesResult
from common.dependencies import get_celery_app, get_file_repository, get_llm_tool_client
from common.file.file_repository import File
from common.services.query_builder import QueryParameters
from pydantic import BaseModel

from worker.ai.file_fields import iter_described_fields
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()


class _ElasticsearchQuery(BaseModel):
    query_string: str


@app.task(base=AiContextProcessingTask)
def suggest_queries_generate_task(
    query_description: str, folder_path: str | None = None
) -> QuerySuggestion:
    available_fields = list(iter_described_fields(File))
    fields_text = "\n".join(f"- {f.name}: {f.description}" for f in available_fields)

    prompt = f"""Translate the QUERY_DESCRIPTION to an Elasticsearch query string.
AVAILABLE_FIELDS (you may use these in field:value syntax):
{fields_text}
HINT: Use Lucene features (AND, OR, wildcards, fuzzy, proximity, ranges).
HINT: Favour free text search over field queries unless a specific field clearly fits.
HINT: Use Lucene Query syntax.
QUERY_DESCRIPTION: {query_description}"""

    if folder_path:
        prompt += (
            f"\nNOTE: Results will automatically be filtered to files under: "
            f"{folder_path}. Do NOT include path filters in the query — they "
            f"are applied separately."
        )

    client = get_llm_tool_client()

    response = client.beta.chat.completions.parse(
        model=settings.llm.tool.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.llm.tool.temperature,
        extra_headers=settings.llm.tool.extra_headers,
        extra_body=settings.llm.tool.extra_body,
        response_format=_ElasticsearchQuery,
        max_tokens=settings.llm.tool.max_tokens,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        return QuerySuggestion(query="", matching_docs=0)

    query_string = parsed.query_string

    try:
        file_repository = get_file_repository()
        pit_id = file_repository.open_point_in_time()
        search_string = (
            f'full_path.tree:"{folder_path}" AND ({query_string})'
            if folder_path
            else query_string
        )
        query = QueryParameters(query_id=pit_id, search_string=search_string)
        stats = file_repository.count_and_score_stats_by_query(query)
    except Exception:  # pylint: disable=broad-except
        logger.warning("suggest_queries: failed to count for query '%s'", query_string)
        return QuerySuggestion(query=query_string, matching_docs=0)

    return QuerySuggestion(
        query=query_string,
        matching_docs=stats.total,
        max_score=stats.max_score,
        avg_score=stats.avg_score,
    )


@app.task(base=AiContextProcessingTask)
def suggest_queries_aggregate_task(candidates: list) -> SuggestQueriesResult:
    """Deduplicate and sort candidates by match count descending."""
    # Celery chord + self.replace() wraps results in an extra list
    if candidates and isinstance(candidates[0], list):
        candidates = candidates[0]
    parsed = [QuerySuggestion.model_validate(c) for c in candidates]
    seen: dict[str, QuerySuggestion] = {}
    for c in parsed:
        prev = seen.get(c.query)
        if prev is None or c.matching_docs > prev.matching_docs:
            seen[c.query] = c
    sorted_candidates = sorted(
        [c for c in seen.values() if c.matching_docs > 0],
        key=lambda c: c.matching_docs,
        reverse=True,
    )
    return SuggestQueriesResult(
        candidates=sorted_candidates[: settings.tool.suggest_queries.max_results]
    )


@app.task(bind=True, base=AiContextProcessingTask)
def suggest_queries_task(
    self: AiContextProcessingTask,
    query_description: str,
    _context_id: UUID,
    folder_path: str | None = None,
) -> SuggestQueriesResult:
    num_candidates = settings.tool.suggest_queries.num_candidates
    return self.replace(
        chord(
            group(
                suggest_queries_generate_task.s(query_description, folder_path)
                for _ in range(num_candidates)
            ),
            suggest_queries_aggregate_task.s(),
        )
    )
