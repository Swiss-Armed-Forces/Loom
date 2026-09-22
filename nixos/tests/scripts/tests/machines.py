"""A machine that is not booted.

`loom_tests.driver.Machine` is a Protocol, which is what makes this possible: the
helpers that parse a screen or a pane list take a machine and call one method on it, so
a stand-in that answers that one method exercises all of them. Nothing is patched -- the
seam is the argument, the way it is in nixos/ready and nixos/usb-ingest.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from loom_tests.driver import Machine


@dataclass
class FakeMachine:
    """Canned command output, and a record of what was asked for.

    The record matters for the helpers that build commands: `Session.panes` has a format
    string in it, and a test that only checked the parsed result would pass while the
    command asked the wrong question.
    """

    answers: dict[str, str] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)

    def succeed(self, *commands: str, timeout: int | None = None) -> str:
        del timeout
        out = []
        for command in commands:
            self.calls.append(command)
            out.append(self._answer(command))
        return "".join(out)

    def _answer(self, command: str) -> str:
        for fragment, answer in self.answers.items():
            if fragment in command:
                return answer
        raise AssertionError(f"nothing canned for {command!r}")


def as_machine(fake: FakeMachine) -> "Machine":
    """The double, typed as the thing it stands in for.

    `Machine` is a Protocol with two dozen methods and this implements the one the pure
    helpers call, which is the point of a double -- but structural typing checks the
    whole protocol, so the cast is what says "this is deliberate". Keeping it in one
    place means the tests read as tests rather than as type plumbing.
    """
    return cast("Machine", fake)
