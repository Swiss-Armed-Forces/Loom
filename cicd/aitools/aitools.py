import json
import logging
import shutil
import subprocess
import threading
import time
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import IO, TextIO

from git import Repo
from gitlab.v4.objects import ProjectIssueDiscussion, ProjectMergeRequestDiscussion

from . import config
from .config import AI_TIMEOUT, MAX_DIFF_CHARS
from .git_helpers import get_per_file_diffs, get_per_file_tag_diffs
from .gitlab_api import extract_discussion_location, extract_discussion_thread
from .models import (
    AgentCommand,
    AgentEvent,
    AgentExecution,
    AgentOutcome,
    AgentRun,
    BranchWorktree,
    CommitMessage,
    DiffChunk,
    FileDiffMap,
    MRContext,
)
from .prompts import (
    build_comment_reply_prompt,
    build_diff_chunk_summary_prompt,
    build_issue_note_reply_prompt,
    build_mr_update_prompt,
    build_release_notes_prompt,
)
from .worktree import ensure_environment, state_dir

logger = logging.getLogger(__name__)

_DEFAULT_MR_CONTEXT = MRContext()
_DIFF_TRUNCATED_MARKER = "[Diff truncated at"
_SUMMARY_WIDTH = 80
_WATCHDOG_POLL_S = 15

# Invoking an aitools subcommand is the authorisation for the edits and commands its
# prompt describes, so Claude approves them itself rather than asking per operation.
# Auto mode keeps the checks on dangerous operations that "bypassPermissions" drops.
CLAUDE_PERMISSION_MODE = "auto"


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
            "--permission-mode",
            CLAUDE_PERMISSION_MODE,
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


def build_agent_command(backend: str, model: str, prompt: str) -> AgentCommand:
    """Build the argv and stdin of one headless agentic run.

    claude takes the prompt on stdin, which has no ARG_MAX ceiling and needs no quoting;
    the review prompt alone is tens of kilobytes. Under --print its stream-json output
    format additionally requires --verbose, and refuses to start without it.
    """
    if backend == "claude":
        return AgentCommand(
            argv=[
                "claude",
                "--print",
                "--output-format",
                "stream-json",
                "--verbose",
                "--no-session-persistence",
                "--permission-mode",
                CLAUDE_PERMISSION_MODE,
            ],
            stdin_text=prompt,
        )

    argv = ["opencode", "run", "--format", "json"]
    if model != "none":
        argv += ["--model", model]
    # A headless process cannot answer a permission prompt, so auto-accept is not
    # optional here the way it is for an opencode session a user is sitting in front of.
    argv += ["--auto", "--", prompt]
    return AgentCommand(argv=argv, stdin_text="")


def _summarize_assistant_event(payload: dict) -> str:
    """One line describing what the assistant did on this event."""
    content = payload.get("message", {}).get("content", [])
    if not isinstance(content, list):
        return ""
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = str(block.get("text", "")).strip()
            if text:
                return text.splitlines()[0][:_SUMMARY_WIDTH]
        if block.get("type") == "tool_use":
            name = block.get("name", "tool")
            arguments = block.get("input", {})
            detail = ""
            if isinstance(arguments, dict):
                detail = str(
                    arguments.get("command")
                    or arguments.get("file_path")
                    or arguments.get("pattern")
                    or ""
                )
            return f"{name}({detail[:_SUMMARY_WIDTH]})"
    return ""


def parse_stream_event(line: str) -> AgentEvent:
    """Decode one line of a backend's streaming output.

    Every field is read defensively: a line that is not JSON, or JSON of a shape this
    does not know, is reported as "other" and never ends the run. The stream schema is
    the backend's, and it changes between releases.
    """
    try:
        payload = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return AgentEvent(kind="other", summary="", is_error=False, turns=0)
    if not isinstance(payload, dict):
        return AgentEvent(kind="other", summary="", is_error=False, turns=0)

    kind = str(payload.get("type", "other"))
    if kind == "system":
        model = payload.get("model", "")
        return AgentEvent(
            kind=kind,
            summary=f"session started{f' ({model})' if model else ''}",
            is_error=False,
            turns=0,
        )
    if kind == "assistant":
        return AgentEvent(
            kind=kind,
            summary=_summarize_assistant_event(payload),
            is_error=False,
            turns=0,
        )
    if kind == "result":
        turns = payload.get("num_turns", 0)
        return AgentEvent(
            kind=kind,
            summary=str(payload.get("subtype", "")),
            is_error=bool(payload.get("is_error", False)),
            turns=turns if isinstance(turns, int) else 0,
        )
    return AgentEvent(kind="other", summary="", is_error=False, turns=0)


