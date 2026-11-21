"""State an agent run carries alongside its context."""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Sequence
from uuid import UUID

from ag_ui.core import ResumeEntry
from common.ai_context.ai_context_repository import AiContext
from common.ai_context.tool_models import ToolSource


@dataclass
class AgentDeps:
    """State one agent run carries alongside its context."""

    context: AiContext
    source_collector: list[ToolSource] = dataclass_field(default_factory=list)
    # The bulk approvals the client named in this request. A tool that dispatches on
    # an approval requires its id to be in here, so an answer only spends the approval
    # the client was answering.
    approved_bulk_ids: frozenset[UUID] = frozenset()


def collect_approved_bulk_ids(resume: Sequence[ResumeEntry] | None) -> frozenset[UUID]:
    """The bulk approval ids this request approves.

    Each answer to an approval interrupt carries the ``approval_id`` the backend minted
    for the question, in ``ResumeEntry.metadata`` — the envelope AG-UI keeps for routing
    keys, and the only part of an answer that survives the trip: the adapter maps a
    resume entry to approve-or-deny and hands the tool nothing else.

    Only an entry that actually approves contributes. An id that is not a UUID, or that
    rides on a denial or a cancellation, is left out rather than refused here: what it
    buys is checked where the approval is spent, and that is the place that can say what
    was not dispatched.
    """
    if not resume:
        return frozenset()

    approved: set[UUID] = set()
    for entry in resume:
        if entry.status != "resolved":
            continue
        payload: Any = entry.payload
        if not isinstance(payload, dict) or payload.get("approved") is not True:
            continue
        raw_id = (entry.metadata or {}).get("approvalId")
        if not isinstance(raw_id, str):
            continue
        try:
            approved.add(UUID(raw_id))
        except ValueError:
            continue
    return frozenset(approved)
