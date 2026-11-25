import logging
from enum import StrEnum
from uuid import UUID

from celery import chord, group
from common.ai_context.tool_models import QuerySuggestion, SuggestQueriesResult
from common.dependencies import (
    get_celery_app,
    get_file_repository,
)
from common.file.file_repository import File
from common.services.query_builder import QueryParameters
from common.utils.lucene import escape_lucene_phrase

from worker.ai.file_fields import iter_described_fields
from worker.ai.infra.ai_context_processing_task import AiContextProcessingTask
from worker.dependencies import get_llm_suggest_queries_agent
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()


class QueryStrategy(StrEnum):
    """How one candidate builds its query.

    The output is a Lucene query string, so the axis that separates one candidate from
    the next is the shape of the query rather than the wording of the request for it.
    """

    FREE_TEXT = "free_text"
    FIELD_SCOPED = "field_scoped"
    FUZZY = "fuzzy"
    BROAD = "broad"
    NARROW = "narrow"


# One instruction per strategy, rendered into the skeleton `_build_prompt` holds. A
# candidate commits to a single strategy: asking one prompt for free text *and* field
# syntax *and* fuzzy operators leaves the model to resolve the conflict arbitrarily.
_STRATEGY_INSTRUCTIONS: dict[QueryStrategy, str] = {
    QueryStrategy.FREE_TEXT: (
        "Favour free text and phrase matching. Avoid field:value syntax unless a "
        "specific field clearly fits."
    ),
    QueryStrategy.FIELD_SCOPED: (
        "Target AVAILABLE_FIELDS with field:value syntax wherever a field fits the "
        "description."
    ),
    QueryStrategy.FUZZY: (
        "Use fuzzy and proximity operators, so that OCR errors and spelling variants "
        "in the indexed text still match."
    ),
    QueryStrategy.BROAD: (
        "Favour recall: combine synonyms and alternative phrasings with OR and keep "
        "the query permissive."
    ),
    QueryStrategy.NARROW: (
        "Favour precision: combine the essential terms with AND and keep the query "
        "restrictive."
    ),
}


def _build_prompt(
    query_description: str, strategy: QueryStrategy, folder_path: str | None
) -> str:
    """Render the prompt for one candidate query.

    The skeleton carries everything the strategies share, so the Lucene syntax rule and
    the two MUST lines are stated once.
    """
    available_fields = list(iter_described_fields(File))
    fields_text = "\n".join(f"- {f.name}: {f.description}" for f in available_fields)

    prompt = f"""Translate the QUERY_DESCRIPTION to an Elasticsearch query string.
AVAILABLE_FIELDS (you may use these in field:value syntax):
{fields_text}
HINT: Use Lucene Query syntax.
STRATEGY: {_STRATEGY_INSTRUCTIONS[strategy]}
QUERY_DESCRIPTION: {query_description}\n\n
MUST: Only return the plain Lucerne query.
MUST: Do not give an explanation.
"""

    if folder_path:
        prompt += (
            f"\nNOTE: Results will automatically be filtered to files under: "
            f"{folder_path}. Do NOT include path filters in the query — they "
            f"are applied separately."
        )

    return prompt


@app.task(base=AiContextProcessingTask)
def suggest_queries_generate_task(
    query_description: str,
    folder_path: str | None = None,
    strategy: QueryStrategy = QueryStrategy.FREE_TEXT,
    seed: int = 0,
) -> QuerySuggestion:
    """Generate one candidate query, or an empty suggestion if it has to be dropped.

    ``seed`` separates candidates that share a strategy, which happens whenever
    ``num_candidates`` exceeds the strategy count.
    """
    # Celery delivers the member as the plain string it serialises to, so coerce it
    # back: an unknown strategy is then a ValueError here rather than a KeyError
    # during rendering.
    strategy = QueryStrategy(strategy)
    prompt = _build_prompt(query_description, strategy, folder_path)

    agent = get_llm_suggest_queries_agent()

    # This task is one candidate in a chord, and a chord aborts as soon as any
    # of its members fails. Degrade to an empty suggestion -- which
    # suggest_queries_aggregate_task filters out -- so that one bad candidate
    # cannot discard the results of all the others.
    try:
        # A per-run setting is merged over the agent's, so this adds the seed and
        # leaves the configured generation settings alone.
        result = agent.run_sync(prompt, model_settings={"seed": seed})

    except Exception:  # pylint: disable=broad-except
        logger.warning(
            "suggest_queries: dropping candidate, LLM call failed for "
            "description '%s' with strategy %s",
            query_description,
            strategy,
            exc_info=True,
        )
        return QuerySuggestion(query="", matching_docs=0)

    if result is None:
        return QuerySuggestion(query="", matching_docs=0)

    query_string = result.output.query_string
    logger.debug("suggest_queries: strategy %s produced '%s'", strategy, query_string)

    try:
        file_repository = get_file_repository()
        pit_id = file_repository.open_point_in_time()
        search_string = (
            f'full_path.tree:"{escape_lucene_phrase(folder_path)}" AND ({query_string})'
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
    # Cycling rather than zipping keeps the count setting and the strategy list from
    # contradicting each other at any operator-chosen value: above the strategy count
    # the strategies repeat, below it the prefix starts at FREE_TEXT. The index
    # doubles as the seed, so candidates sharing a strategy still differ -- which the
    # default count relies on, being larger than the strategy count -- and a repeated
    # run of one description produces the same candidates.
    strategies = list(QueryStrategy)
    return self.replace(
        chord(
            group(
                suggest_queries_generate_task.s(
                    query_description, folder_path, strategies[i % len(strategies)], i
                )
                for i in range(num_candidates)
            ),
            suggest_queries_aggregate_task.s(),
        )
    )
