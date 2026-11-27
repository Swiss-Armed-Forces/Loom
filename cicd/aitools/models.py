from typing import Literal, NamedTuple

from git import Repo
from gitlab.v4.objects import (
    Project,
    ProjectIssueDiscussion,
    ProjectMergeRequest,
    ProjectMergeRequestDiscussion,
    ProjectPipeline,
)


class CommitMessage(NamedTuple):
    """Parsed commit message split into title and body."""

    title: str
    body: str


class JobRef(NamedTuple):
    """Parsed GitLab job reference from a URL or bare job ID."""

    project_path: str | None
    job_id: int


class PipelineRef(NamedTuple):
    """Parsed GitLab pipeline reference from a URL or bare pipeline ID."""

    project_path: str | None
    pipeline_id: int


class IssueRef(NamedTuple):
    """Parsed GitLab issue reference from a URL or bare issue ID."""

    project_path: str | None
    issue_id: int


class MilestoneRef(NamedTuple):
    """Parsed GitLab milestone reference from a URL or bare milestone ID."""

    project_path: str | None
    milestone_id: int


class MRRef(NamedTuple):
    """Parsed GitLab MR reference from a URL or bare MR IID."""

    project_path: str | None
    mr_iid: int


class MRContext(NamedTuple):
    """MR metadata passed to AI for prompt generation."""

    title: str = ""
    description: str = ""
    user_instructions: str = ""


class IssueBranchResult(NamedTuple):
    """Result of preparing a branch for an issue implementation."""

    mr: ProjectMergeRequest
    branch_name: str


class DiscussionReply(NamedTuple):
    """A generated reply for a single MR review discussion."""

    discussion: ProjectMergeRequestDiscussion
    location: str
    reply: str


class IssueNoteReply(NamedTuple):
    """A generated reply for a single issue comment thread."""

    discussion: ProjectIssueDiscussion
    reply: str


class DiffRange(NamedTuple):
    """The two tree-ishes whose diff is a branch's own contribution to its target."""

    left: str  # baseline: "origin/<target>", or a merge-base sha when degraded
    right: str  # branch content: the merged tree sha, or the branch ref itself
    ref: str  # the branch ref this range was resolved for
    strategy: Literal["merge-tree", "merge-base"]
    behind_count: int  # commits on origin/<target> not reachable from the branch


class FileDiffMap(NamedTuple):
    """Per-file diff data for a branch relative to its target branch."""

    stat: str
    files: dict[str, str]  # file_path -> raw diff text


class DiffChunk(NamedTuple):
    """A chunk of file diffs grouped for summarization."""

    files: list[str]  # file paths in this chunk
    diff: str  # concatenated diff text for those files


class ReviewComment(NamedTuple):
    """A single AI review comment with optional inline file/line position."""

    file: str | None  # repo-relative path, or None for a general MR comment
    line: int | None  # line number in the new file, or None if not applicable
    severity: str  # "Critical", "High", or "Low"
    body: str  # the comment text
    context: str | None  # relevant code snippet(s) to show alongside the comment


class BranchWorktree(NamedTuple):
    """The checkout a subcommand does its work in, dedicated to one branch."""

    repo: Repo
    path: str  # absolute, unlike Repo.working_dir which may be None
    branch: str
    created: bool  # this call added the worktree
    in_place: bool  # this is the invoking checkout, no worktree was added


class WorktreeEnvironment(NamedTuple):
    """Whether a checkout has a devenv environment of its own, and how to enter it."""

    ready: bool
    prefix: list[str]  # argv prefix entering it, empty when none is needed
    reason: str  # why it is not ready, "" when it is


class AgentCommand(NamedTuple):
    """The argv and stdin of one headless agent invocation."""

    argv: list[str]
    stdin_text: str  # "" when the prompt travels in argv


