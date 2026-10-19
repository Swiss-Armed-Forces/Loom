#!/usr/bin/env python3
"""Interactive first-time setup for the Loom development environment.

Walks a fresh clone through everything `Documentation/devenv-setup.md` asks for: Nix,
the binary caches, devenv, direnv and docker. Every step states what it is about to do
and shows the literal command before asking, so nothing happens that the operator has
not read first. A bare Enter declines.

Nothing here needs the development environment it sets up: stdlib only, no Nix, no
project venv. That is the whole point -- it runs before any of them exist.

Re-running is safe. Each step decides for itself whether it is already satisfied and
says so instead of asking again, so this doubles as a way to check a machine.

## The binary caches

The one step worth explaining. Nix refuses a substituter a *client* asks for unless the
caller is in `trusted-users` -- which the nix manual calls "essentially equivalent to
giving that user root access to the system". A daemon that names the caches in its own
`/etc/nix/nix.conf` serves them to everybody without granting anybody anything, so that
is what this writes. `extra-` because the plain spelling replaces the list rather than
adding to it, and a block that forgot `cache.nixos.org` would silently remove it.

Without this the Loom cache is unreachable and `build-appliance-image` compiles the
appliance closure from source -- for `spark`, a qemu-emulated aarch64 kernel, hours
against a 32 MB download.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional, Sequence, Tuple

from git_cleanup_common import Answer, CommandResult, prompt

#
# What gets configured
#


class Cache(NamedTuple):
    """A binary cache and the key its paths are signed with."""

    url: str
    public_key: str


# Keep in step with `cachixPublicKeys` and `cachix.pull` in devenv.nix, which
# stay the source of truth. Every cache devenv pulls from has to be here: one
# left out is one the daemon does not know, and an untrusted caller then gets a
# two-line warning about it on every single nix invocation.
CACHES: Tuple[Cache, ...] = (
    Cache(
        "https://devenv.cachix.org",
        "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=",
    ),
    Cache(
        "https://loom.cachix.org",
        "loom.cachix.org-1:qK4ugmN5g4Pvhv45OLcXTwG53ZnSauwrHLVA0A7Y0rs=",
    ),
    Cache(
        "https://nixpkgs-python.cachix.org",
        "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU=",
    ),
)

NIX_CONF = Path("/etc/nix/nix.conf")

# The block this script owns inside nix.conf. Everything between the markers is
# rewritten on each run and everything outside them is left exactly as it was,
# which is what makes a second run a no-op rather than a second copy.
BLOCK_BEGIN = "# >>> loom devenv setup >>>"
BLOCK_END = "# <<< loom devenv setup <<<"

# The channel devenv is installed from, as in Documentation/devenv-setup.md.
DEVENV_NIXPKGS = "https://github.com/NixOS/nixpkgs/tarball/nixos-26.05"

NIX_INSTALL_URL = "https://nixos.org/nix/install"
DOCKER_INSTALL_DOCS = "https://docs.docker.com/engine/install/"
DIRENV_INSTALL_DOCS = "https://direnv.net/docs/installation.html"
DIRENV_HOOK_DOCS = "https://direnv.net/docs/hook.html"

# Shell -> (rc file, the line that hooks direnv into it).
DIRENV_HOOKS = {
    "bash": (".bashrc", 'eval "$(direnv hook bash)"'),
    "zsh": (".zshrc", 'eval "$(direnv hook zsh)"'),
    "fish": (".config/fish/config.fish", "direnv hook fish | source"),
}


#
# Running things
#


class Runner:
    """Executes commands and writes root-owned files.

    A seam, not an abstraction for its own sake: the tests hand the steps a fake one and
    assert on what *would* have run, so none of the logic below needs a machine to
    exercise it.
    """

    def run(
        self,
        argv: Sequence[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
    ) -> CommandResult:
        """Run a command, capturing output and never raising on failure."""
        merged = None
        if env is not None:
            merged = {**os.environ, **env}
        completed = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False,
            env=merged,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    def run_visible(self, argv: Sequence[str], cwd: Optional[Path] = None) -> int:
        """Run a command with its output going to the terminal.

        Installers are slow and chatty; capturing them would leave the operator watching
        nothing for several minutes.
        """
        return subprocess.run(
            list(argv), cwd=str(cwd) if cwd is not None else None, check=False
        ).returncode

    def write_root_file(self, path: Path, content: str) -> int:
        """Replace a root-owned file, via a temporary file and `sudo install`.

        `sudo tee` would need the content on stdin, which hides it from the operator;
        this way the command shown is the command that runs.
        """
        with tempfile.NamedTemporaryFile(
            "w", suffix=".nix.conf", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(content)
            staged = Path(handle.name)
        try:
            return self.run_visible(
                ["sudo", "install", "-m", "0644", str(staged), str(path)]
            )
        finally:
            staged.unlink(missing_ok=True)


#
# Rendering the nix.conf block
#


def render_block(caches: Sequence[Cache] = CACHES) -> str:
    """The managed block, markers included, without a trailing newline."""
    urls = " ".join(cache.url for cache in caches)
    keys = " ".join(cache.public_key for cache in caches)
    return "\n".join(
        [
            BLOCK_BEGIN,
            "# Written by cicd/setup_devenv.py. Edits between the markers are",
            "# overwritten; edits outside them are kept.",
            f"extra-substituters = {urls}",
            f"extra-trusted-public-keys = {keys}",
            BLOCK_END,
        ]
    )


def apply_block(current: str, block: str) -> str:
    """Return `current` with `block` replacing any previous one, else appended.

    Idempotent by construction: feeding the result back in returns it unchanged.
    """
    begin = current.find(BLOCK_BEGIN)
    end = current.find(BLOCK_END, begin + 1) if begin != -1 else -1
    if begin != -1 and end != -1:
        head = current[:begin]
        tail = current[end + len(BLOCK_END) :]
        return f"{head}{block}{tail}"

    if current and not current.endswith("\n"):
        current += "\n"
    separator = "\n" if current else ""
    return f"{current}{separator}{block}\n"


def nixos_snippet(caches: Sequence[Cache] = CACHES) -> str:
    """The same settings as a NixOS `configuration.nix` fragment."""
    urls = "\n".join(f'    "{cache.url}"' for cache in caches)
    keys = "\n".join(f'    "{cache.public_key}"' for cache in caches)
    return "\n".join(
        [
            "nix.settings = {",
            "  extra-substituters = [",
            urls,
            "  ];",
            "  extra-trusted-public-keys = [",
            keys,
            "  ];",
            "};",
        ]
    )


#
# Steps
#


class State(Enum):
    """What a step found when it looked."""

    SATISFIED = "satisfied"
    NEEDED = "needed"
    MANUAL = "manual"


@dataclass(frozen=True)
class Machine:
    """What this computer is, as far as setting it up is concerned.

    Read once in `build_context` and never again, so a step cannot reach for a fact the
    tests have no way to state.
    """

    is_nixos: bool
    has_systemd: bool
    home: Path
    user: str
    shell: str


@dataclass
class Context:
    """The run: what it is setting up, how, and what earlier steps changed."""

    repo: Path
    runner: Runner
    machine: Machine
    dry_run: bool = False
    nix_conf_changed: bool = False


@dataclass(frozen=True)
class Assessment:
    """What a step decided, and what it would do about it."""

    state: State
    detail: str
    argv: Sequence[Sequence[str]] = field(default_factory=tuple)
    # Shown verbatim before the prompt, for a step whose effect is a file's
    # contents rather than the command that puts them there.
    preview: Optional[str] = None
    # For MANUAL: what the operator has to do by hand.
    instructions: Optional[str] = None
    write: Optional[Tuple[Path, str]] = None


@dataclass(frozen=True)
class Step:
    """One named unit of setup."""

    name: str
    why: str
    assess: Callable[[Context], Assessment]


def assess_nix(ctx: Context) -> Assessment:
    """Nix itself."""
    if ctx.machine.is_nixos:
        return Assessment(State.SATISFIED, "NixOS ships nix")
    if shutil.which("nix"):
        return Assessment(State.SATISFIED, "nix is on PATH")
    notes = (
        "The installer needs root and sets up the multi-user daemon.\n"
        "    On Fedora, comment out the first two lines of\n"
        "    /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh afterwards.\n"
        "    With SELinux enforcing, set SELINUX=disabled in /etc/selinux/config\n"
        "    and reboot first."
    )
    return Assessment(
        State.NEEDED,
        notes,
        argv=[["bash", "-c", f"sh <(curl -L {NIX_INSTALL_URL}) --daemon"]],
    )


def assess_caches(ctx: Context) -> Assessment:
    """The binary caches -- the reason this script exists."""
    block = render_block()

    if ctx.machine.is_nixos:
        # /etc/nix/nix.conf on NixOS is a symlink into the store, regenerated by
        # every nixos-rebuild. Writing it would appear to work and then vanish.
        return Assessment(
            State.MANUAL,
            "NixOS generates /etc/nix/nix.conf, so it cannot be edited directly",
            instructions=(
                "Add this to your configuration.nix and run `nixos-rebuild "
                "switch`:\n\n" + nixos_snippet()
            ),
        )

    current = NIX_CONF.read_text(encoding="utf-8") if NIX_CONF.exists() else ""
    desired = apply_block(current, block)
    if desired == current:
        return Assessment(State.SATISFIED, f"{NIX_CONF} already names every cache")

    verb = "Updating" if BLOCK_BEGIN in current else "Adding"
    return Assessment(
        State.NEEDED,
        f"{verb} the managed block in {NIX_CONF}",
        preview=block,
        write=(NIX_CONF, desired),
    )


def assess_daemon(ctx: Context) -> Assessment:
    """Restarting the daemon, so the new nix.conf takes effect."""
    if not ctx.nix_conf_changed:
        return Assessment(State.SATISFIED, "nix.conf unchanged, nothing to reload")
    if not ctx.machine.has_systemd:
        return Assessment(
            State.MANUAL,
            "no systemctl found",
            instructions="Restart the nix daemon however this system manages it.",
        )
    return Assessment(
        State.NEEDED,
        "the daemon reads nix.conf at startup",
        argv=[["sudo", "systemctl", "restart", "nix-daemon.service"]],
    )


def assess_devenv(_ctx: Context) -> Assessment:
    """devenv."""
    if shutil.which("devenv"):
        return Assessment(State.SATISFIED, "devenv is on PATH")
    return Assessment(
        State.NEEDED,
        "installs into your user profile, not system-wide",
        argv=[["nix-env", "--install", "--attr", "devenv", "-f", DEVENV_NIXPKGS]],
    )


def assess_direnv(ctx: Context) -> Assessment:
    """Direnv, and its shell hook."""
    if not shutil.which("direnv"):
        return Assessment(
            State.NEEDED,
            "loads the environment on cd, so no command needs a devenv prefix",
            argv=[["nix-env", "--install", "--attr", "nixpkgs.direnv"]],
        )

    hook = DIRENV_HOOKS.get(ctx.machine.shell)
    if hook is None:
        return Assessment(
            State.MANUAL,
            f"unknown shell {ctx.machine.shell!r}",
            instructions=f"Hook direnv into your shell: {DIRENV_HOOK_DOCS}",
        )

    rc_name, line = hook
    rc_path = ctx.machine.home / rc_name
    existing = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
    if "direnv hook" in existing:
        return Assessment(State.SATISFIED, f"hooked into {rc_path}")

    return Assessment(
        State.MANUAL,
        f"not hooked into {rc_path}",
        # Appending to a dotfile behind someone's back is the one thing here
        # that cannot be undone by re-running, so it is shown rather than done.
        instructions=f"Add this line to {rc_path}, then open a new shell:\n\n{line}",
    )


def assess_docker(ctx: Context) -> Assessment:
    """Docker, which `up` needs."""
    if not shutil.which("docker"):
        return Assessment(
            State.MANUAL,
            "docker is not installed",
            instructions=(
                "Install docker-engine -- not docker-desktop -- following\n"
                f"{DOCKER_INSTALL_DOCS}, then run this script again."
            ),
        )

    probe = ctx.runner.run(["docker", "info"])
    if probe.ok:
        return Assessment(State.SATISFIED, "docker responds")

    combined = f"{probe.stdout}{probe.stderr}".lower()
    if "permission denied" in combined or "dial unix" in combined:
        return Assessment(
            State.NEEDED,
            "your account cannot reach the docker socket "
            "(the group change needs a re-login to take effect)",
            argv=[["sudo", "gpasswd", "-a", ctx.machine.user, "docker"]],
        )
    return Assessment(
        State.MANUAL,
        "docker is installed but not responding",
        instructions=(
            "Start the docker daemon (`sudo systemctl start docker`) and run "
            "this script again."
        ),
    )


def assess_allow(ctx: Context) -> Assessment:
    """Trusting this checkout, so direnv will load it."""
    if not shutil.which("direnv"):
        return Assessment(State.MANUAL, "direnv is not installed yet", instructions="")

    status = ctx.runner.run(["direnv", "status"], cwd=ctx.repo)
    if "Found RC allowed true" in status.stdout or "allowed 0" in status.stdout:
        return Assessment(State.SATISFIED, f"{ctx.repo} is already allowed")
    return Assessment(
        State.NEEDED,
        "direnv refuses to load an untrusted directory",
        argv=[["direnv", "allow"]],
    )


def assess_verify(ctx: Context) -> Assessment:
    """Proving the daemon really offers the caches.

    Deliberately asks the daemon with NIX_CONFIG emptied. Inside the devenv shell that
    variable already names every cache, so leaving it set would make this report success
    no matter what /etc/nix/nix.conf says -- it would be measuring the thing we are
    trying to verify.
    """
    if not shutil.which("nix"):
        return Assessment(State.MANUAL, "nix is not installed yet", instructions="")

    missing = effective_gaps(ctx)
    if missing is None:
        return Assessment(
            State.MANUAL,
            "could not read the effective nix configuration",
            instructions="Run `nix config show substituters` and check by hand.",
        )
    if not missing:
        return Assessment(State.SATISFIED, "every cache and key is in effect")
    return Assessment(
        State.MANUAL,
        "the daemon does not offer: " + ", ".join(missing),
        instructions=(
            "Re-run the `caches` step, then restart the nix daemon. On NixOS, "
            "apply the configuration.nix snippet and `nixos-rebuild switch`."
        ),
    )


def effective_gaps(ctx: Context) -> Optional[List[str]]:
    """Caches or keys the daemon does not have.

    None when it cannot be read.
    """
    blank = {"NIX_CONFIG": ""}
    subs = ctx.runner.run(["nix", "config", "show", "substituters"], env=blank)
    keys = ctx.runner.run(["nix", "config", "show", "trusted-public-keys"], env=blank)
    if not subs.ok or not keys.ok:
        return None

    missing: List[str] = []
    for cache in CACHES:
        if cache.url not in subs.stdout:
            missing.append(cache.url)
        elif cache.public_key not in keys.stdout:
            missing.append(f"{cache.url} (key)")
    return missing


STEPS: Tuple[Step, ...] = (
    Step("nix", "the package manager everything else is built on", assess_nix),
    Step("caches", "so builds are fetched instead of compiled", assess_caches),
    Step("daemon", "picks up the cache configuration", assess_daemon),
    Step("devenv", "provides the project's toolchain and commands", assess_devenv),
    Step("direnv", "enters that environment automatically", assess_direnv),
    Step("docker", "runs the cluster `up` deploys to", assess_docker),
    Step("allow", "lets direnv load this checkout", assess_allow),
    Step("verify", "confirms the caches are actually reachable", assess_verify),
)


#
# Driving them
#


def preflight(ctx: Context) -> bool:
    """Report what this machine looks like.

    Returns False to refuse the run.
    """
    print("Loom development environment setup")
    print()
    print(f"  repository   {ctx.repo}")
    print(f"  system       {platform.system()} {platform.machine()}")
    print(f"  distribution {'NixOS' if ctx.machine.is_nixos else distro_name()}")
    print(f"  user         {ctx.machine.user}")
    print(f"  shell        {ctx.machine.shell}")
    if ctx.dry_run:
        print()
        print("  --dry-run: nothing will be run or written.")
    print()

    if os.geteuid() == 0:
        print(
            "Refusing to run as root. direnv trust and docker group membership\n"
            "belong to your own account; this script asks for sudo where it is\n"
            "actually needed."
        )
        return False
    return True


def distro_name() -> str:
    """A readable distribution name, or the platform as a fallback."""
    release = Path("/etc/os-release")
    if release.exists():
        for line in release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.partition("=")[2].strip().strip('"')
    return platform.platform()


def describe(assessment: Assessment, step: Step) -> None:
    """Print what a step wants to do, before anything is asked."""
    print(f"  why: {step.why}")
    if assessment.detail:
        print(f"  {assessment.detail}")
    if assessment.preview:
        print()
        for line in assessment.preview.splitlines():
            print(f"    {line}")
    if assessment.write:
        path, _ = assessment.write
        print()
        print(f"    writes {path} (via sudo)")
    for argv in assessment.argv:
        print()
        print(f"    {shell_join(argv)}")
    print()


def shell_join(argv: Sequence[str]) -> str:
    """Render an argv the way it would be typed."""
    parts = []
    for arg in argv:
        parts.append(f"'{arg}'" if " " in arg and not arg.startswith("'") else arg)
    return " ".join(parts)


def perform(ctx: Context, step: Step, assessment: Assessment) -> bool:
    """Carry out a step.

    Returns whether it succeeded.
    """
    if ctx.dry_run:
        print("  (dry run, not executed)")
        return True

    if assessment.write is not None:
        path, content = assessment.write
        if ctx.runner.write_root_file(path, content) != 0:
            print(f"  failed to write {path}")
            return False
        ctx.nix_conf_changed = True

    for argv in assessment.argv:
        if ctx.runner.run_visible(argv, cwd=ctx.repo) != 0:
            print(f"  command failed: {shell_join(argv)}")
            return False

    if step.name == "caches":
        ctx.nix_conf_changed = True
    return True


def run_steps(ctx: Context, steps: Sequence[Step], assume_yes: bool) -> int:
    """Walk the steps, asking before each one.

    Returns an exit code.
    """
    failures = 0
    for step in steps:
        print(f"── {step.name} " + "─" * max(0, 60 - len(step.name)))
        assessment = step.assess(ctx)

        if assessment.state is State.SATISFIED:
            print(f"  already done: {assessment.detail}")
            print()
            continue

        if assessment.state is State.MANUAL:
            print(f"  needs you: {assessment.detail}")
            if assessment.instructions:
                print()
                for line in assessment.instructions.splitlines():
                    print(f"    {line}")
            print()
            continue

        describe(assessment, step)
        answer = prompt(f"  run the {step.name} step?", assume_yes=assume_yes)
        if answer is Answer.QUIT:
            print("  stopping here.")
            return failures
        if answer is Answer.ALL:
            assume_yes = True
        elif answer is Answer.NO:
            print("  skipped.")
            print()
            continue

        if not perform(ctx, step, assessment):
            failures += 1
        print()
    return failures


def select(names: Sequence[str], only: List[str], skip: List[str]) -> List[Step]:
    """The steps to run, honouring --only and --skip."""
    unknown = set(only) | set(skip)
    unknown -= set(names)
    if unknown:
        raise SystemExit(
            f"unknown step(s): {', '.join(sorted(unknown))}. "
            f"Valid: {', '.join(names)}"
        )
    chosen = [step for step in STEPS if not only or step.name in only]
    return [step for step in chosen if step.name not in skip]


def build_context(args: argparse.Namespace) -> Context:
    """Gather the facts the steps read."""
    return Context(
        repo=args.repo.resolve(),
        runner=Runner(),
        dry_run=args.dry_run,
        machine=Machine(
            # /etc/NIXOS is the marker NixOS itself writes. Checking it rather
            # than the os-release id, because what matters here is that
            # /etc/nix/nix.conf is generated, not what the distribution calls
            # itself.
            is_nixos=Path("/etc/NIXOS").exists(),
            has_systemd=shutil.which("systemctl") is not None,
            home=Path.home(),
            user=os.environ.get("USER") or Path.home().name,
            shell=Path(os.environ.get("SHELL", "")).name or "unknown",
        ),
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Command line."""
    names = [step.name for step in STEPS]
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n", maxsplit=1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"steps, in order: {', '.join(names)}",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="the Loom checkout to set up (default: the one holding this script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show every step and its commands, run nothing",
    )
    parser.add_argument(
        "--yes", action="store_true", help="assume yes, for an unattended run"
    )
    parser.add_argument(
        "--only", action="append", default=[], metavar="STEP", help="run only this step"
    )
    parser.add_argument(
        "--skip", action="append", default=[], metavar="STEP", help="skip this step"
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    ctx = build_context(args)
    if not preflight(ctx):
        return 1

    steps = select([step.name for step in STEPS], args.only, args.skip)
    try:
        failures = run_steps(ctx, steps, assume_yes=args.yes)
    except KeyboardInterrupt:
        print()
        print("Cancelled. Nothing further was run.")
        return 130

    print()
    if failures:
        print(f"{failures} step(s) failed. Re-run to retry just those.")
        return 1
    print("Done. Open a new shell in the repository, or run `direnv reload`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
