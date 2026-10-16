"""Running the tools this package is made of.

Two runners, and the difference between them is the only thing a caller has to decide:

  * `run_checked` is for a command whose failure is the caller's problem. It raises
    `subprocess.CalledProcessError` or `OSError`, exactly as
    `subprocess.run(check=True)` does, and returns stdout.
  * `run_tolerant` never raises. It answers a `CommandOutcome` carrying the exit status
    and whatever the tool said, which is what every best-effort path here wants: a
    `blockdev` that refused, a `wall` on a box with no terminals, a tmux server that is
    not running.

One module rather than one per caller. There used to be five -- `devices._run`,
`transfer._run`, `mounts.run_command`, `pane._tmux` and an inline loop in `report` --
two of which had the same name in the same package and differed only in whether `env`
and `timeout` were parameters. That is how a call gets moved between modules and
silently loses its timeout.

`mounts.Runner` stays an injected `Callable`, because mounting a stranger's filesystem
is the one thing in this package whose failure paths are worth exercising without a
stick in the box.
"""

import logging
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Nothing here is interactive, and nothing may hang a root unit holding the ingest
# lock. The mirror is the deliberate exception and does not come through here.
DEFAULT_TIMEOUT_S = 300


@dataclass(frozen=True)
class CommandOutcome:
    """How one command went.

    A command that could not be run at all is a failure too. `stderr` carries the reason
    either way -- what the tool printed, or what Python said about not being able to
    start it -- because both end up in front of the operator as the reason a volume was
    skipped.
    """

    returncode: int
    stderr: str = ""
    stdout: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


# How `mounts` reaches `mount`, `blockdev` and `umount`: positional timeout, because
# every call site passes one of three different deadlines deliberately.
Runner = Callable[[list[str], int], CommandOutcome]


def run_checked(
    argv: list[str],
    env: Mapping[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> str:
    """Standard output of a command that has to work, or raise."""
    return subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=dict(env) if env is not None else None,
    ).stdout


def run_tolerant(
    argv: list[str],
    timeout: int = DEFAULT_TIMEOUT_S,
    env: Mapping[str, str] | None = None,
) -> CommandOutcome:
    """Run a command and report how it went, never raising."""
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(env) if env is not None else None,
        )
    except (subprocess.SubprocessError, OSError) as error:
        # 127 is the shell's "could not execute", which is what this is.
        logger.debug("%s: %s", argv[0], error)
        return CommandOutcome(127, str(error))
    return CommandOutcome(
        completed.returncode, completed.stderr or "", completed.stdout or ""
    )
