"""Running the tools the installer is made of.

A thin object rather than bare `subprocess` calls, for one reason: everything that
decides what may be written to -- `devices.py` above all -- asks the box questions
through this, so the rules can be exercised against a recorded set of answers instead of
against a disk. See tests/.

The methods are deliberately few and their failure modes explicit. Shelling out to
`lsblk` and getting "" back because the device vanished is ordinary here, and a helper
that raised on it would turn every probe into a try block.
"""

import logging
import os
import stat
import subprocess
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)

# Nothing the installer runs is interactive, and nothing it runs should be able to
# hang the console session forever. `nixos-install` is the exception and is run
# through `stream` below, which has no deadline.
DEFAULT_TIMEOUT_S = 300


@dataclass(frozen=True)
class CommandResult:
    """What a command did, whether or not it worked."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CommandError(RuntimeError):
    """A command that had to work did not."""

    def __init__(self, argv: list[str], result: CommandResult) -> None:
        super().__init__(argv, result)
        self.argv = argv
        self.result = result

    def __str__(self) -> str:
        """The last line the command said, which is the line worth showing.

        Composed here rather than handed to `super().__init__` so that the exception
        still carries both arguments it was raised with -- what a failing command
        printed is one line on a console, but what it was is what a caller may want to
        look at.
        """
        detail = (self.result.stderr or self.result.stdout).strip().splitlines()
        message = detail[-1] if detail else f"exit status {self.result.returncode}"
        return f"{self.argv[0]}: {message}"


class CommandRunner(Protocol):
    """What `devices.py` and `storage.py` need from the outside world."""

    def run(
        self,
        argv: list[str],
        *,
        stdin: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_S,
    ) -> CommandResult:
        """Run a command, whatever its exit status."""

    def output(self, argv: list[str], *, timeout: int = DEFAULT_TIMEOUT_S) -> str:
        """Standard output, or "" when the command failed."""

    def check(
        self,
        argv: list[str],
        *,
        stdin: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        """Run a command that has to work, or raise `CommandError`."""

    def read_text(self, path: str) -> str | None:
        """A file's contents, or None when it cannot be read."""

    def is_block_device(self, path: str) -> bool:
        """Whether a path is a block device right now."""

    def resolve(self, path: str) -> str | None:
        """Follow a symlink, or None when there is nothing at the end of it."""


class Subprocess:
    """The real one."""

    def run(
        self,
        argv: list[str],
        *,
        stdin: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_S,
    ) -> CommandResult:
        """Run a command and report how it went, never raising on its exit status.

        `stdin` is a pipe rather than a file: the one caller is the recovery
        passphrase going into `cryptsetup luksAddKey`, and a pipe is the only route
        that leaves it neither on disk nor in /proc as a path.
        """
        logger.debug("running %s", argv)
        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                input=stdin,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return CommandResult(127, "", str(error))
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    def output(self, argv: list[str], *, timeout: int = DEFAULT_TIMEOUT_S) -> str:
        """Standard output, or "" if the command failed.

        Every caller of this is a probe whose answer is a line on the operator's screen
        or an input to a decision that treats "nothing" as its own case.
        """
        return self.run(argv, timeout=timeout).stdout

    def check(
        self,
        argv: list[str],
        *,
        stdin: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        """Run a command that has to work, or raise."""
        result = self.run(argv, stdin=stdin, timeout=timeout)
        if not result.ok:
            raise CommandError(argv, result)

    def read_text(self, path: str) -> str | None:
        """A file's contents, or None when it is not there or cannot be read.

        Used for sysfs attributes and for the two files installer.nix writes into
        /etc/loom, both of which are allowed to be absent.
        """
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                return handle.read()
        except OSError:
            return None

    def is_block_device(self, path: str) -> bool:
        """Whether a path is a block device *now*.

        Asked rather than assumed all over this package: a logical volume comes and
        goes as the group is activated, and "the device node is there" is the only
        honest way to tell whether it did.
        """
        try:
            return stat.S_ISBLK(os.stat(path).st_mode)
        except OSError:
            return False

    def resolve(self, path: str) -> str | None:
        """Follow a /dev/disk/by-partlabel symlink, or None when there is none."""
        try:
            return os.path.realpath(path, strict=True)
        except OSError:
            return None
