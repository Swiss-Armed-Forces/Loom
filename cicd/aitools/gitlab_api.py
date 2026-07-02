import io
import logging
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import gitlab
from git import Repo
from gitlab.v4.objects import (
    Project,
    ProjectIssue,
    ProjectIssueDiscussion,
    ProjectIssueNote,
    ProjectJob,
    ProjectMergeRequest,
    ProjectMergeRequestDiscussion,
    ProjectMilestone,
    ProjectPipeline,
)

from .config import CI_PROJECT_ID, CI_SERVER_HOST, GITLAB_TOKEN
from .models import IssueRef, JobRef, MilestoneRef, MRRef, PipelineRef

PIPELINE_WAITING_STATUSES: frozenset[str] = frozenset(
    {
        "created",
        "waiting_for_resource",
        "preparing",
        "pending",
        "running",
        "scheduled",
        "canceling",
    }
)

logger = logging.getLogger(__name__)


def get_gitlab_client() -> gitlab.Gitlab | None:
    """Create GitLab client from environment variables."""
    if not GITLAB_TOKEN:
        logger.warning("No GitLab token found (GITLAB_TOKEN or PROJECT_ACCESS_TOKEN)")
        return None
    return gitlab.Gitlab(f"https://{CI_SERVER_HOST}", private_token=GITLAB_TOKEN)


def get_project_id_from_remote(repo: Repo) -> str | None:
    """Try to infer GitLab project path from git remote URL."""
    try:
        remote_url = repo.remotes.origin.url
        # Handle SSH URLs: git@gitlab.com:group/project.git
        ssh_match = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", remote_url)
        if ssh_match:
            return ssh_match.group(1)
        # Handle HTTPS URLs: https://gitlab.com/group/project.git
        https_match = re.match(r"https?://[^/]+/(.+?)(?:\.git)?$", remote_url)
        if https_match:
            return https_match.group(1)
    except (IndexError, AttributeError, ValueError) as e:
        logger.debug("Failed to parse remote URL: %s", e)
    return None


def get_project(gl: gitlab.Gitlab, repo: Repo) -> Project:
    """Get the GitLab project object."""
    project_id = CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_id:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    return gl.projects.get(project_id)


def find_open_mr_for_branch(
    gl: gitlab.Gitlab, branch: str, repo: Repo
) -> ProjectMergeRequest | None:
    """Find an open MR for the given source branch."""
    project_id = CI_PROJECT_ID
    if not project_id:
        # Try to infer from git remote
        project_id = get_project_id_from_remote(repo)
        if not project_id:
            logger.error(
                "Could not determine project ID from CI_PROJECT_ID or git remote"
            )
            return None

    logger.info("Using project ID: %s", project_id)
    project = gl.projects.get(project_id)
    mrs = project.mergerequests.list(source_branch=branch, state="opened", per_page=1)
    return mrs[0] if mrs else None


def update_mr(mr: ProjectMergeRequest, title: str, description: str) -> None:
    """Update MR title and description."""
    mr.title = title
    mr.description = description
    mr.save()


def fetch_issue(gl: gitlab.Gitlab, repo: Repo, issue_number: int) -> ProjectIssue:
    """Fetch a GitLab issue by number."""
    project_id = CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_id:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_id)
    return project.issues.get(issue_number)


