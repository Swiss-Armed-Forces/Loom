"""What the NixOS test driver hands a test script, as types.

Every test in this package is a Python file rather than a string inside a `.nix` file,
so the repository's own hooks reach them -- black, isort, flake8, pylint and mypy, the
same set every other Python directory gets.

Being a package rather than a script each `.nix` file inlines with `builtins.readFile`
is the other half of that. Inlined scripts share one namespace: two files cannot both
`import json` without ruff rejecting the pair, and nothing can be shared *between*
tests. `nixos/tests/scripts.nix` builds this directory as a Python package and each
test installs it through the driver's `extraPythonPackages`, so the modules import each
other like ordinary Python and the helpers live in one place (`vt.py`, `tmux.py`).

The driver's globals (`start_all`, `subtest`, and one object per node) are still not
importable: they exist only in the namespace the driver `exec`s the testScript in. So
each module exports a single `run()` that takes them as arguments, and the `.nix`
file's testScript is the import plus the one line that calls it. That line is still
checked -- the driver runs ruff over it with the node names as builtins -- but the body
of the test lives somewhere the rest of the toolchain can see.

The declarations below are the half of `${nixpkgs}/nixos/lib/test-script-prepend.py`
these scripts actually use. They are a Protocol rather than the driver's own
`test_driver.machine.Machine`, because that package exists only inside the driver's
closure: importing it here would mean the devenv could not type-check any of this.
Which is also why each test sets `skipTypeCheck = true` -- the driver's mypy cannot
resolve *this* module, so exactly one of the two checks can run, and the one that
runs on every commit is worth more than the one that runs when a VM boots.
"""

from typing import Callable, ContextManager, NamedTuple, Protocol

# `start_all()` and `with subtest("..."):`, which the driver provides as plain
# globals.
StartAll = Callable[[], None]
Subtest = Callable[[str], ContextManager[None]]


class CommandResult(NamedTuple):
    """What `execute` answered, with the two halves named.

    The Protocol below mirrors the upstream NixOS test driver, which really does return
    a bare `tuple[int, str]` -- narrowing it there would make the Protocol a lie about
    the object it describes, and `Machine` would stop satisfying it. So the tuple is
    given names here instead, and this repo's own call sites go through `execute` below
    rather than unpacking positionally.
    """

    status: int
    output: str


def execute(
    machine: "Machine", command: str, timeout: int | None = 900
) -> CommandResult:
    """`machine.execute`, with the result named."""
    status, output = machine.execute(command, timeout=timeout)
    return CommandResult(status=status, output=output)


class Machine(Protocol):
    """One booted node.

    Only the methods these tests call.
    """

    def succeed(self, *commands: str, timeout: int | None = None) -> str:
        """Run shell commands, raising unless every one of them exits 0."""

    def fail(self, *commands: str, timeout: int | None = None) -> str:
        """Run shell commands, raising unless every one of them exits non-zero."""

    def execute(
        self,
        command: str,
        check_return: bool = True,
        check_output: bool = True,
        timeout: int | None = 900,
    ) -> tuple[int, str]:
        """Run one command and return its status and output."""

    def wait_for_unit(
        self, unit: str, user: str | None = None, timeout: int = 900
    ) -> None:
        """Block until a systemd unit is active."""

    def wait_for_file(self, filename: str, timeout: int = 900) -> None:
        """Block until a path exists."""

    def wait_for_open_port(
        self, port: int, addr: str = "localhost", timeout: int = 900
    ) -> None:
        """Block until something is listening."""

    def wait_until_succeeds(self, command: str, timeout: int = 900) -> str:
        """Retry a command until it exits 0."""

    def wait_until_tty_matches(self, tty: str, regexp: str, timeout: int = 900) -> None:
        """Block until one virtual console shows something matching `regexp`."""

    def send_chars(self, chars: str, delay: float | None = 0.01) -> None:
        """Type at the console."""

    def send_key(self, key: str, delay: float | None = 0.01, log: bool = True) -> None:
        """Press one key at the console."""

    def sleep(self, secs: int) -> None:
        """Wait, on the machine's own clock."""

    def wait_for_shutdown(self) -> None:
        """Block until the machine is gone."""
