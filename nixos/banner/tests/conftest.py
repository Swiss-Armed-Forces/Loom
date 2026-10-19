"""Fixtures for the banner suite.

The helpers these use live in `banner_text`, imported by name; fixtures stay here
because pytest wires them by directory.
"""

import stat
from io import StringIO

import pytest
from banner_text import WARNINGS

from loom_banner import render


@pytest.fixture
def paint():
    """Render renderables and hand back the raw text, escapes included."""

    def render_to_text(*renderables, colour: bool = True) -> str:
        stream = StringIO()
        console = render.console(stream, render.Colour(sgr=colour, palette=False))
        for renderable in renderables:
            console.print(renderable)
        return stream.getvalue()

    return render_to_text


@pytest.fixture
def box(tmp_path):
    """A box with every row this screen can carry, and a mark it can draw."""
    eyes = tmp_path / "loom-eyes"
    eyes.write_text("#!/bin/sh\nprintf '  XXXX  XXXX\\n'\n")
    eyes.chmod(eyes.stat().st_mode | stat.S_IEXEC)

    (tmp_path / "network.conf").write_text(
        "LOOM_WIRED_INTERFACE=loom0\nLOOM_SUBNET=10.160.227.0/24\n"
    )
    (tmp_path / "summary").write_text("Loom: ready.\n")
    (tmp_path / "state").write_text("armed\n")
    (tmp_path / "recovery").write_text("8euwj-4qkws-yvwk7-9rs7k-typst-jxae4\n")
    (tmp_path / "password").write_text("backspin.finisher.taste.unsmooth\n")

    return [
        "--tag",
        "1.5.0-rc6",
        "--platform",
        "NVIDIA DGX Spark",
        "--key-guard-action",
        "warn",
        "--portal-host",
        "portal.loom",
        "--portal-issues-certificates",
        "--eyes",
        str(eyes),
        "--network-conf",
        str(tmp_path / "network.conf"),
        "--ready-summary",
        str(tmp_path / "summary"),
        "--key-guard-state",
        str(tmp_path / "state"),
        "--key-guard-deadline",
        str(tmp_path / "missing"),
        "--recovery-passphrase",
        str(tmp_path / "recovery"),
        "--portal-password",
        str(tmp_path / "password"),
        "--warning",
        WARNINGS[0],
        "--warning",
        WARNINGS[1],
    ]
