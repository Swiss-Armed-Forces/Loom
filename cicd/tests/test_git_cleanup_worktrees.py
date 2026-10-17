"""Unit tests for the worktree cleanup verdicts.

The classification is the part worth testing: it decides what gets deleted without being
asked, so every rule that holds a worktree back — an open merge request, uncommitted
work, unpushed commits, an unanswerable GitLab query — is pinned here. Ancestry cannot
stand in for any of it, because Loom squash-merges and a merged branch is never an
ancestor of main.
"""

from pathlib import Path
from typing import List, Optional

import pytest

from git_cleanup_common import WorktreeRef
from git_cleanup_worktrees import (
    MergeRequestFetch,
    MergeRequestLookup,
    MergeRequestState,
    MergeRequestSummary,
    Verdict,
    WorktreeInfo,
    classify,
    interpret_merge_requests,
)

ELSEWHERE = Path("/elsewhere")
WORKTREE = Path("/repo-worktrees/branch")


def make_info(
    state: MergeRequestState = MergeRequestState.MERGED,
    dirty: int = 0,
    unpushed: int = 0,
    path: Path = WORKTREE,
) -> WorktreeInfo:
    """Build a WorktreeInfo for a worktree that exists on disk."""
    return WorktreeInfo(
        ref=WorktreeRef(path, "branch"),
        dirty_files=dirty,
        unpushed=unpushed,
        lookup=MergeRequestLookup(state, "!1:" + state.value),
    )


def verdict_of(info: WorktreeInfo, here: Path = ELSEWHERE) -> Verdict:
    """Classify against a tmp_path-backed worktree and return the verdict."""
    classify(info, here)
    return info.verdict


@pytest.fixture(name="existing")
def fixture_existing(tmp_path: Path) -> Path:
    """A directory that really exists, so the 'prunable' branch is not taken."""
    path = tmp_path / "worktree"
    path.mkdir()
    return path


class TestAutomaticRemoval:
    """Only one combination may be removed without a prompt."""

    def test_merged_clean_and_pushed(self, existing: Path) -> None:
        info = make_info(MergeRequestState.MERGED, path=existing)
        assert verdict_of(info) is Verdict.REMOVE

    def test_reason_names_the_merge_request(self, existing: Path) -> None:
        info = make_info(MergeRequestState.MERGED, path=existing)
        classify(info, ELSEWHERE)
        assert "!1:merged" in info.reasons[0]


class TestHeldBack:
    """Everything that must stop an automatic deletion."""

    def test_open_merge_request_is_kept_without_asking(self, existing: Path) -> None:
        info = make_info(MergeRequestState.OPENED, path=existing)
        assert verdict_of(info) is Verdict.KEEP

    def test_merged_but_dirty_is_asked_about(self, existing: Path) -> None:
        """Uncommitted work must never be discarded unprompted."""
        info = make_info(MergeRequestState.MERGED, dirty=3, path=existing)
        assert verdict_of(info) is Verdict.ASK

    def test_merged_but_unpushed_is_asked_about(self, existing: Path) -> None:
        """A commit that exists nowhere else is not recoverable after removal."""
        info = make_info(MergeRequestState.MERGED, unpushed=2, path=existing)
        assert verdict_of(info) is Verdict.ASK

    def test_closed_merge_request_is_asked_about(self, existing: Path) -> None:
        """Closed means abandoned or superseded — the operator decides."""
        info = make_info(MergeRequestState.CLOSED, path=existing)
        assert verdict_of(info) is Verdict.ASK

    def test_no_merge_request_is_asked_about(self, existing: Path) -> None:
        info = make_info(MergeRequestState.NONE, path=existing)
        assert verdict_of(info) is Verdict.ASK

    def test_unknown_state_is_asked_about(self, existing: Path) -> None:
        """A failed glab query must not read as 'finished'."""
        info = make_info(MergeRequestState.UNKNOWN, path=existing)
        assert verdict_of(info) is Verdict.ASK

    def test_current_directory_is_always_kept(self, existing: Path) -> None:
        """Removing the worktree you are standing in breaks the running shell."""
        info = make_info(MergeRequestState.MERGED, path=existing)
        assert verdict_of(info, here=existing.resolve()) is Verdict.KEEP

    def test_subdirectory_of_the_worktree_counts_as_inside(
        self, existing: Path
    ) -> None:
        nested = existing / "backend"
        nested.mkdir()
        info = make_info(MergeRequestState.MERGED, path=existing)
        assert verdict_of(info, here=nested.resolve()) is Verdict.KEEP

    def test_missing_directory_is_asked_about(self) -> None:
        info = make_info(MergeRequestState.MERGED, path=Path("/does/not/exist"))
        assert verdict_of(info) is Verdict.ASK


class TestBlockersAreReported:
    """The operator has to be told what they are about to lose."""

    def test_dirty_count_appears(self, existing: Path) -> None:
        info = make_info(MergeRequestState.NONE, dirty=4, path=existing)
        classify(info, ELSEWHERE)
        assert any("4 uncommitted" in reason for reason in info.reasons)

    def test_unpushed_count_appears(self, existing: Path) -> None:
        info = make_info(MergeRequestState.CLOSED, unpushed=2, path=existing)
        classify(info, ELSEWHERE)
        assert any("2 unpushed" in reason for reason in info.reasons)

    def test_needs_force_tracks_dirtiness(self, existing: Path) -> None:
        """Git refuses to remove a dirty worktree without --force."""
        assert make_info(dirty=1, path=existing).needs_force is True
        assert make_info(dirty=0, path=existing).needs_force is False


class TestInterpretMergeRequests:
    """Turning a glab answer into a state."""

    @staticmethod
    def _fetch(states: List[str], error: Optional[str] = None) -> MergeRequestFetch:
        return MergeRequestFetch(
            [MergeRequestSummary(index + 1, s) for index, s in enumerate(states)],
            error,
        )

    def test_single_merged(self) -> None:
        assert interpret_merge_requests(self._fetch(["merged"])).state is (
            MergeRequestState.MERGED
        )

    def test_no_merge_requests(self) -> None:
        assert interpret_merge_requests(self._fetch([])).state is MergeRequestState.NONE

    def test_open_wins_over_merged(self) -> None:
        """A branch reused for a second merge request must not look finished."""
        lookup = interpret_merge_requests(self._fetch(["merged", "opened"]))
        assert lookup.state is MergeRequestState.OPENED

    def test_merged_wins_over_closed(self) -> None:
        """One closed attempt does not undo a merge that landed."""
        lookup = interpret_merge_requests(self._fetch(["closed", "merged"]))
        assert lookup.state is MergeRequestState.MERGED

    def test_all_closed(self) -> None:
        lookup = interpret_merge_requests(self._fetch(["closed", "closed"]))
        assert lookup.state is MergeRequestState.CLOSED

    def test_error_is_unknown_not_none(self) -> None:
        """A failed query must be distinguishable from 'no merge request'."""
        lookup = interpret_merge_requests(self._fetch([], error="glab query failed"))
        assert lookup.state is MergeRequestState.UNKNOWN
        assert lookup.label == "glab query failed"

    def test_label_lists_every_merge_request(self) -> None:
        lookup = interpret_merge_requests(self._fetch(["merged", "closed"]))
        assert lookup.label == "!1:merged !2:closed"
