"""A box that answers questions, without being a box.

Every probe in `loom_installer.devices` and `loom_installer.storage` goes through a
`CommandRunner`, so a recorded set of answers is all it takes to put the rules in front
of a disk layout that would otherwise need hardware. This is the fake, and it is
deliberately a real object rather than a patched module: nothing here reaches into the
code under test, it is handed in.
"""

from dataclasses import dataclass, field
from typing import NamedTuple

from loom_installer.commands import CommandResult


class FakeCall(NamedTuple):
    """One command the code under test ran, and what it piped into it.

    `stdin` is recorded rather than discarded because two things in this package
    deliberately pass a secret that way -- the recovery passphrase into `luksAddKey`,
    and the key-stick passphrase into `cryptsetup open`. A pipe is what keeps either out
    of /proc, so "went in on stdin" is the property worth asserting, not an
    implementation detail.
    """

    argv: list[str]
    stdin: str | None


@dataclass
class FakeRunner:
    """Answers, keyed by the command that asks for them.

    `commands` maps a joined argv to what running it produces; `files` maps a path to
    its contents; `block_devices` and `links` describe what is in /dev. Anything not
    listed behaves the way a missing device does on a real box -- an empty answer, or a
    non-zero exit status -- which is the case most of these rules turn on.
    """

    commands: dict[str, CommandResult] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    block_devices: set[str] = field(default_factory=set)
    links: dict[str, str] = field(default_factory=dict)
    calls: list[list[str]] = field(default_factory=list)
    # As `calls`, with the piped input beside each one. Kept separate rather than
    # changing `calls`, which a dozen existing assertions index into by argv.
    piped: list[FakeCall] = field(default_factory=list)
    # Answers that are consumed rather than repeated, for the one thing on a box
    # that legitimately gives a different answer to the same question twice: a
    # passphrase prompt somebody got wrong and then got right.
    queued: dict[str, list[CommandResult]] = field(default_factory=dict)

    def run(
        self, argv: list[str], *, stdin: str | None = None, timeout: int = 300
    ) -> CommandResult:
        del timeout
        key = " ".join(argv)
        self.calls.append(list(argv))
        self.piped.append(FakeCall(list(argv), stdin))

        pending = self.queued.get(key)
        if pending:
            return pending.pop(0)

        return self.commands.get(key, CommandResult(1, "", "no such answer"))

    def output(self, argv: list[str], *, timeout: int = 300) -> str:
        return self.run(argv, timeout=timeout).stdout

    def check(
        self, argv: list[str], *, stdin: str | None = None, timeout: int = 300
    ) -> None:
        self.run(argv, stdin=stdin, timeout=timeout)

    def read_text(self, path: str) -> str | None:
        return self.files.get(path)

    def is_block_device(self, path: str) -> bool:
        return path in self.block_devices

    def resolve(self, path: str) -> str | None:
        return self.links.get(path)

    def succeeds(self, argv: list[str], stdout: str = "") -> None:
        self.commands[" ".join(argv)] = CommandResult(0, stdout, "")

    def fails_then_succeeds(self, argv: list[str], failures: int) -> None:
        """Refuse this command `failures` times, then behave like `succeeds`."""
        self.queued[" ".join(argv)] = [
            CommandResult(1, "", "No key available with this passphrase.")
            for _ in range(failures)
        ]
        self.succeeds(argv)
