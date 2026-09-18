from common.ai_context.tool_models import QuerySuggestion
from common.dependencies import get_celery_app
from worker.ai.tasks.suggest_queries_tool import (
    suggest_queries_generate_task,
)

GET_TIMEOUT = 360


def test_suggest_queries_generate_task():
    result = (
        get_celery_app()
        .send_task(
            suggest_queries_generate_task.name,
            args=[
                "I want to show all files",
                None,
            ],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert isinstance(result, QuerySuggestion)
    assert len(result.query) > 0