class AgentEvent(NamedTuple):
    """One decoded line of a backend's streaming output."""

    kind: str  # "system", "assistant", "result" or "other"
    summary: str  # one-line progress text, "" when there is nothing to show
    is_error: bool
    turns: int  # turns reported on a result event, 0 otherwise


class AgentOutcome(NamedTuple):
    """What the agent's output stream said, independent of how the process ended."""

    reported_error: bool
    turns: int
    last_text: str


class AgentExecution(NamedTuple):
    """How the backend process itself ended, before it is judged."""

    exit_code: int
    killed: str  # why the watchdog killed it, "" when it exited on its own
    outcome: AgentOutcome


class AgentRun(NamedTuple):
    """Outcome of one headless agentic run."""

    ok: bool
    exit_code: int  # -1 when the watchdog killed the process
    duration_s: float
    turns: int
    transcript_path: str
    error: str  # short reason when ok is False, "" otherwise


AutopilotOutcome = Literal[
    "green",  # the pipeline for the branch head succeeded
    "no_commits",  # the implement agent produced no commit
    "fix_rounds_exhausted",  # the fix-round cap was spent, CI still failing
    "timed_out",  # the overall wall clock elapsed
    "pipeline_unresolved",  # terminal status that is neither success nor failed
    "setup_failed",  # worktree, branch/MR or push error
]


class AutopilotLimits(NamedTuple):
    """Caps bounding one issue's autonomous run."""

    max_fix_rounds: int = 5
    max_review_rounds: int = 1
    overall_timeout_s: int = 4 * 3600
    poll_interval_s: int = 180
    pipeline_grace_s: int = 120
    pipeline_grace_poll_s: int = 5


class AutopilotSettings(NamedTuple):
    """What bounds and shapes one issue's autonomous run."""

    limits: AutopilotLimits = AutopilotLimits()
    review: bool = True


class StrandContext(NamedTuple):
    """Everything one issue's green loop works on."""

    project: Project
    mr: ProjectMergeRequest
    worktree: BranchWorktree
    settings: AutopilotSettings


class AutopilotResult(NamedTuple):
    """Terminal state of one issue's autonomous run."""

    issue_iid: int
    outcome: AutopilotOutcome
    branch_name: str | None
    mr_iid: int | None
    mr_url: str | None
    pipeline_id: int | None
    pipeline_status: str | None
    fix_rounds: int
    review_rounds: int
    worktree_path: str | None
    detail: str  # why it ended as it did, "" when green


class ImplementAttempt(NamedTuple):
    """Whether the implementation agent left a commit behind, and why not."""

    committed: bool
    detail: str


class FixRoundResult(NamedTuple):
    """What one CI-failure fix round changed."""

    job_id: int | None
    commits_pushed: int
    pushed: bool


class ReviewFindings(NamedTuple):
    """The findings of one review agent run, with the range they were found in."""

    comments: list[ReviewComment]
    diff_range: DiffRange
    run_ok: bool


class ReviewCycleResult(NamedTuple):
    """Outcome of one automated review-and-fix pass over an MR."""

    comments_found: int
    comments_posted: int
    fixed: bool
    commits_pushed: int


class PipelineStart(NamedTuple):
    """How the MR's current pipeline came to exist."""

    pipeline: ProjectPipeline | None
    created: bool  # this run called mr.pipelines.create()
    reopened: bool  # the MR had to be closed and reopened first
    detail: str


class StrandSession(NamedTuple):
    """The tmux session a milestone's strands run in."""

    socket: str
    name: str
    cwd: str
    milestone_iid: int


class StrandCommandSpec(NamedTuple):
    """The run settings a strand's own aitools invocation carries on its command
    line."""

    backend: str
    model: str
    max_fix_rounds: int
    timeout_minutes: int
    review: bool


class StrandWindow(NamedTuple):
    """One tmux window running one issue's autopilot."""

    issue_iid: int
    window_name: str


class StrandStatus(NamedTuple):
    """Live state of one strand window."""

    issue_iid: int
    window_name: str
    dead: bool
    exit_code: int | None
