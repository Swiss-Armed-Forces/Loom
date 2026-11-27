import argparse
import logging
import os
import sys
import time

from git import Repo
from gitlab.v4.objects import Project, ProjectIssue

from ._common import _get_gitlab_client_or_exit
from .autopilot import implement_issue_autonomously
from .gitlab_api import (
    fetch_issue_by_ref,
    fetch_milestone_by_ref,
    fetch_open_issues_for_milestone,
    get_project,
    parse_issue_url_or_id,
    parse_milestone_url_or_id,
)
from .models import (
    AutopilotLimits,
    AutopilotResult,
    AutopilotSettings,
    StrandCommandSpec,
    StrandSession,
    StrandWindow,
)
from .tmux_runner import (
    STRAND_POLL_INTERVAL_S,
    ensure_tmux_available,
    kill_session,
    list_strands,
    log_path,
    session_exists,
    session_name,
    socket_path,
    start_session,
    start_strand,
    strand_command,
)
from .worktree import devenv_root

logger = logging.getLogger(__name__)


def _settings_from_args(args: argparse.Namespace) -> AutopilotSettings:
    """Build the run's caps and switches from the command line."""
    return AutopilotSettings(
        limits=AutopilotLimits(
            max_fix_rounds=args.max_fix_rounds,
            overall_timeout_s=args.timeout_minutes * 60,
        ),
        review=not args.no_review,
    )


def _spec_from_args(args: argparse.Namespace) -> StrandCommandSpec:
    """Build the settings a strand repeats on its own command line."""
    return StrandCommandSpec(
        backend=args.backend,
        model=args.model,
        max_fix_rounds=args.max_fix_rounds,
        timeout_minutes=args.timeout_minutes,
        review=not args.no_review,
    )


def _report(result: AutopilotResult) -> None:
    """Print one issue's terminal state."""
    print(f"\n--- Issue #{result.issue_iid}: {result.outcome} ---")
    if result.mr_url:
        print(f"MR:        !{result.mr_iid}  {result.mr_url}")
    if result.worktree_path:
        print(f"Worktree:  {result.worktree_path}")
    if result.pipeline_id:
        print(f"Pipeline:  #{result.pipeline_id} ({result.pipeline_status})")
    print(f"Rounds:    {result.fix_rounds} fix, {result.review_rounds} review")
    if result.detail:
        print(f"Detail:    {result.detail}")


def cmd_implement(args: argparse.Namespace) -> None:
    """Implement a GitLab issue autonomously, through to a green pipeline."""
    try:
        ref = parse_issue_url_or_id(args.issue_number)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    repo = Repo(os.getcwd())
    gl = _get_gitlab_client_or_exit()
    project = get_project(gl, repo)
    issue = fetch_issue_by_ref(gl, repo, ref)

    print(f"\nIssue #{issue.iid}: {issue.title}")
    print(f"URL: {issue.web_url}")
    print(f"Labels: {', '.join(issue.labels) if issue.labels else '(none)'}")

    result = implement_issue_autonomously(
        project, issue, repo, _settings_from_args(args)
    )
    _report(result)
    if result.outcome != "green":
        sys.exit(1)


def _implement_sequentially(
    project: Project,
    issues: list[ProjectIssue],
    repo: Repo,
    args: argparse.Namespace,
) -> list[AutopilotResult]:
    """Run every issue's strand in this process, one after another."""
    settings = _settings_from_args(args)
    return [
        implement_issue_autonomously(project, issue, repo, settings) for issue in issues
    ]


def _strand_session(repo: Repo, milestone_iid: int) -> StrandSession:
    """Describe the tmux session a milestone's strands run in."""
    return StrandSession(
        socket=socket_path(milestone_iid),
        name=session_name(milestone_iid),
        cwd=devenv_root(repo),
        milestone_iid=milestone_iid,
    )


