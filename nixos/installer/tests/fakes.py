"""A box that answers questions, without being a box.

Every probe in `loom_installer.devices` and `loom_installer.storage` goes through a
`CommandRunner`, so a recorded set of answers is all it takes to put the rules in front
of a disk layout that would otherwise need hardware. This is the fake, and it is
deliberately a real object rather than a patched module: nothing here reaches into the
code under test, it is handed in.

The same goes for the screen: `ScriptedUi` below is a real `Ui` writing into a buffer,
subclassed to answer a prompt. Both doubles live here rather than beside the first test
that needed them, because more than one now does.
"""

import io
from dataclasses import dataclass, field
from typing import Final, NamedTuple

from rich.console import Console

from loom_installer import constants, devices
from loom_installer.commands import CommandResult
from loom_installer.console import THEME, Ui


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
    # Every command that was run, with whatever was piped into it. `calls` below is
    # the same list without the pipes, which is what a dozen assertions index into.
    piped: list[FakeCall] = field(default_factory=list)
    # Answers that are consumed rather than repeated, for the one thing on a box
    # that legitimately gives a different answer to the same question twice: a
    # passphrase prompt somebody got wrong and then got right.
    queued: dict[str, list[CommandResult]] = field(default_factory=dict)
    # Commands that do not come back. The type rather than an instance, so that a
    # re-raised exception does not accumulate a traceback across calls.
    raises: dict[str, type[BaseException]] = field(default_factory=dict)

    @property
    def calls(self) -> list[list[str]]:
        """What was run, in order, without the piped input."""
        return [list(call.argv) for call in self.piped]

    def run(
        self, argv: list[str], *, stdin: str | None = None, timeout: int = 300
    ) -> CommandResult:
        del timeout
        key = " ".join(argv)
        self.piped.append(FakeCall(list(argv), stdin))

        # After the recording above, so that the command this landed on is in
        # `calls` -- which is how a test says "and everything after this point".
        problem = self.raises.get(key)
        if problem is not None:
            raise problem(key)

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

    def interrupts(self, argv: list[str]) -> None:
        """Ctrl-C lands while this command is running."""
        self.raises[" ".join(argv)] = KeyboardInterrupt


@dataclass(frozen=True)
class ScriptedUi(Ui):
    """A `Ui` with the operator's answers queued up.

    A subclass rather than a patch: everything that prompts is handed its Ui, so the
    double goes in the front door. Everything else about it is a real Ui writing into a
    buffer, which is how test_console.py builds one too.

    `answers` feeds `prompt_passphrase`. `interrupted` is the other kind of answer:
    Ctrl-C, injected at the one place this program blocks on a keyboard, so that the
    real `prompt` is what turns it into `Aborted`.
    """

    answers: list[str] = field(default_factory=list)
    interrupted: bool = False

    def prompt_passphrase(self, message: str) -> str:
        del message
        return self.answers.pop(0)

    def _read_line(self) -> str:
        if self.interrupted:
            raise KeyboardInterrupt
        return super()._read_line()


def scripted_ui(
    answers: list[str] | None = None, interrupted: bool = False
) -> ScriptedUi:
    """A `ScriptedUi` over a throwaway buffer."""
    console = Console(
        file=io.StringIO(),
        force_terminal=False,
        markup=False,
        highlight=False,
        width=80,
        # The real theme, because what is drawn through this includes the interlock's
        # panels -- and rich raises on a style name it has never heard of.
        theme=THEME,
    )
    return ScriptedUi(
        out=console,
        err=console,
        answers=list(answers or []),
        interrupted=interrupted,
    )


def printed(ui: ScriptedUi) -> str:
    """Everything the Ui above has been asked to draw."""
    assert isinstance(ui.out.file, io.StringIO)
    return ui.out.file.getvalue()


def with_label(runner: FakeRunner, label: str, partition: str, disk: str) -> FakeRunner:
    """One of our partition labels, on a partition of `disk`.

    The three answers `devices.boot_disk` needs to resolve a label: the symlink under
    by-partlabel, a device node at the end of it, and the parent disk lsblk reports.
    """
    runner.links[f"{constants.BY_PARTLABEL}/{label}"] = partition
    runner.block_devices.add(partition)
    runner.succeeds(
        ["lsblk", "--noheadings", "--raw", "--paths", "--output", "PKNAME", partition],
        f"{disk}\n",
    )
    return runner


def with_stick(runner: FakeRunner, disk: str = "/dev/sda") -> FakeRunner:
    """A Loom stick, with all three of its labels on one device."""
    for index, label in enumerate(
        (constants.KEY_LABEL, constants.LIVE_STORE_LABEL, constants.LIVE_ESP_LABEL),
        start=1,
    ):
        with_label(runner, label, f"{disk}{index}", disk)
    return runner


def with_internal_nvme(runner: FakeRunner, disk: str) -> FakeRunner:
    """An ordinary internal NVMe: not removable, not USB, nothing mounted."""
    runner.files[f"/sys/block/{disk.removeprefix('/dev/')}/removable"] = "0\n"
    runner.succeeds(
        ["udevadm", "info", "--query=property", f"--name={disk}"],
        "ID_MODEL=SAMSUNG\nID_BUS=nvme\n",
    )
    runner.succeeds(
        ["lsblk", "--noheadings", "--raw", "--paths", "--output", "MOUNTPOINTS", disk],
        "\n\n",
    )
    return runner


# What nixos/installer.nix sets on the wrapper, which is how these programs are
# configured. Setting it is using the real interface rather than reaching past one --
# but `settings()` is read once per process, so a fixture over this has to
# `settings.cache_clear()` on both sides of its yield.
INSTALLER_ENVIRONMENT: Final[dict[str, str]] = {
    "LOOM_EFI_ARCH": "x64",
    "LOOM_TAG": "v0.0.0",
    "LOOM_PLATFORM": "test",
    "LOOM_AUTO_GRACE": "30",
    "LOOM_VG_NAME": "loom",
    "LOOM_LV_NAME": "root",
    "LOOM_ROOT_DEVICE": "/dev/mapper/loom-root",
    "LOOM_KEY_LOCKED": "false",
    "LOOM_KEYSTORE_MAPPING": "loom-keystore",
    "LOOM_INSTALLER_BIN": "/run/current-system/sw/bin",
}


def with_installable_box(runner: FakeRunner, disk: str = "/dev/nvme0n1") -> FakeRunner:
    """A box every precondition in `install.run` is happy with.

    The stick with its key, one internal NVMe big enough to be worth installing on,
    and a size answer above `MIN_POOL_BYTES`. What it is *not* is a box the install
    would succeed on: nothing here answers sgdisk or cryptsetup, because the tests
    that use this are about what happens when the install stops.
    """
    with_stick(runner)
    runner.block_devices.add(constants.KEY_DEVICE)
    runner.succeeds(devices.LSBLK_WHOLE_DISKS, f"{disk} disk\n")
    with_internal_nvme(runner, disk)
    runner.succeeds(
        ["blockdev", "--getsize64", disk], f"{2 * constants.MIN_POOL_BYTES}\n"
    )
    return runner
