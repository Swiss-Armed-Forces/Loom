#!/usr/bin/env python3

import argparse
import io
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import gitlab
from git import Repo
from gitlab.v4.objects import ProjectMergeRequest

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Constants from environment variables
CI_SERVER_HOST = os.getenv("CI_SERVER_HOST", "gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN") or os.getenv("PROJECT_ACCESS_TOKEN")
CI_PROJECT_ID = os.getenv("CI_PROJECT_ID")
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "120"))
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "50000"))

# Pathspecs for files to exclude from diffs (lockfiles, generated files)
EXCLUDED_PATHSPECS = [
    ":(exclude)**/poetry.lock",
    ":(exclude)**/pnpm-lock.yaml",
    ":(exclude)Frontend/src/app/api/generated/**",
]


def get_branch_diff(repo: Repo) -> str:
    """Return the diff of commits on the current branch relative to origin/main.

    Uses the merge base so that commits in main that are not yet in this branch
    are excluded. Excludes lockfiles and generated files. Prepends a --stat
    summary. Truncates the diff body if it exceeds MAX_DIFF_CHARS.
    """
    repo.git.fetch("origin", "main")
    merge_base = repo.git.merge_base("origin/main", "HEAD").strip()
    logger.debug("Merge base: %s", merge_base)

    stat = repo.git.diff(merge_base, "HEAD", "--stat", "--", *EXCLUDED_PATHSPECS)
    diff = repo.git.diff(merge_base, "HEAD", "--", *EXCLUDED_PATHSPECS)

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + (
            f"\n\n[Diff truncated at {MAX_DIFF_CHARS} characters."
            " See stat summary above for full file list.]"
        )
        logger.warning("Diff truncated to %d characters", MAX_DIFF_CHARS)

    result = f"Changed files:\n{stat}\n\nDiff:\n{diff}" if stat else f"Diff:\n{diff}"
    logger.debug("Branch diff retrieved: %d characters", len(result))
    return result


def load_mr_template(repo: Repo) -> str:
    """Load the MR template from the repository."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return ""

    template_path = os.path.join(
        repo.working_dir, ".gitlab", "merge_request_templates", "Default.md"
    )
    try:
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("MR template not found at %s", template_path)
        return ""



def build_mr_update_prompt(
    mr_template: str,
    current_title: str = "",
    current_description: str = "",
    include_diff: str | None = None,
    user_instructions: str = "",
) -> str:
    """Build the prompt for MR title/description generation.

    Args:
        mr_template: The MR template content to include in instructions.
        current_title: The current MR title (as a hint for the AI).
        current_description: The current MR description (as a hint for the AI).
        include_diff: If provided, append the diff to the prompt.
        user_instructions: Additional user instructions to append to the prompt.
    """
    template_instruction = ""
    if mr_template:
        template_instruction = f"""
- MR description body should follow this template:

{mr_template}

For the Summary section, write a brief paragraph summarizing the changes, followed by
sections like "Added:", "Changed:", "Removed:", "Fixed:" with bullet points (use "- " for bullets).

Leave the Issue Reference section empty (it will be filled manually).
"""

    current_mr_hint = ""
    if current_title or current_description:
        current_mr_hint = "\nCurrent MR content (use as reference):\n"
        if current_title:
            current_mr_hint += f"Title: {current_title}\n"
        if current_description:
            current_mr_hint += f"Description:\n{current_description}\n"

    prompt = f"""Generate a git commit message and MR description for the following diff.

