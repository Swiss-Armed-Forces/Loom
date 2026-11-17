import io
import json
import os
import pty
import re
import subprocess
import sys
from pathlib import Path

import pytest
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_cli.helpers import _run
from create_archive.archive_helpers import build_archive, simple_entries

from worker.create_archive.tasks.archive_cli import CLI_ENTRYPOINT_FILENAME
from worker.create_archive.tasks.archive_cli._color import (
    COLOR_ALWAYS,
    COLOR_AUTO,
    COLOR_NEVER,
    Colors,
    should_colorize,
)

ESC = "\033"


class _Stream(io.StringIO):
    """A stream that reports whatever TTY-ness the test needs."""

    def __init__(self, *, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


class TestShouldColorize:
    @pytest.mark.parametrize(
        ("when", "tty", "env", "expected"),
        [
            # 'auto' follows the stream: a pipe stays plain so scripts keep working.
            (COLOR_AUTO, False, {}, False),
            (COLOR_AUTO, True, {}, True),
            # An explicit choice overrides the stream in both directions.
            (COLOR_ALWAYS, False, {}, True),
            (COLOR_NEVER, True, {}, False),
            # The environment only speaks for 'auto'.
            (COLOR_AUTO, True, {"NO_COLOR": "1"}, False),
            (COLOR_AUTO, True, {"NO_COLOR": ""}, True),
            (COLOR_AUTO, True, {"TERM": "dumb"}, False),
            (COLOR_ALWAYS, True, {"NO_COLOR": "1"}, True),
            # An unset mode is 'auto'.
            (None, False, {}, False),
        ],
    )
    def test_decision(
        self, when: str | None, tty: bool, env: dict[str, str], expected: bool
    ) -> None:
        assert should_colorize(when, stream=_Stream(tty=tty), env=env) is expected


class TestColors:
    def test_disabled_returns_text_untouched(self) -> None:
        colors = Colors(enabled=False)

        assert colors.path("a/b/c.pdf") == "a/b/c.pdf"
        assert colors.match("x") == "x"
        assert colors.highlight(re.compile("x"), "axb") == "axb"

    def test_path_colours_only_the_directory_part(self) -> None:
        painted = Colors(enabled=True).path("reports/2024/q1.pdf")

        assert painted == f"{ESC}[1;34mreports/2024/{ESC}[0mq1.pdf"

    def test_bare_name_has_no_directory_to_colour(self) -> None:
        assert Colors(enabled=True).path("q1.pdf") == "q1.pdf"

    def test_highlight_leaves_zero_width_matches_alone(self) -> None:
        # A pattern that matches the empty string would otherwise wrap nothing
        # in escape sequences at every position.
        assert Colors(enabled=True).highlight(re.compile("x*"), "abc") == "abc"

    def test_json_text_matches_json_dumps_when_disabled(self) -> None:
        data = {"name": "a.pdf", "size": 4, "tags": ["x"], "ok": True}

        assert Colors(enabled=False).json_text(data) == json.dumps(data, indent=2)

    def test_json_text_keeps_its_data_when_coloured(self) -> None:
        data = {"name": "a.pdf", "size": 4}
        painted = Colors(enabled=True).json_text(data)

        assert ESC in painted
        assert json.loads(re.sub(r"\033\[[0-9;]*m", "", painted)) == data

    def test_prompt_brackets_sequences_as_non_printing(self) -> None:
        # readline miscounts the cursor column unless the escapes sit inside
        # \001 ... \002.
        painted = Colors(enabled=True).prompt("loom:/")

        assert painted.startswith("\001")
        assert painted.endswith("\002")
        assert "loom:/" in painted


class TestCliColorOption:
    def test_no_colour_when_output_is_piped(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "important"])

        assert result.returncode == 0
        assert ESC not in result.stdout

    def test_color_always_highlights_the_match(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "--color=always", "important"])

        assert result.returncode == 0
        assert f"{ESC}[1;31mimportant{ESC}[0m" in result.stdout

    def test_colour_turns_itself_on_for_a_terminal(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        controller, follower = pty.openpty()
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(archive_dir / CLI_ENTRYPOINT_FILENAME),
                    "grep",
                    "important",
                ],
                stdout=follower,
                stderr=subprocess.DEVNULL,
                cwd=archive_dir,
                check=True,
            )
            os.close(follower)
            output = os.read(controller, 65536).decode()
        finally:
            os.close(controller)

        assert ESC in output

    def test_color_before_the_subcommand_is_honoured(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["--color=always", "grep", "important"])

        assert result.returncode == 0
        assert ESC in result.stdout
