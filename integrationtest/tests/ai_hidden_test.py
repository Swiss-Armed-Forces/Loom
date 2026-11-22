"""Integration tests for hidden AI contexts.

Hidden is a display filter only: the context is excluded from GET /v1/ai but is
otherwise fully functional.
"""

from utils.ai_helpers import (
    create_ai_context,
    get_ai_context_history,
    list_ai_context_ids,
    set_ai_context_hidden,
)


def test_hidden_context_is_omitted_from_the_list_and_reachable_by_id():
    """Hiding drops a context from the list; unhiding brings the same one back."""
    context = create_ai_context()
    assert context.context_id in list_ai_context_ids()

    assert set_ai_context_hidden(context.context_id, True).hidden is True
    assert context.context_id not in list_ai_context_ids()

    # The flag is the frontend's only way back to a chat the list no longer
    # carries, so the history route has to report it.
    assert get_ai_context_history(context.context_id).hidden is True

    assert set_ai_context_hidden(context.context_id, False).hidden is False
    assert context.context_id in list_ai_context_ids()
