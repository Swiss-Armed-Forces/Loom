"""What the NixOS test driver hands a test script, as types.

Every test in this package used to be a string inside a `.nix` file, where nothing in
this repository could lint it or check its types. Out here the repository's own hooks
reach them -- black, isort, flake8, pylint and mypy, the same set every other Python
directory gets.

They reached that state in two steps, and the second one is why this is a package. At
first each `.nix` file inlined its script with `builtins.readFile`, which put every
script the driver ran into one namespace: two files could not both `import json`
without ruff rejecting the pair, and nothing could be shared *between* tests, so two
of them grew their own copy of the /dev/vcsa1 decoder. Now `nixos/tests/scripts.nix`
builds this directory as a Python package and each test installs it through the
driver's `extraPythonPackages`, so the modules import each other like ordinary Python
and the helpers live in one place (`vt.py`, `tmux.py`).

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

from typing import Callable, ContextManager, Protocol

# `start_all()` and `with subtest("..."):`, which the driver provides as plain
# globals.
StartAll = Callable[[], None]
Subtest = Callable[[str], ContextManager[None]]


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

    def wait_until_fails(self, command: str, timeout: int = 900) -> str:
        """Retry a command until it exits non-zero."""

    def wait_for_console_text(self, regex: str, timeout: int | None = None) -> None:
        """Block until the machine prints something matching `regex`."""

    def wait_until_tty_matches(self, tty: str, regexp: str, timeout: int = 900) -> None:
        """Block until one virtual console shows something matching `regexp`."""

    def send_chars(self, chars: str, delay: float | None = 0.01) -> None:
        """Type at the console."""

    def send_key(self, key: str, delay: float | None = 0.01, log: bool = True) -> None:
        """Press one key at the console."""

    def sleep(self, secs: int) -> None:
        """Wait, on the machine's own clock."""

    def start(self, allow_reboot: bool = False) -> None:
        """Boot the machine."""

    def shutdown(self) -> None:
        """Power it off and wait for it."""

    def crash(self) -> None:
        """Pull the plug."""

    def wait_for_shutdown(self) -> None:
        """Block until the machine is gone."""
