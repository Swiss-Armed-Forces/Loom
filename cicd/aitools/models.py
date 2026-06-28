from typing import NamedTuple

from gitlab.v4.objects import ProjectMergeRequest, ProjectMergeRequestDiscussion


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
    """MR metadata passed to Claude for prompt generation."""

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


class FileDiffMap(NamedTuple):
    """Per-file diff data for a branch relative to origin/main."""

    stat: str
    files: dict[str, str]  # file_path -> raw diff text


class DiffChunk(NamedTuple):
    """A chunk of file diffs grouped for summarization."""

    files: list[str]  # file paths in this chunk
    diff: str  # concatenated diff text for those files
