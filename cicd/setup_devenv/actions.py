"""The effects `cicd/setup-devenv` can have on a machine, and what they need to run.

A setup step decides *what* should happen; an `Action` is *how*, and -- just as
importantly -- how it reads out loud. The script's promise is that the operator sees
the real thing before consenting to it, so every action can `describe()` itself, and
the driver prints that and waits for a yes before calling `perform()`.

Modelling effects as values rather than as argv lists is what keeps shell out of the
script. Writing a file, appending a line to a dotfile, creating a directory with a
mode and registering a key with GitLab are not commands, and expressing them as
generated `bash -c` strings costs both the quoting and the operator's ability to read
what they are agreeing to.

An action reports what it changed by returning an `Outcome` rather than reaching into
a shared mutable context, so the only state that moves during a run is one `Session`
owned by the driver.

No secret is ever a field of an action. A token lives in `devenv.local.nix` and is
read at the moment it is needed, so it cannot reach a `repr()`, a log line or an
argument vector.

Python 3.9 is the floor here; see the note in the package docstring.
"""

from __future__ import annotations

import getpass
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, FrozenSet, Optional, Protocol, Sequence, Tuple

from git_cleanup_common import CommandResult, run_command
from setup_devenv.gitlab import GitLabClient, GitLabError

# The exit code a shell reports for a command it cannot find.
NOT_FOUND = 127

TOKEN_BINDING = re.compile(r'GITLAB_TOKEN\s*=\s*"([^"]*)"')


#
# Talking to the operator
#


def supports_colour() -> bool:
    """Whether escape sequences will reach a terminal rather than a log file."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def paint(text: str, code: str) -> str:
    """Wrap `text` in an SGR code, or return it unchanged off a terminal."""
    if not supports_colour():
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    """`text`, emphasised."""
    return paint(text, "1")


def red(text: str) -> str:
    """`text`, as a problem."""
    return paint(text, "1;31")


class Console(Protocol):
    """Where a step's output goes, and where its answers come from."""

    def say(self, line: str, /) -> None:
        """Print one line to the operator."""

    def ask_secret(self, question: str, /) -> Optional[str]:
        """The value typed in reply, or None when there is no terminal to ask."""


class TerminalConsole:
    """The real terminal."""

    def say(self, line: str, /) -> None:
        """Print one line to the operator."""
        print(line)

    def ask_secret(self, question: str, /) -> Optional[str]:
        """Read a secret without echoing it, or None with no terminal.

        Returning None rather than raising is what makes `--yes` on a closed stdin a
        step that declines to run, instead of an EOFError traceback.
        """
        if not sys.stdin.isatty():
            return None
        return getpass.getpass(question).strip() or None


#
# Running things and writing files
#


