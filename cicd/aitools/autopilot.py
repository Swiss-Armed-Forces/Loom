"""Driving one issue from open to a green pipeline without user interaction.

Nothing here raises `SystemExit`: a strand that exits takes its result with it, and the
milestone summary then silently loses an issue. Every failure becomes an outcome.
"""

import logging
import os
import tempfile
import time
from collections.abc import Callable

from git import Repo
from git.exc import GitCommandError
from gitlab.exceptions import GitlabError
from gitlab.v4.objects import (
    Project,
    ProjectIssue,
    ProjectMergeRequest,
    ProjectPipeline,
)

from ._common import fix_failing_job_and_push, generate_mr_description
from .aitools import run_agent
from .cmd_mr_review import run_review_cycle
from .git_helpers import build_initial_mr_description, load_mr_template
from .gitlab_api import (
    DRAFT_PREFIX,
    PIPELINE_WAITING_STATUSES,
    create_branch_and_mr_for_issue,
    fetch_latest_pipeline_for_mr,
    find_open_mr_for_issue,
    pipeline_matches_head,
    slugify_issue_title,
    start_mr_pipeline,
    update_mr,
)
from .models import (
    AgentRun,
    AutopilotOutcome,
    AutopilotResult,
    AutopilotSettings,
    BranchWorktree,
    ImplementAttempt,
    IssueBranchResult,
    PipelineStart,
    StrandContext,
)
from .prompts import build_implement_prompt
from .worktree import acquire_branch_worktree

logger = logging.getLogger(__name__)

DEFAULT_AUTOPILOT_SETTINGS = AutopilotSettings()

# How an agentic run is performed, so a caller can supply one that does not need a
# backend installed.
AgentRunner = Callable[[str, BranchWorktree, str], AgentRun]


def _find_or_create_issue_mr(
    project: Project, issue: ProjectIssue, repo: Repo
) -> IssueBranchResult:
    """Return the issue's open MR and branch, creating both when there are none."""
    mr = find_open_mr_for_issue(project, issue)
    if mr:
        result = IssueBranchResult(mr=mr, branch_name=mr.source_branch)
        print(f"Found existing MR !{result.mr.iid} on branch {result.branch_name}")
        return result

    try:
        result = create_branch_and_mr_for_issue(project, issue, load_mr_template(repo))
    except GitlabError as e:
        # A re-run after the previous MR was closed finds the branch already there.
        logger.info("Could not create a branch for issue #%s: %s", issue.iid, e)
        result = _mr_on_existing_branch(project, issue, repo)
    print(f"Created MR !{result.mr.iid} on branch {result.branch_name}")
    return result


def _mr_on_existing_branch(
    project: Project, issue: ProjectIssue, repo: Repo
) -> IssueBranchResult:
    """Open an MR for an issue whose branch is already on the server."""
    branch_name = f"{issue.iid}-{slugify_issue_title(issue.title)}"
    mr = project.mergerequests.create(
        {
            "source_branch": branch_name,
            "target_branch": "main",
            "title": f"Draft: {issue.title}",
            "description": build_initial_mr_description(
                load_mr_template(repo), issue.iid
            ),
        }
    )
    return IssueBranchResult(mr=mr, branch_name=branch_name)


def _failure(
    issue: ProjectIssue,
    outcome: AutopilotOutcome,
    detail: str,
    result: IssueBranchResult | None = None,
    worktree: BranchWorktree | None = None,
) -> AutopilotResult:
    """Build a terminal result for an issue that did not reach a green pipeline."""
    return AutopilotResult(
        issue_iid=issue.iid,
        outcome=outcome,
        branch_name=result.branch_name if result else None,
        mr_iid=result.mr.iid if result else None,
        mr_url=result.mr.web_url if result else None,
        pipeline_id=None,
        pipeline_status=None,
        fix_rounds=0,
        review_rounds=0,
        worktree_path=worktree.path if worktree else None,
        detail=detail,
    )


def _run_implement_agent(
    issue: ProjectIssue,
    worktree: BranchWorktree,
    runner: AgentRunner = run_agent,
) -> ImplementAttempt:
    """Run the implementation agent and report whether it committed anything."""
    base_sha = worktree.repo.head.commit.hexsha
    with tempfile.TemporaryDirectory(
        prefix=".loom_implement_", dir=worktree.path
    ) as context_dir:
        with open(os.path.join(context_dir, "issue.md"), "w", encoding="utf-8") as f:
            f.write(f"# {issue.title}\n\n{issue.description or ''}")
        run = runner(build_implement_prompt(issue, context_dir), worktree, "implement")

    # Whether work happened is a question for git: the agent can exit 0 having changed
    # nothing, and it may push what it committed, which leaves origin/<branch>..HEAD
    # empty for a run that did everything asked of it.
    if worktree.repo.head.commit.hexsha == base_sha:
        detail = run.error or "the agent made no commit"
        if worktree.repo.is_dirty(untracked_files=True):
            detail = f"{detail}; it left uncommitted changes behind"
        return ImplementAttempt(committed=False, detail=detail)
    return ImplementAttempt(committed=True, detail="")


def _apply_mr_description(mr: ProjectMergeRequest, worktree: BranchWorktree) -> None:
    """Replace the MR's title and description with ones describing what landed."""
    parsed = generate_mr_description(mr, worktree.repo)
    if not parsed:
        return
    # A model handed a template whose title still said "Draft:" tends to hand it back.
    update_mr(mr, DRAFT_PREFIX.sub("", parsed.title), parsed.body)
    logger.info("Updated MR !%s", mr.iid)


