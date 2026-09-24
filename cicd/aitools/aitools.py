import logging
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from git import Repo
from gitlab.v4.objects import ProjectIssueDiscussion, ProjectMergeRequestDiscussion

from . import config
from .config import AI_TIMEOUT, MAX_DIFF_CHARS
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


def run_prompt(prompt: str, repo: Repo) -> str | None:
    if not repo.working_dir:
        return None

    # Build cmd
    if config.BACKEND == "claude":
        cmd = [
            "claude",
            "--print",
            "--output-format",
            "text",
            "--no-session-persistence",
        ]
    else:
        cmd = [
            "opencode",
            "run",
        ]
        if config.MODEL != "none":
            cmd = cmd + ["--model", config.MODEL]

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=AI_TIMEOUT,
            cwd=repo.working_dir,
            check=False,
        )
        if result.returncode != 0:
            logger.warning("AI CLI returned non-zero exit code: %s", result.returncode)
            if result.stdout:
                logger.warning("AI CLI stdout: %s", result.stdout)
            if result.stderr:
                logger.warning("AI CLI stderr: %s", result.stderr)
            return None

        if config.BACKEND == "claude":
            message = result.stdout
        else:
            message = ""
            for line in result.stdout.splitlines(keepends=True):
                # Strip opencode specifics
                if not line.startswith("> build"):
                    message += line

        return message.strip()

    except (subprocess.TimeoutExpired, OSError):
        logger.warning("AI CLI timed out after %s seconds", AI_TIMEOUT)
        return None


def _summarize_diff_chunk_via_ai(chunk: DiffChunk, repo: Repo) -> str | None:
    prompt = build_diff_chunk_summary_prompt(chunk.files, chunk.diff)

    summary = run_prompt(prompt, repo)

    return summary if summary else None


def _build_chunked_summary(file_map: FileDiffMap, repo: Repo) -> str:
    chunks = _chunk_file_diffs(file_map)
    logger.info("Summarizing %d diff chunks in parallel", len(chunks))

    summaries: list[str | None] = [None] * len(chunks)

    def summarize_indexed(args: tuple[int, DiffChunk]) -> tuple[int, str | None]:
        idx, chunk = args
        return idx, _summarize_diff_chunk_via_ai(chunk, repo)

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


def is_ai_cli_installed() -> bool:
    """Check if the AI Code CLI is installed."""
    return shutil.which(config.BACKEND) is not None


def generate_commit_message_via_ai(
    diff: str,
    mr_template: str,
    repo: Repo,
    mr_context: MRContext = _DEFAULT_MR_CONTEXT,
    target_branch: str = "main",
) -> str | None:
    """Generate a commit message using the AI code CLI."""
    if _DIFF_TRUNCATED_MARKER in diff:
        logger.info("Diff was truncated — switching to chunked summarization mode")
        diff = _build_chunked_summary(
            get_per_file_diffs(repo, target_branch),
            repo,
        )

    prompt = build_mr_update_prompt(
        mr_template,
        mr_context.title,
        mr_context.description,
        include_diff=diff,
        user_instructions=mr_context.user_instructions,
    )

    logger.info("Sending diff to AI CLI for commit message suggestion...")
    message = run_prompt(prompt, repo)
    logger.debug("AI CLI response: %s", message)

    return message if message else None


def parse_commit_message(message: str) -> CommitMessage:
    """Split commit message into title (first line) and body (rest)."""
    lines = message.strip().split("\n", 1)
    title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    return CommitMessage(title=title, body=body)


def generate_discussion_reply(
    discussion: ProjectMergeRequestDiscussion, diff: str, repo: Repo
) -> str | None:
    """Generate a reply to a single review discussion using AI."""
    location = extract_discussion_location(discussion)
    thread = extract_discussion_thread(discussion)
    prompt = build_comment_reply_prompt(location, thread, diff)

    reply = run_prompt(prompt, repo)

    return reply if reply else None


def generate_issue_note_reply(
    discussion: ProjectIssueDiscussion,
    old_description: str,
    new_description: str,
    repo: Repo,
) -> str | None:
    """Generate a reply to a single issue comment thread using AI."""
    notes = discussion.attributes.get("notes", [])
    if not notes:
        return None
    first_note = notes[0]
    author = first_note.get("author", {}).get("username", "unknown")
    body = first_note.get("body", "")
    prompt = build_issue_note_reply_prompt(
        author, body, old_description, new_description
    )

    reply = run_prompt(prompt, repo)

    return reply if reply else None


def generate_release_notes_via_ai(
    tag_name: str,
    previous_tag: str | None,
    milestone_info: str,
    diff: str,
    repo: Repo,
) -> str | None:
    """Generate release notes using the AI Code CLI."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return None

    if _DIFF_TRUNCATED_MARKER in diff and previous_tag is not None:
        logger.info("Diff was truncated — switching to chunked summarization mode")
        diff = _build_chunked_summary(
            get_per_file_tag_diffs(repo, previous_tag, tag_name),
            repo,
        )

    prompt = build_release_notes_prompt(tag_name, previous_tag, milestone_info, diff)

    logger.info("Sending context to AI CLI for release notes generation...")

    message = run_prompt(prompt, repo)

    logger.debug("AI CLI response: %s", message)
    return message if message else None


def run_ai_agentic(prompt: str, repo: Repo) -> None:
    """Run AI CLI in agentic mode, handing over the terminal to the user."""
    if not repo.working_dir:
        logger.error("No working directory available (bare repo?)")
        sys.exit(1)

    if not is_ai_cli_installed():
        logger.error("AI CLI is not installed.")
        sys.exit(1)

    cmd = [config.BACKEND]
    if config.AUTO_MODE:
        if config.BACKEND == "claude":
            cmd += ["--dangerously-skip-permissions"]
        else:
            cmd += ["--auto"]
    if config.BACKEND == "opencode":
        cmd += ["--prompt"]

    cmd.append(prompt)

    subprocess.run(cmd, cwd=repo.working_dir, check=False)