def _launch_strand(
    session: StrandSession, issue: ProjectIssue, args: argparse.Namespace
) -> StrandWindow:
    """Open the tmux window that implements one issue."""
    strand_log = log_path(session.milestone_iid, issue.iid)
    command = strand_command(session.cwd, issue.iid, _spec_from_args(args))
    window = start_strand(session, issue.iid, command, strand_log)
    print(f"Issue #{issue.iid} started in window {window.window_name}")
    print(f"  log: {strand_log}")
    return window


def _summarize_strands(
    session: StrandSession,
    issues: list[ProjectIssue],
    finished: dict[int, int | None],
) -> int:
    """Report how every strand ended, and keep the session when any did not go green."""
    print("\n--- Milestone summary ---")
    for issue in issues:
        code = finished.get(issue.iid)
        state = "green" if code == 0 else f"failed (exit {code})"
        print(
            f"#{issue.iid}: {state}  log: {log_path(session.milestone_iid, issue.iid)}"
        )

    failed = [iid for iid, code in finished.items() if code != 0]
    if failed:
        print(
            f"\n{len(failed)} strand(s) did not finish green — their windows are kept. "
            f"Read them with: tmux -S {session.socket} attach -t {session.name}"
        )
        return 1

    kill_session(session.socket, session.name)
    return 0


def _schedule_strands(
    issues: list[ProjectIssue], session: StrandSession, args: argparse.Namespace
) -> int:
    """Run the issues in tmux windows, at most `--parallel` of them at a time."""
    ensure_tmux_available()

    if session_exists(session.socket, session.name):
        raise RuntimeError(
            f"A session for this milestone is already running. Attach with "
            f"`tmux -S {session.socket} attach -t {session.name}`, or end it with "
            f"`tmux -S {session.socket} kill-server`."
        )

    start_session(session.socket, session.name, session.cwd)
    print(
        f"\nStrands run in tmux. Attach with: "
        f"tmux -S {session.socket} attach -t {session.name}"
    )

    queue = list(issues)
    running: dict[str, StrandWindow] = {}
    finished: dict[int, int | None] = {}

    while queue or running:
        for status in list_strands(session.socket, session.name):
            if status.dead and status.window_name in running:
                del running[status.window_name]
                finished[status.issue_iid] = status.exit_code
                print(f"Issue #{status.issue_iid} finished (exit {status.exit_code})")

        while queue and len(running) < args.parallel:
            window = _launch_strand(session, queue.pop(0), args)
            running[window.window_name] = window

        if queue or running:
            time.sleep(STRAND_POLL_INTERVAL_S)

    return _summarize_strands(session, issues, finished)


def cmd_milestone_implement(args: argparse.Namespace) -> None:
    """Implement every open issue in a GitLab milestone, autonomously."""
    try:
        ref = parse_milestone_url_or_id(args.milestone)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    repo = Repo(os.getcwd())
    gl = _get_gitlab_client_or_exit()
    project = get_project(gl, repo)
    milestone = fetch_milestone_by_ref(gl, repo, ref)
    logger.info("Milestone: %s", milestone.title)

    issues = fetch_open_issues_for_milestone(project, milestone)
    if not issues:
        print("No open issues in milestone.")
        return

    print(f"\nOpen issues in milestone '{milestone.title}':")
    for issue in issues:
        print(f"  #{issue.iid}: {issue.title}")
    print(f"\nRunning {min(args.parallel, len(issues))} strand(s) at a time.")

    if args.no_tmux:
        results = _implement_sequentially(project, issues, repo, args)
        for result in results:
            _report(result)
        if any(result.outcome != "green" for result in results):
            sys.exit(1)
        return

    session = _strand_session(repo, milestone.id)
    try:
        exit_code = _schedule_strands(issues, session, args)
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        # The tmux server outlives this client, so the strands are left running rather
        # than killed mid-commit.
        print(
            f"\nStopped watching. The strands keep running — attach with "
            f"`tmux -S {session.socket} attach -t {session.name}`, or end them with "
            f"`tmux -S {session.socket} kill-server`."
        )
        return
    if exit_code:
        sys.exit(exit_code)
