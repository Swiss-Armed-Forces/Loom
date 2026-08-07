import argparse
import io
import re
import sqlite3
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from worker.create_archive.tasks.archive_cli import (
    SHELL_INDEX_FILENAME,
    cmd_shell,
)
from worker.create_archive.tasks.archive_cli._db import SHELL_DB_SCHEMA


class TestShellCrashRecovery:
    """Shell REPL continues after unexpected exceptions in dispatched commands."""

    def _make_db(self, tmp_path: Path) -> sqlite3.Connection:
        db = sqlite3.connect(str(tmp_path / SHELL_INDEX_FILENAME))
        db.executescript(SHELL_DB_SCHEMA)
        return db

    def _closed_db(self, tmp_path: Path) -> sqlite3.Connection:
        """Return a closed connection so any DB call raises ProgrammingError."""
        db = self._make_db(tmp_path)
        db.close()
        return db

    def test_crash_does_not_raise(self, tmp_path: Path) -> None:
        """cmd_shell returns normally even when _dispatch raises."""
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )
        # No exception raised — reaching here means the shell recovered

    def test_crash_writes_stderr_message(self, tmp_path: Path) -> None:
        """Stderr receives the exception type and message on crash."""
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        err = io.StringIO()
        with redirect_stderr(err):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )

        stderr_text = err.getvalue()
        assert "ProgrammingError" in stderr_text
        assert "unexpected error" in stderr_text.lower()

    def test_crash_writes_log_file(self, tmp_path: Path) -> None:
        """Crash log file is created and contains diagnostic info."""
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        with redirect_stderr(io.StringIO()):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )

        assert crash_log.exists()
        content = crash_log.read_text(encoding="utf-8")
        assert re.search(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]", content)
        assert "Command: ls" in content
        assert "ProgrammingError" in content
        assert "Traceback" in content

    def test_shell_continues_after_crash(self, tmp_path: Path) -> None:
        """A second command executes normally after a crash."""
        # the closed DB will crash on 'ls' but 'exit' is handled before _dispatch.
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )

        # The 'exit' command ran (it's handled before _dispatch) → loop exited cleanly
        assert crash_log.exists()

    def test_crash_log_appended_on_multiple_crashes(self, tmp_path: Path) -> None:
        """Multiple crashes produce multiple separator blocks in the log."""
        commands = iter(["ls", "ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        with redirect_stderr(io.StringIO()):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )

        content = crash_log.read_text(encoding="utf-8")
        separator = "=" * 72
        assert content.count(separator) == 4  # two entries × 2 separators each

    def test_no_crash_log_when_crash_log_file_is_none(self, tmp_path: Path) -> None:
        """Shell still recovers when crash_log_file=None; no file is written."""
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        with redirect_stderr(io.StringIO()):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=None,
                input_fn=lambda _: next(commands),
            )

        assert not crash_log.exists()

    def test_crash_log_path_in_stderr(self, tmp_path: Path) -> None:
        """Stderr includes the path to the crash log file."""
        commands = iter(["ls", "exit"])
        crash_log = tmp_path / ".loom_crash.log"

        err = io.StringIO()
        with redirect_stderr(err):
            cmd_shell(
                argparse.Namespace(),
                db=self._closed_db(tmp_path),
                history_file=None,
                crash_log_file=crash_log,
                input_fn=lambda _: next(commands),
            )

        assert str(crash_log) in err.getvalue()
