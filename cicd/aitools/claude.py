import logging
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from git import Repo
from gitlab.v4.objects import ProjectIssueDiscussion, ProjectMergeRequestDiscussion

from . import config
from .config import CLAUDE_TIMEOUT, MAX_DIFF_CHARS
from .git_helpers import get_per_file_diffs, get_per_file_tag_diffs
from .gitlab_api import extract_discussion_location, extract_discussion_thread
from .models import CommitMessage, DiffChunk, FileDiffMap, MRContext
from .prompts import (
    build_comment_reply_prompt,
    build_diff_chunk_summary_prompt,
    build_issue_note_reply_prompt,
    build_mr_update_prompt,
    build_release_notes_prompt,
)

logger = logging.getLogger(__name__)

_DEFAULT_MR_CONTEXT = MRContext()
_DIFF_TRUNCATED_MARKER = "[Diff truncated at"


def _chunk_file_diffs(file_map: FileDiffMap) -> list[DiffChunk]:
    chunks: list[DiffChunk] = []
    current_files: list[str] = []
    current_diff = ""

    for file_path, file_diff in file_map.files.items():
        if len(file_diff) > MAX_DIFF_CHARS:
            # Oversized single file: flush current chunk, then add this file alone (truncated)
            if current_files:
                chunks.append(DiffChunk(files=current_files, diff=current_diff))
                current_files = []
                current_diff = ""
            truncated = file_diff[:MAX_DIFF_CHARS]
            chunks.append(DiffChunk(files=[file_path], diff=truncated))
        elif current_diff and len(current_diff) + len(file_diff) > MAX_DIFF_CHARS:
            # Adding this file would exceed limit: flush and start new chunk
            chunks.append(DiffChunk(files=current_files, diff=current_diff))
            current_files = [file_path]
            current_diff = file_diff
        else:
            current_files.append(file_path)
            current_diff += file_diff

    if current_files:
        chunks.append(DiffChunk(files=current_files, diff=current_diff))

    return chunks


def _summarize_diff_chunk_via_claude(chunk: DiffChunk, repo: Repo) -> str | None:
    if not repo.working_dir:
        return None
    prompt = build_diff_chunk_summary_prompt(chunk.files, chunk.diff)
    try:
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
                "Claude CLI returned non-zero for chunk summary: %s", result.returncode
            )
            return None
        summary = result.stdout.strip()
        return summary if summary else None
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("Failed to summarize diff chunk: %s", e)
        return None


def _build_chunked_summary(file_map: FileDiffMap, repo: Repo) -> str:
    chunks = _chunk_file_diffs(file_map)
    logger.info("Summarizing %d diff chunks in parallel", len(chunks))

    summaries: list[str | None] = [None] * len(chunks)

    def summarize_indexed(args: tuple[int, DiffChunk]) -> tuple[int, str | None]:
        idx, chunk = args
        return idx, _summarize_diff_chunk_via_claude(chunk, repo)

    with ThreadPoolExecutor() as executor:
        for idx, summary in executor.map(summarize_indexed, enumerate(chunks)):
            summaries[idx] = summary

    parts = [f"Changed files:\n{file_map.stat}"]
    parts.append(
        f"\nChange summaries ({len(chunks)} chunks, diff too large for direct inclusion):\n"
    )

    for chunk, summary in zip(chunks, summaries):
        files_label = ", ".join(chunk.files)
        parts.append(f"### Files: {files_label}")
        if summary:
            parts.append(summary)
        else:
            logger.warning(
                "Chunk summary failed for %s — including raw truncated diff",
                files_label,
            )
            parts.append(chunk.diff[:MAX_DIFF_CHARS])
        parts.append("")

    return "\n".join(parts)


def is_claude_cli_installed() -> bool:
    """Check if the Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def generate_commit_message_via_claude(
    diff: str,
    mr_template: str,
    repo: Repo,
    mr_context: MRContext = _DEFAULT_MR_CONTEXT,
) -> str | None:
    """Generate a commit message using the Claude Code CLI."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return None

    if _DIFF_TRUNCATED_MARKER in diff:
        logger.info("Diff was truncated — switching to chunked summarization mode")
        diff = _build_chunked_summary(get_per_file_diffs(repo), repo)

    prompt = build_mr_update_prompt(
        mr_template,
        mr_context.title,
        mr_context.description,
        include_diff=diff,
        user_instructions=mr_context.user_instructions,
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


def parse_commit_message(message: str) -> CommitMessage:
    """Split commit message into title (first line) and body (rest)."""
    lines = message.strip().split("\n", 1)
    title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    return CommitMessage(title=title, body=body)


def generate_discussion_reply(
    discussion: ProjectMergeRequestDiscussion, diff: str, repo: Repo
) -> str | None:
    """Generate a reply to a single review discussion using Claude."""
    if not repo.working_dir:
        return None

    location = extract_discussion_location(discussion)
    thread = extract_discussion_thread(discussion)
    prompt = build_comment_reply_prompt(location, thread, diff)

    try:
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
                "Claude CLI returned non-zero for reply generation: %s",
                result.returncode,
            )
            return None
        reply = result.stdout.strip()
        return reply if reply else None
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("Failed to generate reply for %s: %s", location, e)
        return None


def generate_issue_note_reply(
    discussion: ProjectIssueDiscussion,
    old_description: str,
    new_description: str,
    repo: Repo,
) -> str | None:
    """Generate a reply to a single issue comment thread using Claude."""
    if not repo.working_dir:
        return None

    notes = discussion.attributes.get("notes", [])
    if not notes:
        return None
    first_note = notes[0]
    author = first_note.get("author", {}).get("username", "unknown")
    body = first_note.get("body", "")
    prompt = build_issue_note_reply_prompt(
        author, body, old_description, new_description
    )

    try:
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
                "Claude CLI returned non-zero for issue reply generation: %s",
                result.returncode,
            )
            return None
        reply = result.stdout.strip()
        return reply if reply else None
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning(
            "Failed to generate reply for discussion %s: %s", discussion.id, e
        )
        return None


def generate_release_notes_via_claude(
    tag_name: str,
    previous_tag: str | None,
    milestone_info: str,
    diff: str,
    repo: Repo,
) -> str | None:
    """Generate release notes using the Claude Code CLI."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return None

    if _DIFF_TRUNCATED_MARKER in diff and previous_tag is not None:
        logger.info("Diff was truncated — switching to chunked summarization mode")
        diff = _build_chunked_summary(
            get_per_file_tag_diffs(repo, previous_tag, tag_name), repo
        )

    prompt = build_release_notes_prompt(tag_name, previous_tag, milestone_info, diff)

    try:
        logger.info("Sending context to Claude CLI for release notes generation...")
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


def run_claude_agentic(prompt: str, repo: Repo) -> None:
    """Run Claude CLI in agentic mode, handing over the terminal to the user."""
    if not repo.working_dir:
        logger.error("No working directory available (bare repo?)")
        sys.exit(1)

    if not is_claude_cli_installed():
        logger.error("Claude CLI is not installed.")
        sys.exit(1)

    cmd = ["claude"]
    if config.AUTO_MODE:
        cmd += ["--dangerously-skip-permissions"]
    cmd.append(prompt)

    subprocess.run(cmd, cwd=repo.working_dir, check=False)
