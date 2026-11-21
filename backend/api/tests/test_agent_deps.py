"""Unit tests for reading the bulk approvals a resume request names."""

from uuid import uuid4

from ag_ui.core import ResumeEntry

from api.services.agent_deps import collect_approved_bulk_ids


def test_only_an_answer_that_approves_contributes_its_id():
    """A denial and a cancellation are answers too, and neither buys a dispatch."""
    approved, denied, cancelled = uuid4(), uuid4(), uuid4()

    ids = collect_approved_bulk_ids(
        [
            ResumeEntry(
                interrupt_id="i1",
                status="resolved",
                payload={"approved": True},
                metadata={"approvalId": str(approved)},
            ),
            ResumeEntry(
                interrupt_id="i2",
                status="resolved",
                payload={"approved": False},
                metadata={"approvalId": str(denied)},
            ),
            ResumeEntry(
                interrupt_id="i3",
                status="cancelled",
                payload={"approved": True},
                metadata={"approvalId": str(cancelled)},
            ),
        ]
    )

    assert ids == frozenset({approved})


def test_an_answer_without_a_usable_id_names_nothing():
    """What a missing or malformed id costs is decided where the approval is spent,
    which is the place that can say what was not dispatched."""
    assert (
        collect_approved_bulk_ids(
            [
                ResumeEntry(
                    interrupt_id="i1", status="resolved", payload={"approved": True}
                ),
                ResumeEntry(
                    interrupt_id="i2",
                    status="resolved",
                    payload={"approved": True},
                    metadata={"approvalId": "not-a-uuid"},
                ),
            ]
        )
        == frozenset()
    )
