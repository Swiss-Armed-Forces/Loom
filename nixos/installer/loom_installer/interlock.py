"""The typed word that stands between an operator and a destroyed disk.

The action word is the whole interlock: it is never "yes", so it cannot be confirmed by
muscle memory, and the disk that is about to be destroyed is named on screen directly
above the prompt. Transcribing a 20-character NVMe serial was the earlier design and was
simply too tedious to live with.
"""

from rich.table import Table
from rich.text import Text

from loom_installer.commands import CommandRunner
from loom_installer.console import Ui
from loom_installer.devices import describe_disk


class Aborted(RuntimeError):
    """The operator did not type the word."""


def confirm_destructive(
    ui: Ui,
    runner: CommandRunner,
    action: str,
    boot: str,
    targets: list[str],
) -> None:
    """Print what dies and what survives, then demand the action word.

    Nothing clears the screen from here on: the list of disks about to die has to
    stay on screen directly above the prompt.
    """
    doomed = Table.grid(padding=(0, 1))
    doomed.add_column(overflow="fold")
    for disk in targets:
        doomed.add_row(
            Text(describe_disk(runner, disk).describe(), style="loom.danger")
        )
    if len(targets) > 1:
        doomed.add_row(
            Text(
                f"^^ ALL {len(targets)} DISKS ABOVE, not just the first.",
                style="loom.danger",
            )
        )

    ui.blank()
    ui.show(
        ui.panel(
            doomed,
            f"{action}: THE FOLLOWING WILL BE DESTROYED",
            style="loom.danger",
        )
    )

    survivor = Table.grid(padding=(0, 1))
    survivor.add_column(overflow="fold")
    survivor.add_row(Text(describe_disk(runner, boot).describe(), style="loom.quiet"))
    ui.show(ui.panel(survivor, "WILL NOT BE TOUCHED (boot medium)", style="loom.ok"))
    ui.blank()

    answer = ui.prompt(f"Type {action} to proceed: ")
    if answer != action:
        raise Aborted("Aborted.")
