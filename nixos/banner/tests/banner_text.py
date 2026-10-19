"""Reading a rendered screen the way a console would.

A module of its own, with a basename unique across every suite `appliance-pytest` loads:
they share one pytest session, so a second `conftest` imported by name resolves to
whichever directory landed on `sys.path` first.
"""

import re

SGR = re.compile(r"\x1b\[[0-9;]*m")

# The danger block a --debug image carries, as the fixtures pass it.
WARNINGS = [
    "DEBUG IMAGE -- NEVER USE THIS IN PRODUCTION",
    "This box runs an SSH server.",
]


def visible(text: str) -> str:
    """What a reader sees: the text with every SGR escape taken out."""
    return SGR.sub("", text)


def columns(line: str) -> int:
    """How many cells a line occupies.

    Every glyph this screen draws is one cell wide on a Linux VT -- the box-drawing set,
    the half blocks and ASCII -- so counting characters is counting columns.
    """
    return len(visible(line))
