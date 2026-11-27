"""Unit tests for taking an MR out of Draft and giving it exactly one pipeline."""

from unittest.mock import MagicMock

import gitlab

from aitools.gitlab_api import start_mr_pipeline
from aitools.models import AutopilotLimits

BRANCH = "461-some-branch"
HEAD_SHA = "f00dcafef00dcafef00dcafef00dcafef00dcafe"

# No grace period and no sleep between polls: the waits exist for GitLab's benefit and
# would only make the test slow.
IMMEDIATE = AutopilotLimits(pipeline_grace_s=0, pipeline_grace_poll_s=0)


def _make_project(mr: MagicMock, pipelines: list[MagicMock]) -> MagicMock:
    """A project whose branch is at HEAD_SHA and whose MR lookups return `mr`."""
    project = MagicMock()
    project.branches.get.return_value.commit = {"id": HEAD_SHA}
    project.mergerequests.get.return_value = mr
    project.pipelines.get.side_effect = lambda pipeline_id: next(
        p for p in pipelines if p.id == pipeline_id
    )
    return project


def _make_pipeline(pipeline_id: int, sha: str) -> MagicMock:
    pipeline = MagicMock()
    pipeline.id = pipeline_id
    pipeline.sha = sha
    return pipeline


class TestStartMrPipeline:
    def test_draft_mr_is_undrafted_and_gets_a_pipeline(self):
        """A Draft MR can have no pipeline at all, so one is created straight away."""
        created = _make_pipeline(101, HEAD_SHA)
        mr = MagicMock()
        mr.title = "Draft: feat(api): do the thing"
        mr.sha = HEAD_SHA
        mr.pipelines.create.return_value = created
        project = _make_project(mr, [created])

        start = start_mr_pipeline(project, mr, BRANCH, IMMEDIATE)

        assert not mr.title.startswith("Draft")
        mr.save.assert_called()
        assert mr.pipelines.create.call_count == 1
        assert start.created is True
        assert start.pipeline is created

    def test_existing_head_pipeline_is_not_duplicated(self):
        """An open MR already gets a pipeline from GitLab for a push; adopt that one."""
        existing = _make_pipeline(202, HEAD_SHA)
        mr = MagicMock()
        mr.title = "feat(api): do the thing"
        mr.sha = HEAD_SHA
        mr.pipelines.list.return_value = [existing]
        project = _make_project(mr, [existing])

        start = start_mr_pipeline(project, mr, BRANCH, IMMEDIATE)

        mr.pipelines.create.assert_not_called()
        assert start.created is False
        assert start.pipeline is existing

    def test_405_closes_and_reopens_before_retrying(self):
        """GitLab answers 405 while preparing an MR that has lost its branch head."""
        created = _make_pipeline(303, HEAD_SHA)
        mr = MagicMock()
        mr.title = "Draft: feat(api): do the thing"
        mr.sha = HEAD_SHA
        mr.pipelines.create.side_effect = [
            gitlab.exceptions.GitlabCreateError(
                "Method Not Allowed", response_code=405
            ),
            created,
        ]
        project = _make_project(mr, [created])

        start = start_mr_pipeline(project, mr, BRANCH, IMMEDIATE)

        # Reopening is the remedy: a retry without it answers 405 again.
        assert mr.state_event == "reopen"
        assert mr.pipelines.create.call_count == 2
        assert start.reopened is True
        assert start.created is True
        assert start.pipeline is created
