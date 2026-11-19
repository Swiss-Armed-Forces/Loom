"""Walking the steps: what is printed, what is asked, and what is carried out.

The driver owns every `print` and the one piece of state that moves during a run. A step
reports what it changed by returning an `Outcome`, which is folded into the `Session`
here, so nothing reaches into a shared mutable object.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import FrozenSet, Optional, Sequence

import setup_devenv
from git_cleanup_common import Answer, prompt
from setup_devenv.actions import (
    Context,
    Machine,
    Runner,
    Session,
    TerminalConsole,
    bold,
    fold,
    read_text,
    red,
)
from setup_devenv.steps import (
    MINIMUM_PYTHON,
    PROBED_TOOLS,
    STEPS,
    Assessment,
    State,
    Step,
    select,
)

#
# Driving them
#


@dataclass(frozen=True)
class StepResult:
    """Whether a step succeeded, and the session it leaves behind."""

    ok: bool
    session: Session


def probe_tools() -> FrozenSet[str]:
    """Which of the executables the steps care about are on PATH right now."""
    return frozenset(tool for tool in PROBED_TOOLS if shutil.which(tool))


def distro_name() -> str:
    """A readable distribution name, or the platform as a fallback."""
    for line in read_text(Path("/etc/os-release")).splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.partition("=")[2].strip().strip('"')
    return platform.platform()


def preflight(ctx: Context, session: Session) -> bool:
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
    if session.dry_run:
        print()
        print("  --dry-run: nothing is run, written, asked for or fetched.")
    print()

    if os.geteuid() == 0:
        print(
            "Refusing to run as root. direnv trust and docker group membership\n"
            "belong to your own account; this script asks for sudo where it is\n"
            "actually needed."
        )
        return False

    return True


def announce(step: Step, assessment: Assessment) -> None:
    """Print what a step wants to do, before anything is asked."""
    print(f"  why: {step.why}")
    if assessment.detail:
        print(f"  {assessment.detail}")
    if assessment.preview:
        print()
        for line in assessment.preview.splitlines():
            print(f"    {line}")
    for action in assessment.actions:
        print()
        print(f"    {action.describe()}")
    print()


def hand_back(assessment: Assessment) -> None:
    """Print a step that is leaving the work to the operator."""
    blocked = assessment.state is State.BLOCKED
    label = "blocked" if blocked else "needs you"
    line = f"  {label}: {assessment.detail}"
    print(red(line) if blocked else line)
    if assessment.instructions:
        print()
        for text in assessment.instructions.splitlines():
            print(f"    {text}")
    print()


def carry_out(ctx: Context, session: Session, assessment: Assessment) -> StepResult:
    """Perform a step's actions, folding what they changed into the session."""
    if session.dry_run:
        print("  (dry run, not executed)")
        return StepResult(True, session)

    for action in assessment.actions:
        outcome = action.perform(ctx)
        session = fold(session, outcome)
        if not outcome.ok:
            print(red(f"  failed: {action.describe().splitlines()[0]}"))
            return StepResult(False, session)
    return StepResult(True, session)


def heading(index: int, total: int, step: Step) -> str:
    """The rule that introduces a step."""
    progress = f"{index}/{total}"
    width = max(0, 60 - len(step.name) - len(progress) - 3)
    return bold(f"{progress} {step.emoji} {step.name} " + "─" * width)


def run_steps(ctx: Context, steps: Sequence[Step], session: Session) -> int:
    """Walk the steps, asking before each one.

    Returns the number that failed.
    """
    failures = 0
    assume_yes = session.assume_yes
    for index, step in enumerate(steps, start=1):
        print(heading(index, len(steps), step))
        assessment = step.assess(ctx, session)

        if assessment.state is State.SATISFIED:
            print(f"  ✅ {assessment.detail}")
            print()
            continue

        if assessment.state in (State.MANUAL, State.BLOCKED):
            hand_back(assessment)
            if assessment.state is State.BLOCKED:
                return failures + 1
            continue

        announce(step, assessment)
        answer = prompt(f"  run the {step.name} step?", assume_yes=assume_yes)
        if answer is Answer.QUIT:
            print("  stopping here.")
            return failures
        if answer is Answer.ALL:
            assume_yes = True
        elif answer is Answer.NO:
            print("  skipped.")
            if assessment.required:
                print(red("  this step is required; setup cannot continue."))
                return failures + 1
            print()
            continue

        result = carry_out(ctx, session, assessment)
        session = result.session
        if not result.ok:
            failures += 1
        # A nix installed a moment ago is not in the set probed at startup.
        if session.nix_on_path and not ctx.machine.has("nix"):
            ctx = replace(ctx, machine=replace(ctx.machine, tools=probe_tools()))
        print()
    return failures


def build_context(args: argparse.Namespace) -> Context:
    """Gather the facts the steps read."""
    return Context(
        repo=args.repo.resolve(),
        runner=Runner(),
        console=TerminalConsole(),
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
            tools=probe_tools(),
        ),
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Command line."""
    names = [step.name for step in STEPS]
    parser = argparse.ArgumentParser(
        # The package docstring, not this module's: `--help` describes the
        # command, and the command is the package.
        description=(setup_devenv.__doc__ or "").split("\n\n", maxsplit=1)[0],
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
        help="show every step and its actions; run, write, ask and fetch nothing",
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
    parser.add_argument(
        "--skip-gitlab-token",
        action="store_true",
        help="treat the gitlab-token step as satisfied",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point."""
    if sys.version_info < MINIMUM_PYTHON:
        major, minor = MINIMUM_PYTHON
        print(
            f"cicd/setup-devenv needs Python {major}.{minor} or newer; this is "
            f"{platform.python_version()}. Install a newer python3 and re-run."
        )
        return 1

    args = parse_args(argv)
    ctx = build_context(args)
    session = Session(
        dry_run=args.dry_run,
        assume_yes=args.yes,
        skip_gitlab_token=args.skip_gitlab_token,
        # A dry run writes no nix.conf, so the daemon step would short-circuit and
        # hide the one privileged command somebody ran --dry-run to see.
        nix_conf_changed=args.dry_run,
    )
    if not preflight(ctx, session):
        return 1

    steps = select(STEPS, args.only, args.skip)
    try:
        failures = run_steps(ctx, steps, session)
    except KeyboardInterrupt:
        print()
        print("Cancelled. Nothing further was run.")
        return 130

    print()
    if failures:
        print(f"{failures} step(s) failed. Re-run to retry just those.")
        return 1
    print("✅ Open a new shell in the repository, or run `direnv reload`.")
    return 0