def parse_issue_url_or_id(value: str) -> IssueRef:
    """Parse a GitLab issue URL or bare ID into an IssueRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/(?:issues|work_items)/(\d+)", value)
    if url_match:
        return IssueRef(
            project_path=url_match.group(1), issue_id=int(url_match.group(2))
        )
    try:
        return IssueRef(project_path=None, issue_id=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse issue URL or ID: {value!r}") from exc


def fetch_issue_by_ref(gl: gitlab.Gitlab, repo: Repo, ref: IssueRef) -> ProjectIssue:
    """Fetch a GitLab issue by IssueRef, resolving the project from the ref, CI env, or
    git remote."""
    project_path = ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_path)
    return project.issues.get(ref.issue_id)


def fetch_issue_notes(issue: ProjectIssue) -> list[ProjectIssueNote]:
    """Return all non-system notes (user comments) for a GitLab issue."""
    return [note for note in issue.notes.list(all=True) if not note.system]


def format_issue_notes_for_context(notes: list[ProjectIssueNote]) -> str:
    """Format issue notes as a markdown string for context files."""
    if not notes:
        return "(no comments)"
    parts = []
    for note in notes:
        author = (
            note.author.get("username", "unknown")
            if isinstance(note.author, dict)
            else "unknown"
        )
        created = str(note.created_at)[:10]
        parts.append(f"## Comment by @{author} ({created})\n\n{note.body}\n\n---")
    return "\n\n".join(parts)


def update_issue_description(issue: ProjectIssue, description: str) -> None:
    """Update the description of a GitLab issue."""
    issue.description = description
    issue.save()


def fetch_issue_discussions(issue: ProjectIssue) -> list[ProjectIssueDiscussion]:
    """Return all non-system discussions (user comments) for a GitLab issue."""
    result = []
    for discussion in issue.discussions.list(all=True):
        notes = discussion.attributes.get("notes", [])
        if notes and not notes[0].get("system", False):
            result.append(discussion)
    return result


def post_issue_discussion_reply(discussion: ProjectIssueDiscussion, body: str) -> None:
    """Post a reply note in a GitLab issue discussion thread."""
    discussion.notes.create({"body": body})


def fetch_unresolved_discussions(
    mr: ProjectMergeRequest,
) -> list[ProjectMergeRequestDiscussion]:
    """Return unresolved MR discussions."""
    discussions = mr.discussions.list(all=True)
    unresolved = []
    for discussion in discussions:
        notes = discussion.attributes.get("notes", [])
        if not notes:
            continue
        first_note = notes[0]
        if first_note.get("resolvable") and not first_note.get("resolved"):
            unresolved.append(discussion)
    return unresolved


def format_discussions_for_prompt(
    discussions: list[ProjectMergeRequestDiscussion],
) -> str:
    """Format unresolved MR discussions for inclusion in a prompt."""
    parts = []
    for discussion in discussions:
        notes = discussion.attributes.get("notes", [])
        if not notes:
            continue

        first_note = notes[0]
        position = first_note.get("position") or {}
        new_path = position.get("new_path")
        new_line = position.get("new_line")

        if new_path:
            location = f"{new_path}:{new_line}" if new_line else new_path
        else:
            location = "(general comment)"

        thread_lines = [f"Location: {location}"]
        for note in notes:
            author = note.get("author", {}).get("username", "unknown")
            body = note.get("body", "")
            thread_lines.append(f"@{author}:\n{body}")

        parts.append("\n".join(thread_lines))

    return "\n\n---\n\n".join(parts)


def extract_discussion_location(discussion: ProjectMergeRequestDiscussion) -> str:
    """Return a human-readable location string for a discussion."""
    notes = discussion.attributes.get("notes", [])
    if not notes:
        return "(general comment)"
    position = notes[0].get("position") or {}
    new_path = position.get("new_path")
    new_line = position.get("new_line")
    if new_path:
        return f"{new_path}:{new_line}" if new_line else new_path
    return "(general comment)"


def extract_discussion_thread(discussion: ProjectMergeRequestDiscussion) -> str:
    """Return the thread text of a discussion as '@author: body' lines."""
    notes = discussion.attributes.get("notes", [])
    lines = []
    for note in notes:
        author = note.get("author", {}).get("username", "unknown")
        body = note.get("body", "")
        lines.append(f"@{author}: {body}")
    return "\n".join(lines)


def post_discussion_reply(
    discussion: ProjectMergeRequestDiscussion, reply_text: str
) -> None:
    """Post a reply note to a GitLab MR discussion."""
    discussion.notes.create({"body": reply_text})


def parse_milestone_url_or_id(value: str) -> MilestoneRef:
    """Parse a GitLab milestone URL or bare ID into a MilestoneRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/milestones/(\d+)", value)
    if url_match:
        return MilestoneRef(
            project_path=url_match.group(1), milestone_id=int(url_match.group(2))
        )
    try:
        return MilestoneRef(project_path=None, milestone_id=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse milestone URL or ID: {value!r}") from exc


def fetch_milestone_by_ref(
    gl: gitlab.Gitlab, repo: Repo, ref: MilestoneRef
) -> ProjectMilestone:
    """Fetch a GitLab milestone by MilestoneRef."""
    project_path = ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_path)
    return project.milestones.get(ref.milestone_id)


