"""Turning the screen's contents into bytes a Linux VT will accept.

Everything here answers to one consumer: agetty, painting an issue file straight to a
VT with no paging. That imposes four rules which are enforced in this module and
nowhere else, so that the five units writing to /run/issue.d cannot each get them
slightly wrong.

  * **No backslash, anywhere.** agetty reads one in an issue file as the start of an
    escape of its own and eats it before the screen sees it. `_safe` raises instead,
    because a silently swallowed character in a passphrase is unrecoverable from the
    console it was supposed to be read on.
  * **Nothing wider than `WIDTH`.** The console cannot be measured -- it is resized
    several times during boot, so any reading describes a screen that no longer
    exists by the time agetty paints -- and the narrowest in play is the 80-column
    getty a --vm-serial box carries.
  * **Sixteen colours, named.** console_codes(4) shoehorns even a 24-bit SGR into the
    basic sixteen, so rich's default truecolor lands somewhere unpredictable.
  * **No intensity.** branding.nix loads a 512-glyph font and setfont(8) spends the
    console's intensity bit on glyph selection past 256, so `bold` cannot be relied
    on to show. Emphasis is carried by reverse video and by hue.

rich draws the styles and owns the colour system; the geometry is composed here with
`Text.assemble` rather than with `Table.grid`, because a grid pads every cell in a
column to the width of its widest and that padding lands *inside* the style -- which
turns a short secret into a long reverse-video bar.
"""

import os
from dataclasses import dataclass
from typing import IO, Iterable, Mapping

from rich.console import Console
from rich.text import Text

# The right margin, and the indent every line carries. Two spaces is what the mark
# is drawn at, so the text lines up under it.
WIDTH = 78
INDENT = 2

# Where a value starts, measured from the indent. A label that does not fit is a
# mistake in the caller rather than a long label: this column is the whole reason
# the block can be read down rather than hunted through.
LABEL_COLUMN = 27

# The glyph section rules are drawn from. branding.nix asserts the console font
# carries it, along with the rest of the box-drawing set.
RULE = "─"

# "Type this." The one thing on the screen a person is holding a phone up to.
SECRET_STYLE = "reverse"

# A problem, and a danger. Hue rather than weight, for the intensity reason above.
PROBLEM_STYLE = "red"
DANGER_STYLE = "bold white on red"

# The QR card: black modules on a white field, which is the orientation every
# scanner is tuned for. Palette index 7 is redefined to pure white by `palette`
# below, so `white` here really is white rather than light grey.
CARD_STYLE = "black on white"


class BannerError(ValueError):
    """A value that cannot be put on the login screen."""


@dataclass(frozen=True)
class Colour:
    """What this screen may emit, which is not the same question as "is it a tty".

    `palette` is the ESC]P redefinition of palette entries 3, B and 7. It reaches a
    Linux VT and nothing else -- console_codes(4) warns that xterm hangs on it until
    somebody presses return -- so it is emitted only where the output is known to be
    one.
    """

    sgr: bool
    palette: bool

    @classmethod
    def decide(
        cls, stream: IO[str], environ: Mapping[str, str] | None = None
    ) -> "Colour":
        environ = os.environ if environ is None else environ
        # loom-issue.service captures this output into a file, so the checks below
        # cannot see the console -- but that file is read only by agetty, and agetty
        # is only ever on a VT here.
        if environ.get("LOOM_INFO_COLOR", "auto") == "vt":
            return cls(sgr=True, palette=True)
        if not _isatty(stream):
            # Keyed on the stream so that `loom-info > banner.txt` stays readable.
            return cls(sgr=False, palette=False)
        # A pts -- a tmux pane of the console session -- gets the selector but not
        # the redefinition, and still comes out amber: the VT underneath it had its
        # palette rewritten by the banner at boot.
        return cls(sgr=True, palette=_is_vt(stream))


