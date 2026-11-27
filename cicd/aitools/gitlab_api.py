import io
import logging
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import gitlab
from git import Repo
from gitlab.exceptions import GitlabError
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

from .config import CI_JOB_TOKEN, CI_PROJECT_ID, CI_SERVER_HOST, GITLAB_TOKEN
from .git_helpers import build_initial_mr_description
from .models import (
    AutopilotLimits,
    IssueBranchResult,
    IssueRef,
    JobRef,
    MilestoneRef,
    MRRef,
    PipelineRef,
    PipelineStart,
    ReviewComment,
)

DRAFT_PREFIX = re.compile(r"^\s*draft:\s*", re.IGNORECASE)

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
    """Create GitLab client from environment variables.

    Prefers a personal/project access token (full API scope) and falls back to
    CI_JOB_TOKEN when running inside GitLab CI.
    """
    url = f"https://{CI_SERVER_HOST}"
    if GITLAB_TOKEN:
        return gitlab.Gitlab(url, private_token=GITLAB_TOKEN)
    if CI_JOB_TOKEN:
        logger.info("Using CI_JOB_TOKEN for GitLab authentication")
        return gitlab.Gitlab(url, job_token=CI_JOB_TOKEN)
    logger.warning("No GitLab token found (GITLAB_TOKEN or CI_JOB_TOKEN)")
    return None


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
    if not mrs:
        return None
    # Re-fetch via .get() so the full MR object is returned, including diff_refs
    # (list() returns lightweight objects that omit diff_refs)
    return project.mergerequests.get(mrs[0].iid)


def update_mr(mr: ProjectMergeRequest, title: str, description: str) -> None:
    """Update MR title and description."""
    mr.title = title
    mr.description = description
    mr.save()


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
    """Parse a GitLab milestone URL or bare IID into a MilestoneRef."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/milestones/(\d+)", value)
    if url_match:
        return MilestoneRef(
            project_path=url_match.group(1), milestone_iid=int(url_match.group(2))
        )
    try:
        return MilestoneRef(project_path=None, milestone_iid=int(value))
    except ValueError as exc:
        raise ValueError(f"Cannot parse milestone URL or IID: {value!r}") from exc


def fetch_milestone_by_ref(
    gl: gitlab.Gitlab, repo: Repo, ref: MilestoneRef
) -> ProjectMilestone:
    """Fetch a GitLab milestone by MilestoneRef.

    The number in a milestone's web URL is its project-scoped iid, while the milestones
    API addresses a milestone by its global id, so the iid is resolved against the
    project's milestone list rather than passed to a GET.
    """
    project_path = ref.project_path or CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_path)
    milestone = find_milestone_by_iid(project, ref.milestone_iid)
    if milestone is None:
        logger.error(
            "No milestone with iid %d in project %s", ref.milestone_iid, project_path
        )
        sys.exit(1)
    return milestone


def find_milestone_by_iid(project: Project, iid: int) -> ProjectMilestone | None:
    """Return the project milestone with the given iid, or None."""
    for milestone in project.milestones.list(all=True):
        if milestone.iid == iid:
            return milestone
    return None


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
    project: Project, issue: ProjectIssue, mr_template: str
) -> IssueBranchResult:
    """Create a branch and draft MR for the given issue.

    The description is rendered from the repository's MR template, so an MR opened by
    aitools has the same shape as one opened through the GitLab UI.
    """
    branch_name = f"{issue.iid}-{slugify_issue_title(issue.title)}"
    project.branches.create({"branch": branch_name, "ref": "main"})
    mr = project.mergerequests.create(
        {
            "source_branch": branch_name,
            "target_branch": "main",
            "title": f"Draft: {issue.title}",
            "description": build_initial_mr_description(mr_template, issue.iid),
        }
    )
    return IssueBranchResult(mr=mr, branch_name=branch_name)


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


def undraft_mr(mr: ProjectMergeRequest) -> bool:
    """Take the MR out of Draft, returning whether the title changed.

    A Draft MR runs no pipeline at all, so this is what makes CI possible for it. The
    title change does not itself create one.
    """
    title = str(mr.title)
    undrafted = DRAFT_PREFIX.sub("", title)
    if undrafted == title:
        return False
    mr.title = undrafted
    mr.save()
    logger.info("Undrafted MR !%s", mr.iid)
    return True


def create_mr_pipeline(project: Project, mr: ProjectMergeRequest) -> ProjectPipeline:
    """Create a pipeline through the merge-request pipelines endpoint.

    The project pipelines endpoint would create a branch pipeline, which the
    `workflow:rules` discard while a merge request is open for the branch.
    """
    created = mr.pipelines.create()
    return project.pipelines.get(created.id)


def reopen_mr(mr: ProjectMergeRequest) -> None:
    """Close and reopen the MR so GitLab re-attaches it to its branch head."""
    logger.info("Closing and reopening MR !%s to re-attach it to its branch", mr.iid)
    mr.state_event = "close"
    mr.save()
    mr.state_event = "reopen"
    mr.save()


def branch_head_sha(project: Project, branch_name: str) -> str:
    """The commit the branch currently points at on the server."""
    return str(project.branches.get(branch_name).commit["id"])


def mr_tracks_branch_head(
    project: Project, mr: ProjectMergeRequest, branch_name: str
) -> bool:
    """Whether the MR has caught up with its branch's head commit."""
    try:
        return str(mr.sha) == branch_head_sha(project, branch_name)
    except GitlabError as e:
        logger.warning("Could not compare MR !%s against its branch: %s", mr.iid, e)
        return False