def fetch_open_issues_for_milestone(
    project: Project, milestone: ProjectMilestone
) -> list[ProjectIssue]:
    """Return all open issues for the given milestone."""
    return project.issues.list(milestone=milestone.title, state="opened", all=True)


def _mr_qualifies_for_watch(mr: ProjectMergeRequest) -> bool:
    """Return True if this MR should be included in the watch set."""
    if mr.merge_when_pipeline_succeeds:
        return True
    if bool(mr.approvals.get().approved_by):
        return True
    pipelines = mr.pipelines.list(per_page=1, order_by="id", sort="desc", get_all=False)
    return bool(pipelines and pipelines[0].status in PIPELINE_WAITING_STATUSES)


def fetch_watched_mrs(project: Project) -> list[ProjectMergeRequest]:
    """Return open MRs that are approved, set to auto-merge, or have an active pipeline.

    Filters client-side: merge_when_pipeline_succeeds is a reliable MR attribute;
    "approved" means at least one user has explicitly approved (approved_by non-empty),
    not just that approval requirements are satisfied (which is always true when
    required_approvals_count is 0).
    """
    all_mrs = project.mergerequests.list(state="opened", all=True)
    result: list[ProjectMergeRequest] = []
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(_mr_qualifies_for_watch, mr): mr for mr in all_mrs}
        for future in as_completed(futures):
            mr = futures[future]
            try:
                if future.result():
                    result.append(mr)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "Failed to check qualification for MR !%s: %s", mr.iid, e
                )
    return result


def find_open_mr_for_issue(
    project: Project, issue: ProjectIssue
) -> ProjectMergeRequest | None:
    """Find an open MR linked to the given issue."""
    related = issue.related_merge_requests()
    for mr_dict in related:
        if mr_dict.get("state") == "opened":
            return project.mergerequests.get(mr_dict["iid"])
    return None