def _head_sha(worktree: BranchWorktree) -> str:
    """The commit the branch points at on the server, as this checkout sees it."""
    try:
        worktree.repo.git.fetch("origin", worktree.branch)
        return str(worktree.repo.commit(f"origin/{worktree.branch}").hexsha)
    except GitCommandError as e:
        logger.warning("Could not read origin/%s: %s", worktree.branch, e)
        return str(worktree.repo.head.commit.hexsha)


def _pipeline_for_head(strand: StrandContext) -> ProjectPipeline | None:
    """The pipeline running the branch's current head, starting one if none is.

    A review fix pushes new commits, and reading success off the pipeline that preceded
    them would call the branch green on code nothing built.
    """
    project, mr, worktree = strand.project, strand.mr, strand.worktree
    try:
        head_sha = _head_sha(worktree)
        pipeline = fetch_latest_pipeline_for_mr(project, mr)
    except GitlabError as e:
        # A transient API failure must not end a run measured in hours.
        logger.warning("GitLab call failed, retrying after the poll interval: %s", e)
        return None

    if pipeline and pipeline_matches_head(pipeline, head_sha):
        return pipeline

    print(f"Waiting for a pipeline on {head_sha[:8]}...")
    restarted = start_mr_pipeline(project, mr, worktree.branch, strand.settings.limits)
    return restarted.pipeline


def _green_loop(strand: StrandContext, start: PipelineStart) -> AutopilotResult:
    """Review the MR, then poll its pipeline until it passes or the caps run out."""
    project, mr, worktree = strand.project, strand.mr, strand.worktree
    limits = strand.settings.limits
    deadline = time.monotonic() + limits.overall_timeout_s
    fix_rounds = 0
    review_rounds = 0
    pipeline = start.pipeline
    status = pipeline.status if pipeline else None

    def finish(outcome: AutopilotOutcome, detail: str) -> AutopilotResult:
        return AutopilotResult(
            issue_iid=0,
            outcome=outcome,
            branch_name=worktree.branch,
            mr_iid=mr.iid,
            mr_url=mr.web_url,
            pipeline_id=pipeline.id if pipeline else None,
            pipeline_status=status,
            fix_rounds=fix_rounds,
            review_rounds=review_rounds,
            worktree_path=worktree.path,
            detail=detail,
        )

    while time.monotonic() < deadline:
        # The review runs in this strand rather than beside it: its fix agent commits in
        # this worktree, and a CI fix agent committing there at the same time would make
        # the two races on the index. The pipeline runs on GitLab meanwhile either way.
        if strand.settings.review and review_rounds < limits.max_review_rounds:
            review_rounds += 1
            cycle = run_review_cycle(mr, worktree, post_comments=True, fix=True)
            print(
                f"Review pass {review_rounds}: {cycle.comments_found} finding(s), "
                f"{cycle.commits_pushed} commit(s) pushed"
            )
            continue

        pipeline = _pipeline_for_head(strand)
        if not pipeline:
            time.sleep(limits.poll_interval_s)
            continue

        status = pipeline.status
        print(f"Pipeline #{pipeline.id}: {status}  {pipeline.web_url}")

        if status in PIPELINE_WAITING_STATUSES:
            time.sleep(limits.poll_interval_s)
            continue

        if status == "success":
            _apply_mr_description(mr, worktree)
            return finish("green", "")

        if status != "failed":
            return finish("pipeline_unresolved", f"pipeline ended as {status!r}")

        if fix_rounds >= limits.max_fix_rounds:
            return finish(
                "fix_rounds_exhausted",
                f"CI still failing after {fix_rounds} fix round(s)",
            )

        fix_failing_job_and_push(project, pipeline, worktree)
        fix_rounds += 1
        time.sleep(limits.poll_interval_s)

    return finish("timed_out", f"gave up after {limits.overall_timeout_s}s")


def implement_issue_autonomously(
    project: Project,
    issue: ProjectIssue,
    base_repo: Repo,
    settings: AutopilotSettings = DEFAULT_AUTOPILOT_SETTINGS,
    *,
    runner: AgentRunner = run_agent,
) -> AutopilotResult:
    """Drive one issue from open to a green pipeline without any user interaction.

    `base_repo` is only read: it supplies the MR template and the git directory the
    worktree is added to. Its checked-out branch is never touched — all commits happen
    in the issue's own worktree.
    """
    print(f"\n=== Issue #{issue.iid}: {issue.title} ===")

    try:
        result = _find_or_create_issue_mr(project, issue, base_repo)
    except GitlabError as e:
        return _failure(issue, "setup_failed", f"could not prepare an MR: {e}")

    try:
        worktree = acquire_branch_worktree(base_repo, result.branch_name)
    except (GitCommandError, RuntimeError) as e:
        return _failure(
            issue, "setup_failed", f"could not acquire a worktree: {e}", result
        )
    print(f"Worktree: {worktree.path}")

    attempt = _run_implement_agent(issue, worktree, runner)
    if not attempt.committed:
        return _failure(issue, "no_commits", attempt.detail, result, worktree)

    try:
        worktree.repo.git.push("--set-upstream", "origin", worktree.branch)
    except GitCommandError as e:
        return _failure(issue, "setup_failed", f"could not push: {e}", result, worktree)

    start = start_mr_pipeline(project, result.mr, worktree.branch, settings.limits)
    if not start.pipeline:
        return _failure(
            issue,
            "pipeline_unresolved",
            f"no pipeline could be started: {start.detail}",
            result,
            worktree,
        )

    strand = StrandContext(
        project=project, mr=result.mr, worktree=worktree, settings=settings
    )
    outcome = _green_loop(strand, start)
    return outcome._replace(issue_iid=issue.iid)