def console(stream: IO[str], colour: Colour) -> Console:
    """The one Console, with every default that matters pinned.

    `force_terminal` because the banner's usual destination is a file; without it rich
    strips the colour the screen exists for. `highlight=False` and `markup=False`
    because the values here are passphrases, SSIDs and URLs: rich's auto-highlighter
    would recolour them, and its markup parser would eat any bracketed run inside one.
    """
    return Console(
        file=stream,
        width=WIDTH,
        force_terminal=colour.sgr,
        color_system="standard" if colour.sgr else None,
        no_color=not colour.sgr,
        highlight=False,
        markup=False,
        emoji=False,
        soft_wrap=False,
    )


def rule(title: str, style: str = "") -> Text:
    """`── Connect ────…`, to the right margin.

    Composed rather than handed to `rich.rule.Rule`, whose left-aligned form puts no
    glyphs before the title and has no reason to keep that layout across releases.
    """
    opening = f"{RULE * 2} {_safe(title)} "
    width = WIDTH - INDENT - _width(opening)
    if width < 1:
        raise BannerError(f"section title leaves no room for a rule: {title!r}")
    return _indented(Text(f"{opening}{RULE * width}", style=style))


def row(label: str, value: str, secret: bool = False) -> Text:
    """`Portal password (today):   backspin.finisher.taste.unsmooth`.

    The style covers the value and not the padding, so a short secret is a short field
    rather than a ragged bar.
    """
    label = _safe(label)
    if _width(label) > LABEL_COLUMN - 1:
        raise BannerError(
            f"label {label!r} is {_width(label)} columns, over the {LABEL_COLUMN - 1} "
            "the value column leaves it"
        )
    return _indented(
        Text.assemble(
            (f"{label:<{LABEL_COLUMN}}", ""),
            (_safe(value), SECRET_STYLE if secret else ""),
        )
    )


def note(text: str, style: str = "") -> Text:
    """A line of prose: the caveat under a secret, the instruction under a rule."""
    return _indented(Text(_safe(text), style=style))


def card(lines: Iterable[str]) -> list[Text]:
    """The QR code, as a solid rectangle.

    The background is re-opened per line because a terminal resets it at the newline,
    and one long run would paint a staircase rather than a card.
    """
    return [_indented(Text(_safe(line), style=CARD_STYLE)) for line in lines]


def danger(lines: Iterable[str]) -> list[Text]:
    """The warning an image gives up a guarantee for.

    Padded to a common width so the background runs to the same column on every row,
    which is what makes it read as a block rather than as coloured text.
    """
    padded = [f" {_safe(line)} " for line in lines]
    width = max((_width(line) for line in padded), default=0)
    return [_indented(Text(f"{line:<{width}}", style=DANGER_STYLE)) for line in padded]


def palette(amber_rgb: str) -> str:
    """The VT palette redefinition, as raw bytes for the stream.

    Indices 3 and B are both set because bold promotes one to the other and a
    512-glyph font makes which one unpredictable; index 7 becomes pure white so the
    QR card is a card and ordinary text is white rather than grey.

    Deliberately not followed by a reset: a VT looks the palette up when it paints,
    not when the character was written, so restoring it would recolour the mark
    already on screen.
    """
    if not _HEX.issuperset(amber_rgb.lower()) or len(amber_rgb) != 6:
        raise BannerError(f"not a six-digit hex colour: {amber_rgb!r}")
    return f"\033]P3{amber_rgb}\033]PB{amber_rgb}\033]P7ffffff"


_HEX = set("0123456789abcdef")

# Selecting the palette entry above, and dropping back out of it. Safe anywhere:
# these are ordinary SGR, unlike the redefinition they select.
AMBER = "\033[33m"
RESET = "\033[0m"


def _indented(text: Text) -> Text:
    return Text(" " * INDENT) + text


def _safe(value: str) -> str:
    if "\\" in value:
        raise BannerError(
            f"{value!r} contains a backslash, which agetty eats out of an issue file"
        )
    return value


def _width(value: str) -> int:
    return len(value)


def _isatty(stream: IO[str]) -> bool:
    try:
        return stream.isatty()
    except (AttributeError, ValueError):
        return False


def _is_vt(stream: IO[str]) -> bool:
    """Whether this stream is a Linux VT rather than a pts of one."""
    try:
        name = os.ttyname(stream.fileno())
    except (AttributeError, OSError, ValueError):
        return False
    return name.startswith("/dev/tty") and name[len("/dev/tty") :].isdigit()