def slugify_issue_title(title: str) -> str:
    """Convert an issue title to a URL-safe slug for use in branch names."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def create_branch_and_mr_for_issue(
    project: Project, issue: ProjectIssue
) -> tuple[ProjectMergeRequest, str]:
    """Create a branch and draft MR for the given issue.

    Returns (mr, branch_name).
    """
    branch_name = f"{issue.iid}-{slugify_issue_title(issue.title)}"
    project.branches.create({"branch": branch_name, "ref": "main"})
    mr = project.mergerequests.create(
        {
            "source_branch": branch_name,
            "target_branch": "main",
            "title": f"Draft: {issue.title}",
            "description": f"Closes #{issue.iid}",
        }
    )
    return mr, branch_name


def parse_job_url_or_id(value: str) -> JobRef:
    """Parse a GitLab job URL or bare ID into a JobRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/jobs/(\d+)", value)
    if url_match:
        return JobRef(project_path=url_match.group(1), job_id=int(url_match.group(2)))
    try:
        return JobRef(project_path=None, job_id=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse job URL or ID: {value!r}") from exc


def fetch_job_log(job: ProjectJob) -> str:
    """Fetch the trace/log of a GitLab job."""
    trace = job.trace()
    if isinstance(trace, bytes):
        return trace.decode("utf-8", errors="replace")
    return str(trace)


def extract_job_artifacts(job: ProjectJob, dest_dir: str) -> bool:
    """Download job artifacts zip and extract to dest_dir.

    Returns True if artifacts were found.
    """
    try:
        artifact_bytes = job.artifacts()
    except gitlab.exceptions.GitlabError as e:
        logger.debug("No artifacts available: %s", e)
        return False

    if not artifact_bytes:
        return False

    try:
        with zipfile.ZipFile(io.BytesIO(artifact_bytes)) as zf:
            zf.extractall(dest_dir)
    except zipfile.BadZipFile as e:
        logger.warning("Could not read artifacts zip: %s", e)
        return False

    return True


def prompt_tag_selection(tags: list[str]) -> str:
    """Prompt the user to select a tag for the release."""
    print("\nAvailable tags (newest first):")
    shown = tags[:20]
    for i, tag in enumerate(shown):
        print(f"  {i + 1}. {tag}")
    if len(tags) > 20:
        print(f"  ... and {len(tags) - 20} more")
    print()

    while True:
        answer = input("Enter tag name or number: ").strip()
        if not answer:
            continue
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(tags):
                return tags[idx]
            print(f"Invalid number. Enter 1-{len(tags)}.")
            continue
        except ValueError:
            pass
        if answer in tags:
            return answer
        print(f"Tag {answer!r} not found.")


def find_previous_tag(tags: list[str], current_tag: str) -> str | None:
    """Return the tag immediately before current_tag in the sorted list."""
    try:
        idx = tags.index(current_tag)
        if idx + 1 < len(tags):
            return tags[idx + 1]
    except ValueError:
        pass
    return None


def fetch_milestone_for_tag(project: Project, tag_name: str) -> ProjectMilestone | None:
    """Find a GitLab milestone whose title exactly matches the tag name."""
    for state in ("active", "closed"):
        milestones = project.milestones.list(search=tag_name, state=state, all=True)
        for m in milestones:
            if m.title == tag_name:
                return m
    return None


def parse_mr_url_or_id(value: str) -> MRRef:
    """Parse a GitLab MR URL or bare IID into an MRRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/merge_requests/(\d+)", value)
    if url_match:
        return MRRef(project_path=url_match.group(1), mr_iid=int(url_match.group(2)))
    try:
        return MRRef(project_path=None, mr_iid=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse MR URL or ID: {value!r}") from exc


def fetch_mr_by_ref(gl: gitlab.Gitlab, repo: Repo, ref: MRRef) -> ProjectMergeRequest:
    """Fetch a GitLab MR by MRRef, resolving the project from the ref, CI env, or git
    remote."""
    project_path = ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_path)
    return project.mergerequests.get(ref.mr_iid)


def fetch_latest_pipeline_for_mr(
    project: Project, mr: ProjectMergeRequest
) -> ProjectPipeline | None:
    """Return the most recent pipeline for the given MR, or None if none exist."""
    pipelines = mr.pipelines.list(per_page=1, order_by="id", sort="desc", get_all=False)
    if not pipelines:
        return None
    return project.pipelines.get(pipelines[0].id)


def fetch_first_failing_job(
    project: Project, pipeline: ProjectPipeline
) -> ProjectJob | None:
    """Return the first failed job in the pipeline, promoted to a full ProjectJob."""
    for job in pipeline.jobs.list(all=True):
        if job.status == "failed":
            return project.jobs.get(job.id)
    return None


def format_milestone_items(
    mrs: list[ProjectMergeRequest], issues: list[ProjectIssue]
) -> str:
    """Format milestone MRs and issues into a markdown string for the prompt."""
    parts: list[str] = []

    if mrs:
        parts.append("## Merged Merge Requests\n")
        for mr in mrs:
            parts.append(f"- !{mr.iid}: {mr.title}")
            if mr.description:
                desc = mr.description[:500]
                if len(mr.description) > 500:
                    desc += " [truncated]"
                parts.append(f"  Description: {desc}")
        parts.append("")

    if issues:
        parts.append("## Issues\n")
        for issue in issues:
            labels = f"  Labels: {', '.join(issue.labels)}" if issue.labels else ""
            parts.append(f"- #{issue.iid}: {issue.title}")
            if labels:
                parts.append(labels)
        parts.append("")

    return "\n".join(parts)


def parse_pipeline_url_or_id(value: str) -> PipelineRef:
    """Parse a GitLab pipeline URL or bare ID into a PipelineRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/pipelines/(\d+)", value)
    if url_match:
        return PipelineRef(
            project_path=url_match.group(1), pipeline_id=int(url_match.group(2))
        )
    try:
        return PipelineRef(project_path=None, pipeline_id=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse pipeline URL or ID: {value!r}") from exc


def retry_pipeline(project: Project, pipeline_id: int) -> None:
    """Trigger a retry of the given pipeline."""
    pipeline = project.pipelines.get(pipeline_id)
    pipeline.retry()