def pipeline_matches_head(pipeline: ProjectPipeline, head_sha: str) -> bool:
    """Whether this pipeline ran the commit the branch currently points at."""
    return str(getattr(pipeline, "sha", "")) == head_sha


def _await_branch_head(
    project: Project,
    mr: ProjectMergeRequest,
    branch_name: str,
    limits: AutopilotLimits,
) -> ProjectMergeRequest:
    """Wait for the MR to report its branch's head commit, reopening it if it sticks."""
    deadline = time.monotonic() + limits.pipeline_grace_s
    while True:
        if mr_tracks_branch_head(project, mr, branch_name):
            return mr
        if time.monotonic() >= deadline:
            break
        time.sleep(limits.pipeline_grace_poll_s)
        mr = project.mergerequests.get(mr.iid)

    logger.warning(
        "MR !%s still reports %s while its branch is elsewhere", mr.iid, mr.sha
    )
    reopen_mr(mr)
    return project.mergerequests.get(mr.iid)


def _adopt_head_pipeline(
    project: Project,
    mr: ProjectMergeRequest,
    head_sha: str,
    limits: AutopilotLimits,
) -> ProjectPipeline | None:
    """Wait briefly for a pipeline GitLab started for the head commit itself."""
    deadline = time.monotonic() + limits.pipeline_grace_s
    while True:
        pipeline = fetch_latest_pipeline_for_mr(project, mr)
        if pipeline and pipeline_matches_head(pipeline, head_sha):
            return pipeline
        if time.monotonic() >= deadline:
            return None
        time.sleep(limits.pipeline_grace_poll_s)


def start_mr_pipeline(
    project: Project,
    mr: ProjectMergeRequest,
    branch_name: str,
    limits: AutopilotLimits,
) -> PipelineStart:
    """Undraft the MR and make sure exactly one pipeline is running its head commit.

    An MR that is already open and non-draft gets a pipeline from GitLab for a push, so
    that one is adopted; creating another would run the same commit twice. An MR that
    was a Draft until a moment ago can have none, so one is created straight away.
    """
    title_changed = undraft_mr(mr)
    mr = _await_branch_head(project, mr, branch_name, limits)
    reopened = not mr_tracks_branch_head(project, mr, branch_name)

    try:
        head_sha = branch_head_sha(project, branch_name)
    except GitlabError as e:
        return PipelineStart(
            pipeline=None, created=False, reopened=reopened, detail=str(e)
        )

    if not title_changed:
        adopted = _adopt_head_pipeline(project, mr, head_sha, limits)
        if adopted:
            logger.info("Adopted pipeline #%s for %s", adopted.id, head_sha[:8])
            return PipelineStart(
                pipeline=adopted, created=False, reopened=reopened, detail=""
            )

    for attempt in (1, 2):
        try:
            created = create_mr_pipeline(project, mr)
            logger.info("Created pipeline #%s for MR !%s", created.id, mr.iid)
            return PipelineStart(
                pipeline=created,
                created=True,
                reopened=reopened,
                detail="",
            )
        except GitlabError as e:
            if attempt == 2:
                return PipelineStart(
                    pipeline=None, created=False, reopened=reopened, detail=str(e)
                )
            # GitLab answers 405 while it is still preparing the merge request, which
            # it stays in indefinitely once the MR has lost track of its branch.
            logger.warning("Could not create a pipeline for MR !%s: %s", mr.iid, e)
            reopen_mr(mr)
            reopened = True
            mr = project.mergerequests.get(mr.iid)
            mr = _await_branch_head(project, mr, branch_name, limits)

    return PipelineStart(
        pipeline=None, created=False, reopened=reopened, detail="unreachable"
    )


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


def post_review_comment(mr: ProjectMergeRequest, comment: ReviewComment) -> None:
    """Post a single review comment to a GitLab MR.

    Attempts to post as an inline discussion when file and line are available. Falls
    back to a general MR comment (with location prepended) if the inline position is
    rejected by GitLab (e.g. line not in diff).
    """
    diff_refs = getattr(mr, "diff_refs", None) or {}
    can_inline = bool(
        comment.file
        and comment.line
        and diff_refs.get("base_sha")
        and diff_refs.get("start_sha")
        and diff_refs.get("head_sha")
    )

    if can_inline:
        try:
            mr.discussions.create(
                {
                    "body": comment.body,
                    "position": {
                        "base_sha": diff_refs["base_sha"],
                        "start_sha": diff_refs["start_sha"],
                        "head_sha": diff_refs["head_sha"],
                        "position_type": "text",
                        "new_path": comment.file,
                        "old_path": comment.file,
                        "new_line": comment.line,
                    },
                }
            )
            return
        except gitlab.exceptions.GitlabError as e:
            logger.warning(
                "Inline comment failed for %s:%s, falling back to general: %s",
                comment.file,
                comment.line,
                e,
            )

    # General comment fallback: prepend location so context is not lost
    location = (
        f"{comment.file}:{comment.line}"
        if (comment.file and comment.line)
        else (comment.file or "(general)")
    )
    body = f"**[{location}]** ({comment.severity})\n\n{comment.body}"
    mr.discussions.create({"body": body})
