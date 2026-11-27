"""Running one autonomous strand per tmux window.

The session lives on a socket of its own rather than on the user's tmux server. A strand
needs GITLAB_TOKEN, and both `new-window -e VAR=value` and `set-environment` would put
that credential on a command line visible in `ps`; a server started from this process
inherits the environment wholesale instead. It also means `$TMUX` never matters — the
windows are only ever created detached, and nothing here attaches to one.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .models import StrandCommandSpec, StrandSession, StrandStatus, StrandWindow
from .worktree import state_dir

logger = logging.getLogger(__name__)

TMUX_TIMEOUT_S = 10
STRAND_POLL_INTERVAL_S = 10
WINDOW_PREFIX = "issue-"


def ensure_tmux_available() -> None:
    """Raise when tmux is missing, naming what needs installing."""
    if not shutil.which("tmux"):
        raise RuntimeError(
            "tmux is required to run implementation strands — install it, or run "
            "`aitools implement <issue>` one issue at a time"
        )


def _tmux(socket: str, *arguments: str) -> str | None:
    """Run one tmux command against our socket, returning its output."""
    try:
        result = subprocess.run(
            ["tmux", "-S", socket, *arguments],
            capture_output=True,
            text=True,
            timeout=TMUX_TIMEOUT_S,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("tmux %s failed: %s", " ".join(arguments), e)
        return None
    if result.returncode != 0:
        logger.debug(
            "tmux %s exited %s: %s",
            " ".join(arguments),
            result.returncode,
            result.stderr.strip(),
        )
        return None
    return result.stdout


def socket_path(milestone_iid: int) -> str:
    """The tmux socket this milestone's session lives on."""
    runtime = os.getenv("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return str(Path(runtime) / f"aitools-milestone-{milestone_iid}.sock")


def session_name(milestone_iid: int) -> str:
    """The tmux session name for a milestone's strands."""
    return f"milestone-{milestone_iid}"


def window_name(issue_iid: int) -> str:
    """The tmux window name for one issue's strand."""
    return f"{WINDOW_PREFIX}{issue_iid}"


def log_path(milestone_iid: int, issue_iid: int) -> Path:
    """Where a strand's console output is written."""
    directory = state_dir() / "aitools-logs" / f"milestone-{milestone_iid}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{window_name(issue_iid)}.log"


def session_exists(socket: str, session: str) -> bool:
    """Whether the session is already running on our socket."""
    return _tmux(socket, "has-session", "-t", session) is not None


def start_session(socket: str, session: str, cwd: str) -> None:
    """Start the detached session that holds this milestone's strands."""
    _tmux(socket, "new-session", "-d", "-s", session, "-c", cwd)
    # A finished window keeps its scrollback and reports how its command exited, which
    # is how a strand's outcome is read back.
    _tmux(socket, "set-option", "-t", session, "remain-on-exit", "on")


def strand_command(
    devenv_root: str, issue_iid: int, spec: StrandCommandSpec
) -> list[str]:
    """The command one strand window runs.

    It enters the devenv environment explicitly: the tmux server was started from this
    process but has no reason to carry a PATH that resolves the repository's own tools.
    """
    argv = ["direnv", "exec", devenv_root, sys.executable, "-m", "cicd.aitools"]
    argv += ["--backend", spec.backend]
    if spec.model != "none":
        argv += ["--model", spec.model]
    argv += ["implement", str(issue_iid)]
    argv += ["--max-fix-rounds", str(spec.max_fix_rounds)]
    argv += ["--timeout-minutes", str(spec.timeout_minutes)]
    if not spec.review:
        argv.append("--no-review")
    return argv


def start_strand(
    session: StrandSession,
    issue_iid: int,
    command: list[str],
    strand_log: Path,
) -> StrandWindow:
    """Open a window running one issue's strand, logging what it prints."""
    name = window_name(issue_iid)
    target = f"{session.name}:{name}"
    _tmux(session.socket, "new-window", "-d", "-n", name, "-c", session.cwd, *command)
    # tmux otherwise renames a window after the process running in it, and the target
    # above stops resolving.
    _tmux(session.socket, "set-option", "-w", "-t", target, "automatic-rename", "off")
    _tmux(session.socket, "set-option", "-w", "-t", target, "remain-on-exit", "on")
    _tmux(session.socket, "pipe-pane", "-o", "-t", target, f"cat >> {strand_log}")
    return StrandWindow(issue_iid=issue_iid, window_name=name)


def parse_strand_statuses(listing: str) -> list[StrandStatus]:
    """Decode `list-panes -F '#{window_name} #{pane_dead} #{pane_dead_status}'`."""
    statuses: list[StrandStatus] = []
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) < 2 or not fields[0].startswith(WINDOW_PREFIX):
            continue
        name = fields[0]
        try:
            issue_iid = int(name[len(WINDOW_PREFIX) :])
        except ValueError:
            continue
        dead = fields[1] == "1"
        exit_code: int | None = None
        if len(fields) > 2 and fields[2]:
            try:
                exit_code = int(fields[2])
            except ValueError:
                exit_code = None
        statuses.append(
            StrandStatus(
                issue_iid=issue_iid,
                window_name=name,
                dead=dead,
                exit_code=exit_code,
            )
        )
    return statuses


def list_strands(socket: str, session: str) -> list[StrandStatus]:
    """The live state of every strand window in the session."""
    listing = _tmux(
        socket,
        "list-panes",
        "-s",
        "-t",
        session,
        "-F",
        "#{window_name} #{pane_dead} #{pane_dead_status}",
    )
    return parse_strand_statuses(listing) if listing else []


def kill_session(socket: str, session: str) -> None:
    """Tear the session down, discarding every window's scrollback with it."""
    _tmux(socket, "kill-session", "-t", session)