Format:
- First line: conventional commit format (type(scope): description), max 72 characters
- Blank line
{template_instruction}
Rules:
- Describe what changed, not why
- Output only the raw commit message text, nothing else
- Do NOT wrap output in code fences or markdown code blocks
- Use markdown formatting for the body (headers with #, bullet points with -)
- Preserve external references from the current description if still relevant (e.g., "Closes #123",
  "Related to #456", links to issues/MRs, or other cross-references)
{current_mr_hint}"""

    if user_instructions:
        prompt += f"\nAdditional user instructions:\n{user_instructions}\n"

    if include_diff:
        prompt += f"\nDiff:\n{include_diff}\n"

    return prompt


def is_claude_cli_installed() -> bool:
    """Check if the Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def generate_commit_message_via_claude(
    diff: str,
    mr_template: str,
    repo: Repo,
    current_title: str = "",
    current_description: str = "",
    user_instructions: str = "",
) -> str | None:
    """Generate a commit message using the Claude Code CLI."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return None

    prompt = build_mr_update_prompt(
        mr_template,
        current_title,
        current_description,
        include_diff=diff,
        user_instructions=user_instructions,
    )

    try:
        logger.info("Sending diff to Claude CLI for commit message suggestion...")
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--output-format",
                "text",
                "--no-session-persistence",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=repo.working_dir,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(
                "Claude CLI returned non-zero exit code: %s", result.returncode
            )
            if result.stdout:
                logger.warning("Claude CLI stdout: %s", result.stdout)
            if result.stderr:
                logger.warning("Claude CLI stderr: %s", result.stderr)
            return None

        message = result.stdout.strip()
        logger.debug("Claude CLI response: %s", message)
        return message if message else None

    except subprocess.TimeoutExpired:
        logger.warning("Claude CLI timed out after %s seconds", CLAUDE_TIMEOUT)
        return None
    except OSError as e:
        logger.warning("Failed to run Claude CLI: %s", e)
        return None


def parse_commit_message(message: str) -> tuple[str, str]:
    """Split commit message into title (first line) and body (rest)."""
    lines = message.strip().split("\n", 1)
    title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    return title, body


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
    except Exception as e:
        logger.debug("Failed to parse remote URL: %s", e)
    return None


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


def fetch_issue(gl: gitlab.Gitlab, repo: Repo, issue_number: int):  # type: ignore[return]
    """Fetch a GitLab issue by number."""
    project_id = CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_id:
        logger.error("Could not determine project ID from CI_PROJECT_ID or git remote")
        sys.exit(1)
    project = gl.projects.get(project_id)
    return project.issues.get(issue_number)


def build_implement_prompt(issue, context_dir: str) -> str:  # type: ignore[no-untyped-def]
    """Build the prompt for implementing a GitLab issue."""
    labels = ", ".join(issue.labels) if issue.labels else "(none)"

    return f"""You are implementing a GitLab issue for the Loom project.

## Issue

Title: {issue.title}
URL: {issue.web_url}
Labels: {labels}

## Context

All context files are in: {context_dir}
- issue.md — full issue description

## Task

Implement the changes described in the issue. Follow the project conventions in CLAUDE.md.
Make the necessary code changes, write tests where appropriate, and ensure the implementation
is complete. Do NOT commit or push the changes.
"""


def fetch_unresolved_discussions(mr: ProjectMergeRequest) -> list:
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


def format_discussions_for_prompt(discussions: list) -> str:
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


def build_mr_fix_prompt(mr: ProjectMergeRequest, context_dir: str) -> str:
    """Build the prompt for fixing MR review comments."""
    return f"""You are addressing code review comments on a GitLab merge request.

## Merge Request

Title: {mr.title}
URL: {mr.web_url}

## Context

All context files are in: {context_dir}
- review_comments.txt — unresolved review threads
- branch.diff — current branch diff

## Task

Address each unresolved review comment by modifying the relevant source files.
Follow the existing code style and project conventions. Do NOT commit or push the changes.
"""


def parse_job_url_or_id(value: str) -> tuple[str | None, int]:
    """Parse a GitLab job URL or bare ID into (project_path_or_None, job_id)."""
    url_match = re.match(r"https?://[^/]+/(.+?)/-/jobs/(\d+)", value)
    if url_match:
        return url_match.group(1), int(url_match.group(2))
    try:
        return None, int(value)
    except ValueError:
        raise ValueError(f"Cannot parse job URL or ID: {value!r}")


def fetch_job_log(job) -> str:  # type: ignore[no-untyped-def]
    """Fetch the trace/log of a GitLab job."""
    trace = job.trace()
    if isinstance(trace, bytes):
        return trace.decode("utf-8", errors="replace")
    return str(trace)


def extract_job_artifacts(job, dest_dir: str) -> bool:  # type: ignore[no-untyped-def]
    """Download job artifacts zip and extract to dest_dir. Returns True if artifacts were found."""
    try:
        artifact_bytes = job.artifacts()
    except Exception as e:
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


def build_diagnose_prompt(job, context_dir: str) -> str:  # type: ignore[no-untyped-def]
    """Build the prompt for diagnosing a CI/CD job failure."""
    return f"""You are diagnosing a failed GitLab CI/CD job in the Loom project.

## Job Details

Job ID: {job.id}
Job Name: {job.name}
Stage: {job.stage}
Status: {job.status}
URL: {job.web_url}

## Context

All context files are in: {context_dir}
- job_log.txt — full job log
- artifacts/ — extracted job artifacts (empty if none)

## Task

Using the job log, artifacts (if any), and the project source code, find the root cause
of this CI/CD failure. Navigate the codebase as needed to understand the context.
Provide a clear explanation of what went wrong and suggest how to fix it.
"""


def run_claude_agentic(prompt: str, repo: Repo) -> None:
    """Run Claude CLI in agentic mode, handing over the terminal to the user."""
    if not repo.working_dir:
        logger.error("No working directory available (bare repo?)")
        sys.exit(1)

    if not is_claude_cli_installed():
        logger.error("Claude CLI is not installed.")
        sys.exit(1)

    subprocess.run(
        ["claude", prompt],
        cwd=repo.working_dir,
        check=False,
    )


def cmd_mr_update(args: argparse.Namespace) -> None:
    """Update GitLab MR title and description using Claude."""
    user_instructions = " ".join(args.instructions) if args.instructions else ""

    if user_instructions:
        logger.info("User instructions: %s", user_instructions)

    repo = Repo(os.getcwd())
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)

    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)

    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)

    logger.info("Found MR !%s: %s", mr.iid, mr.title)

    current_title = mr.title or ""
    current_description = mr.description or ""

    diff = get_branch_diff(repo)
    if not diff:
        logger.info("No changes on this branch compared to its merge base.")
        return

    mr_template = load_mr_template(repo)

    if not is_claude_cli_installed():
        logger.error("Claude CLI not installed.")
        sys.exit(1)

    message = generate_commit_message_via_claude(
        diff,
        mr_template,
        repo,
        current_title,
        current_description,
        user_instructions,
    )
    if not message:
        logger.error("Failed to generate commit message via Claude.")
        sys.exit(1)

    title, body = parse_commit_message(message)

    print("\n--- Preview ---")
    print(f"Title: {title}\n")
    print(f"Description:\n{body}")
    print("--- End Preview ---\n")

    answer = input(f"Update MR !{mr.iid} with the above? [Y/n]: ").strip().lower()
    if answer not in ("", "y"):
        print("Aborted.")
        return

    update_mr(mr, title, body)
    logger.info("Updated MR !%s", mr.iid)


def cmd_implement(args: argparse.Namespace) -> None:
    """Implement a GitLab issue using Claude in agentic mode."""
    repo = Repo(os.getcwd())

    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)

    issue = fetch_issue(gl, repo, args.issue_number)
    labels = ", ".join(issue.labels) if issue.labels else "(none)"

    print(f"\nIssue #{issue.iid}: {issue.title}")
    print(f"URL: {issue.web_url}")
    print(f"Labels: {labels}")
    print()

    answer = input("Proceed with implementation? [Y/n]: ").strip().lower()
    if answer not in ("", "y"):
        print("Aborted.")
        return

    with tempfile.TemporaryDirectory(prefix=".loom_implement_", dir=repo.working_dir) as context_dir:
        with open(os.path.join(context_dir, "issue.md"), "w", encoding="utf-8") as f:
            f.write(f"# {issue.title}\n\n{issue.description or ''}")
        prompt = build_implement_prompt(issue, context_dir)
        run_claude_agentic(prompt, repo)


def cmd_mr_fix(_args: argparse.Namespace) -> None:
    """Address unresolved MR review comments using Claude in agentic mode."""
    repo = Repo(os.getcwd())
    branch = repo.active_branch.name
    logger.info("Current branch: %s", branch)

    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)

    mr = find_open_mr_for_branch(gl, branch, repo)
    if not mr:
        logger.error("No open MR found for branch: %s", branch)
        sys.exit(1)

    logger.info("Found MR !%s: %s", mr.iid, mr.title)

    discussions = fetch_unresolved_discussions(mr)
    if not discussions:
        logger.info("No unresolved review threads found. Nothing to do.")
        return

    print(f"\nFound {len(discussions)} unresolved thread(s) in MR !{mr.iid}:\n")
    for discussion in discussions:
        notes = discussion.attributes.get("notes", [])
        if not notes:
            continue
        first_note = notes[0]
        author = first_note.get("author", {}).get("username", "unknown")
        body = first_note.get("body", "")
        position = first_note.get("position") or {}
        new_path = position.get("new_path", "(general comment)")
        print(f"  @{author} on {new_path}: {body[:80]}")
    print()

    answer = input("Proceed with fixing? [Y/n]: ").strip().lower()
    if answer not in ("", "y"):
        print("Aborted.")
        return

    with tempfile.TemporaryDirectory(prefix=".loom_mrfix_", dir=repo.working_dir) as context_dir:
        with open(os.path.join(context_dir, "review_comments.txt"), "w", encoding="utf-8") as f:
            f.write(format_discussions_for_prompt(discussions))
        with open(os.path.join(context_dir, "branch.diff"), "w", encoding="utf-8") as f:
            f.write(get_branch_diff(repo))
        prompt = build_mr_fix_prompt(mr, context_dir)
        run_claude_agentic(prompt, repo)


def cmd_completions(_args: argparse.Namespace) -> None:
    """Print bash completion script for aitools.

    Source with: source <(aitools completions)
    Or add to your bashrc: aitools completions > ~/.bash_completion.d/aitools
    """
    parser = build_parser()
    subparsers_action = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    subcommands = " ".join(subparsers_action.choices.keys())
    print(f'complete -W "{subcommands}" aitools')


def cmd_diagnose(args: argparse.Namespace) -> None:
    """Diagnose a CI/CD job failure using Claude in agentic mode."""
    repo = Repo(os.getcwd())

    try:
        project_path, job_id = parse_job_url_or_id(args.job)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    gl = get_gitlab_client()
    if not gl:
        logger.error("Could not create GitLab client.")
        sys.exit(1)

    if project_path is None:
        project_path = CI_PROJECT_ID or get_project_id_from_remote(repo)
    if not project_path:
        logger.error(
            "Could not determine project. Provide a full job URL or set CI_PROJECT_ID."
        )
        sys.exit(1)

    logger.info("Using project: %s", project_path)
    project = gl.projects.get(project_path)
    job = project.jobs.get(job_id)

    print(f"\nJob #{job.id}: {job.name}")
    print(f"Stage: {job.stage} | Status: {job.status}")
    print(f"URL: {job.web_url}\n")

    logger.info("Fetching job log...")
    log = fetch_job_log(job)
    logger.info("Job log: %d characters", len(log))

    with tempfile.TemporaryDirectory(prefix=".loom_diagnose_", dir=repo.working_dir) as context_dir:
        with open(os.path.join(context_dir, "job_log.txt"), "w", encoding="utf-8") as f:
            f.write(log)

        logger.info("Fetching job artifacts...")
        artifacts_dir = os.path.join(context_dir, "artifacts")
        os.makedirs(artifacts_dir)
        if extract_job_artifacts(job, artifacts_dir):
            logger.info("Artifacts extracted to %s", artifacts_dir)
        else:
            logger.info("No artifacts found")

        prompt = build_diagnose_prompt(job, context_dir)
        run_claude_agentic(prompt, repo)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Loom AI developer tools.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    # mr-update subcommand
    mr_update_parser = subparsers.add_parser(
        "mr-update",
        help="Update GitLab MR title/description using AI",
    )
    mr_update_parser.add_argument(
        "instructions",
        nargs="*",
        help="Additional instructions to append to the AI prompt",
    )
    mr_update_parser.set_defaults(func=cmd_mr_update)

    # implement subcommand
    implement_parser = subparsers.add_parser(
        "implement",
        help="Implement a GitLab issue using Claude in agentic mode",
    )
    implement_parser.add_argument(
        "issue_number",
        type=int,
        help="GitLab issue number to implement",
    )
    implement_parser.set_defaults(func=cmd_implement)

    # mr-fix subcommand
    mr_fix_parser = subparsers.add_parser(
        "mr-fix",
        help="Address unresolved MR review comments using Claude in agentic mode",
    )
    mr_fix_parser.set_defaults(func=cmd_mr_fix)

    # completions subcommand
    completions_parser = subparsers.add_parser(
        "completions",
        help="Print bash completion script (source with: source <(aitools completions))",
    )
    completions_parser.set_defaults(func=cmd_completions)

    # diagnose subcommand
    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Diagnose a CI/CD job failure using Claude in agentic mode",
    )
    diagnose_parser.add_argument(
        "job",
        help="GitLab job URL (e.g. https://gitlab.com/group/project/-/jobs/123) or bare job ID",
    )
    diagnose_parser.set_defaults(func=cmd_diagnose)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