class Runner:
    """Executes commands and writes files.

    A seam, not an abstraction for its own sake: the tests hand the actions a fake one
    and assert on what *would* have happened, so none of the logic needs a machine to
    exercise it.
    """

    def run(
        self,
        argv: Sequence[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
    ) -> CommandResult:
        """Run a command, capturing output and never raising on failure."""
        merged = {**os.environ, **env} if env is not None else None
        return run_command(argv, cwd=cwd, env=merged)

    def run_visible(self, argv: Sequence[str], cwd: Optional[Path] = None) -> int:
        """Run a command with its output going straight to the terminal.

        Answers 127, as a shell would, for a command that is not on PATH -- the ordinary
        case on a machine that has not been set up yet.
        """
        cmd = list(argv)
        if not shutil.which(cmd[0]):
            return NOT_FOUND
        try:
            completed = subprocess.run(
                cmd, cwd=str(cwd) if cwd is not None else None, check=False
            )
        except OSError:
            return NOT_FOUND
        return completed.returncode

    def write_file(self, path: Path, content: str, mode: int = 0o644) -> bool:
        """Create or replace a file this account owns, at exactly `mode`.

        Opened with the mode rather than chmod'ed afterwards, so a secret is never
        briefly readable at the ambient umask.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.chmod(path, mode)
        except OSError:
            return False
        return True

    def write_root_file(self, path: Path, content: str, mode: int = 0o644) -> bool:
        """Replace a root-owned file, via a temporary file and `sudo install`.

        `sudo tee` would take the content on stdin, which hides it from the operator;
        this way the command shown is the command that runs.

        A symlinked destination is resolved first: installing over the link itself
        would replace it with a regular file, silently detaching a configuration that
        a dotfile manager owns.
        """
        destination = path.resolve() if path.is_symlink() else path
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(content)
            staged = Path(handle.name)
        try:
            return (
                self.run_visible(
                    [
                        "sudo",
                        "install",
                        "--mode",
                        f"{mode:04o}",
                        "--owner",
                        "root",
                        "--group",
                        "root",
                        str(staged),
                        str(destination),
                    ]
                )
                == 0
            )
        finally:
            staged.unlink(missing_ok=True)


#
# What a step may reach for
#


@dataclass(frozen=True)
class Machine:
    """What this computer is, as far as setting it up is concerned.

    Read once at startup and never again, so a step cannot reach for a fact the tests
    have no way to state -- `tools` included, which is why no assessment calls
    `shutil.which` directly.
    """

    is_nixos: bool
    has_systemd: bool
    home: Path
    user: str
    shell: str
    tools: FrozenSet[str] = frozenset()

    def has(self, tool: str) -> bool:
        """Whether `tool` was on PATH when the run started."""
        return tool in self.tools


GitLabFactory = Callable[[str], GitLabClient]


@dataclass(frozen=True)
class Context:
    """Everything an action is allowed to reach for."""

    repo: Path
    machine: Machine
    runner: Runner = field(default_factory=Runner)
    console: Console = field(default_factory=TerminalConsole)
    # A factory rather than a client, because the token is what the `gitlab-token`
    # step is for: until it has run there is nothing to build a client from.
    make_gitlab: GitLabFactory = GitLabClient

    @property
    def devenv_local(self) -> Path:
        """The gitignored Nix file holding this checkout's GITLAB_TOKEN."""
        return self.repo / "devenv.local.nix"

    def stored_token(self) -> Optional[str]:
        """The GitLab token recorded for this checkout, if there is one."""
        return token_in(read_text(self.devenv_local))


@dataclass(frozen=True)
class Outcome:
    """What an action did."""

    ok: bool
    nix_conf_changed: bool = False
    nix_now_on_path: bool = False


DONE = Outcome(ok=True)
FAILED = Outcome(ok=False)


@dataclass(frozen=True)
class Session:
    """The run: the options it was given, and what earlier steps changed.

    Frozen and replaced rather than mutated, so "what has happened so far" is a value
    the driver threads through the steps instead of a flag anything can set.
    """

    dry_run: bool = False
    assume_yes: bool = False
    skip_gitlab_token: bool = False
    nix_conf_changed: bool = False
    nix_on_path: bool = False


def fold(session: Session, outcome: Outcome) -> Session:
    """`session` updated with whatever `outcome` reports having changed."""
    return replace(
        session,
        nix_conf_changed=session.nix_conf_changed or outcome.nix_conf_changed,
        nix_on_path=session.nix_on_path or outcome.nix_now_on_path,
    )


class Action(Protocol):
    """One effect on the machine, able to say what it is before it happens."""

    def describe(self, /) -> str:
        """What the operator is shown before consenting.

        May be several lines.
        """
        raise NotImplementedError

    def perform(self, ctx: Context, /) -> Outcome:
        """Carry it out, reporting what changed."""
        raise NotImplementedError


#
# The effects themselves
#


@dataclass(frozen=True)
class Run:
    """A command, with its output going to the terminal."""

    argv: Tuple[str, ...]
    cwd: Optional[Path] = None

    def __post_init__(self) -> None:
        """Normalise argv to a tuple, so equality and hashing behave."""
        object.__setattr__(self, "argv", tuple(self.argv))

    def describe(self, /) -> str:
        """The command, quoted the way it would have to be typed."""
        return shlex.join(self.argv)

    def perform(self, ctx: Context, /) -> Outcome:
        """Run it, in the repository unless told otherwise."""
        cwd = self.cwd if self.cwd is not None else ctx.repo
        return Outcome(ok=ctx.runner.run_visible(self.argv, cwd=cwd) == 0)


@dataclass(frozen=True)
class WriteFile:
    """A file's entire contents, at a given mode."""

    path: Path
    content: str
    mode: int = 0o644
    sudo: bool = False
    # Whether writing this is what the nix daemon has to be restarted for.
    is_nix_conf: bool = False

    def describe(self, /) -> str:
        """The destination and mode, and how the privilege is obtained."""
        how = " (via sudo)" if self.sudo else ""
        return f"write {self.path}, mode {self.mode:04o}{how}"

    def perform(self, ctx: Context, /) -> Outcome:
        """Write it, reporting whether the nix configuration moved."""
        write = ctx.runner.write_root_file if self.sudo else ctx.runner.write_file
        written = write(self.path, self.content, self.mode)
        if not written:
            ctx.console.say(red(f"  could not write {self.path}"))
        return Outcome(ok=written, nix_conf_changed=written and self.is_nix_conf)


@dataclass(frozen=True)
class AppendLine:
    """One line added to the end of a file, if it is not already there.

    Appending to somebody's shell profile is the one effect here that re-running cannot
    undo, so it is shown in full and re-checked at the moment it happens: the file may
    have gained the line between the assessment and the consent.
    """

    path: Path
    line: str

    def describe(self, /) -> str:
        """The file and the exact line."""
        return f"append to {self.path}:\n    {self.line}"

    def perform(self, ctx: Context, /) -> Outcome:
        """Append it, unless the file already carries it."""
        existing = read_text(self.path)
        if self.line in existing:
            return DONE
        separator = "" if not existing or existing.endswith("\n") else "\n"
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(f"{separator}{self.line}\n")
        except OSError as error:
            ctx.console.say(red(f"  could not write {self.path}: {error}"))
            return FAILED
        return DONE


@dataclass(frozen=True)
class MakeDirectory:
    """A directory, created with exactly the mode given."""

    path: Path
    mode: int = 0o755

    def describe(self, /) -> str:
        """The directory and its mode."""
        return f"create {self.path}/, mode {self.mode:04o}"

    def perform(self, ctx: Context, /) -> Outcome:
        """Create it, and correct the mode if it was already there."""
        try:
            self.path.mkdir(parents=True, mode=self.mode, exist_ok=True)
            os.chmod(self.path, self.mode)
        except OSError as error:
            ctx.console.say(red(f"  could not create {self.path}: {error}"))
            return FAILED
        return DONE


@dataclass(frozen=True)
class StoreGitLabToken:
    """Ask for a GitLab token, check it, and record it in `devenv.local.nix`.

    The one action that cannot show its contents in advance, because those contents
    are a secret the operator has not typed yet. Everything else about it is stated
    up front: where it goes, at what mode, and what is done with it first.
    """

    path: Path

    def describe(self, /) -> str:
        """What will be asked, what will be checked, and what will be written."""
        return (
            "prompt for a GitLab personal access token (`api` scope), not echoed,\n"
            "    check it against gitlab.com, and on success write\n"
            f"    {self.path}, mode 0600, holding exactly:\n"
            '        { ... }: { env.GITLAB_TOKEN = "<the token you type>"; }\n'
            "    The token is never printed and never passed as a command argument."
        )

    def perform(self, ctx: Context, /) -> Outcome:
        """Prompt, validate, then write."""
        token = ctx.console.ask_secret("  GitLab personal access token (api scope): ")
        if not token:
            ctx.console.say(red("  no token given."))
            return FAILED

        try:
            user = ctx.make_gitlab(token).fetch_user()
        except GitLabError as error:
            ctx.console.say(red(f"  {error.detail}"))
            return FAILED

        ctx.console.say(f"  the token belongs to {user.name} <{user.email}>")
        if not ctx.runner.write_file(self.path, render_token_file(token), 0o600):
            ctx.console.say(red(f"  could not write {self.path}"))
            return FAILED
        return DONE


@dataclass(frozen=True)
class UploadSshKey:
    """Register a local public key on the GitLab account."""

    title: str
    public_key_path: Path

    def describe(self, /) -> str:
        """The endpoint, the key and the title, with no token in sight."""
        return (
            "POST https://gitlab.com/api/v4/user/keys\n"
            f"    title: {self.title}\n"
            f"    key:   {self.public_key_path}"
        )

    def perform(self, ctx: Context, /) -> Outcome:
        """Read the public key and upload it, under the stored token."""
        token = ctx.stored_token()
        if not token:
            ctx.console.say(red("  no GitLab token stored; run --only gitlab-token"))
            return FAILED

        public_key = read_text(self.public_key_path).strip()
        if not public_key:
            ctx.console.say(red(f"  {self.public_key_path} is missing or empty"))
            return FAILED

        try:
            key = ctx.make_gitlab(token).upload_ssh_key(self.title, public_key)
        except GitLabError as error:
            ctx.console.say(red(f"  {error.detail}"))
            return FAILED

        ctx.console.say(f"  {key.fingerprint} is on the account as {key.title!r}")
        return DONE


@dataclass(frozen=True)
class SourceNixProfile:
    """Put a freshly installed nix on PATH for the rest of this run.

    The installer writes a shell profile, and sourcing it is what a new login shell
    would do -- the one thing here that genuinely is a shell's job.
    """

    profile: Path

    def describe(self, /) -> str:
        """The profile that will be sourced."""
        return f"source {self.profile}, so the remaining steps can see nix"

    def perform(self, ctx: Context, /) -> Outcome:
        """Source it in a subshell and adopt the PATH it produces."""
        if not self.profile.exists():
            return DONE
        result = ctx.runner.run(
            ["bash", "-c", f'. {shlex.quote(str(self.profile))} && printf %s "$PATH"']
        )
        if not result.ok or not result.out:
            return DONE
        os.environ["PATH"] = result.out
        return Outcome(ok=True, nix_now_on_path=True)


#
# Reading and writing the bits of Nix this script owns
#


def read_text(path: Path) -> str:
    """A file's contents, or the empty string when it cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def token_in(contents: str) -> Optional[str]:
    """The GITLAB_TOKEN bound in a Nix file, when there is one."""
    found = TOKEN_BINDING.search(contents)
    return found.group(1) or None if found else None


def escape_nix_string(value: str) -> str:
    """Escape a value for a double-quoted Nix string."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return escaped.replace("${", "\\${")


def render_token_file(token: str) -> str:
    """The whole of `devenv.local.nix` for a checkout that only needs the token."""
    return f'{{ ... }}: {{ env.GITLAB_TOKEN = "{escape_nix_string(token)}"; }}\n'


def holds_only_a_token(contents: str) -> bool:
    """Whether a `devenv.local.nix` carries nothing this script would destroy.

    Rewriting the file is only safe when its sole binding is the token. The same file
    is where a developer keeps every other local override, and `cicd-mode-enter`
    writes `{ env.cicd = true; }` into it.
    """
    meaningful = [
        line.strip()
        for line in contents.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not meaningful:
        return True
    return len(meaningful) == 1 and "GITLAB_TOKEN" in meaningful[0]