def consume_stream(lines: Iterable[str], transcript: TextIO) -> AgentOutcome:
    """Write every line to the transcript and report what the stream said."""
    reported_error = False
    turns = 0
    last_text = ""
    for line in lines:
        transcript.write(line if line.endswith("\n") else f"{line}\n")
        event = parse_stream_event(line.strip())
        if event.kind == "result":
            reported_error = event.is_error
            turns = event.turns
        if event.summary:
            last_text = event.summary
            logger.info("  %s", event.summary)
    return AgentOutcome(reported_error=reported_error, turns=turns, last_text=last_text)


def _transcript_path(branch: str, label: str, started: datetime) -> Path:
    directory = state_dir() / "aitools" / branch.replace("/", "-")
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{label}-{started.strftime('%Y%m%d-%H%M%S')}.jsonl"


def _kill_when_stalled(
    process: subprocess.Popen, deadline: float, last_event: list[float]
) -> str:
    """Kill the agent when it stops producing events, or outruns its total budget.

    Returns the reason it was killed, or "" when it finished on its own.
    """
    while process.poll() is None:
        time.sleep(_WATCHDOG_POLL_S)
        now = time.monotonic()
        if now > deadline:
            reason = f"exceeded the total budget of {config.AI_AGENT_TIMEOUT}s"
        elif now - last_event[0] > config.AI_AGENT_IDLE_TIMEOUT:
            reason = f"produced no output for {config.AI_AGENT_IDLE_TIMEOUT}s"
        else:
            continue
        process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Agent process did not exit after being killed")
        return reason
    return ""


def _execute_agent(
    argv: list[str],
    command: AgentCommand,
    cwd: str,
    start: float,
    transcript: TextIO,
) -> AgentExecution:
    """Run the backend, stream its output to the transcript and watch for a hang."""
    killed_reasons: list[str] = []
    last_event = [time.monotonic()]
    deadline = start + config.AI_AGENT_TIMEOUT
    outcome = AgentOutcome(reported_error=False, turns=0, last_text="")

    # stderr is inherited rather than captured: a second captured pipe needs a reader
    # thread of its own or it deadlocks once full, and merging it into stdout would
    # corrupt the transcript.
    with subprocess.Popen(
        argv,
        cwd=cwd,
        stdin=subprocess.PIPE if command.stdin_text else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as process:
        if command.stdin_text and process.stdin:
            process.stdin.write(command.stdin_text)
            process.stdin.close()

        def watch() -> None:
            killed_reasons.append(_kill_when_stalled(process, deadline, last_event))

        watchdog = threading.Thread(target=watch, daemon=True)
        watchdog.start()

        def touched(stream: IO[str]) -> Iterator[str]:
            for line in stream:
                last_event[0] = time.monotonic()
                yield line

        if process.stdout:
            outcome = consume_stream(touched(process.stdout), transcript)
        exit_code = process.wait()
        watchdog.join(timeout=_WATCHDOG_POLL_S * 2)

    return AgentExecution(
        exit_code=exit_code,
        killed=killed_reasons[0] if killed_reasons else "",
        outcome=outcome,
    )


def run_agent(prompt: str, worktree: BranchWorktree, label: str) -> AgentRun:
    """Run the AI backend headlessly in a worktree and report how it went.

    Whether the agent actually did any work is a question for git, not for this result:
    an agent can exit 0 having changed nothing, and can exit non-zero after a good
    commit. The result says whether the run itself completed, and where to read it.
    """
    started_at = datetime.now()
    transcript_path = _transcript_path(worktree.branch, label, started_at)
    start = time.monotonic()

    if not is_ai_cli_installed():
        return AgentRun(
            ok=False,
            exit_code=-1,
            duration_s=0.0,
            turns=0,
            transcript_path=str(transcript_path),
            error=f"{config.BACKEND} is not installed",
        )

    environment = ensure_environment(worktree)
    if not environment.ready:
        return AgentRun(
            ok=False,
            exit_code=-1,
            duration_s=0.0,
            turns=0,
            transcript_path=str(transcript_path),
            error=f"devenv environment unavailable: {environment.reason}",
        )

    command = build_agent_command(config.BACKEND, config.MODEL, prompt)
    argv = environment.prefix + command.argv
    logger.info("Running %s agent (%s) in %s", config.BACKEND, label, worktree.path)

    with open(transcript_path, "w", encoding="utf-8") as transcript:
        execution = _execute_agent(argv, command, worktree.path, start, transcript)

    duration = time.monotonic() - start
    if execution.killed:
        error = f"agent killed: {execution.killed}"
    elif execution.exit_code != 0:
        error = f"{config.BACKEND} exited {execution.exit_code}"
    elif execution.outcome.reported_error:
        error = f"{config.BACKEND} reported an error: {execution.outcome.last_text}"
    else:
        error = ""

    if error:
        logger.warning("%s — transcript: %s", error, transcript_path)

    return AgentRun(
        ok=not error,
        exit_code=-1 if execution.killed else execution.exit_code,
        duration_s=duration,
        turns=execution.outcome.turns,
        transcript_path=str(transcript_path),
        error=error,
    )
