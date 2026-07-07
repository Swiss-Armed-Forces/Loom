"""Unit tests for cmd_mr_review and the post_review_comment helper."""

import json
from unittest.mock import MagicMock

import gitlab

from aitools.cmd_mr_review import _read_comment_files
from aitools.gitlab_api import post_review_comment
from aitools.models import ReviewComment

# ---------------------------------------------------------------------------
# _read_comment_files
# ---------------------------------------------------------------------------


class TestReadCommentFiles:
    def test_empty_directory(self, tmp_path):
        assert not _read_comment_files(str(tmp_path))

    def test_missing_directory(self, tmp_path):
        result = _read_comment_files(str(tmp_path / "nonexistent"))
        assert not result

    def test_parses_valid_json(self, tmp_path):
        data = {
            "file": "foo/bar.py",
            "line": 10,
            "severity": "High",
            "body": "This is wrong.",
            "context": "def foo(): pass",
        }
        (tmp_path / "001.json").write_text(json.dumps(data), encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert len(result) == 1
        assert result[0] == ReviewComment(
            file="foo/bar.py",
            line=10,
            severity="High",
            body="This is wrong.",
            context="def foo(): pass",
        )

    def test_strips_outer_markdown_fence(self, tmp_path):
        data = {
            "file": None,
            "line": None,
            "severity": "Low",
            "body": "ok",
            "context": None,
        }
        wrapped = "```json\n" + json.dumps(data) + "\n```"
        (tmp_path / "001.json").write_text(wrapped, encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert len(result) == 1
        assert result[0].body == "ok"

    def test_inner_fence_in_json_value_is_preserved(self, tmp_path):
        # A code snippet inside the JSON "context" field contains backtick fences.
        # Only the outer wrapper should be stripped, not the inner fence lines.
        inner_code = "```python\ndef foo(): pass\n```"
        data = {
            "file": "a.py",
            "line": 1,
            "severity": "Low",
            "body": "note",
            "context": inner_code,
        }
        wrapped = "```json\n" + json.dumps(data) + "\n```"
        (tmp_path / "001.json").write_text(wrapped, encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert len(result) == 1
        assert result[0].context == inner_code

    def test_skips_non_json_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
        assert not _read_comment_files(str(tmp_path))

    def test_skips_malformed_json_with_warning(self, tmp_path):
        (tmp_path / "001.json").write_text("{bad json", encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert not result

    def test_returns_sorted_by_filename(self, tmp_path):
        for i, body in [(3, "third"), (1, "first"), (2, "second")]:
            data = {
                "file": None,
                "line": None,
                "severity": "Low",
                "body": body,
                "context": None,
            }
            (tmp_path / f"00{i}.json").write_text(json.dumps(data), encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert [r.body for r in result] == ["first", "second", "third"]

    def test_missing_optional_keys_use_defaults(self, tmp_path):
        # Only "body" is required in practise; file/line/context default to None,
        # severity defaults to "Low".
        data = {"body": "minimal"}
        (tmp_path / "001.json").write_text(json.dumps(data), encoding="utf-8")
        result = _read_comment_files(str(tmp_path))
        assert len(result) == 1
        assert result[0].severity == "Low"
        assert result[0].file is None
        assert result[0].line is None
        assert result[0].context is None


# ---------------------------------------------------------------------------
# post_review_comment
# ---------------------------------------------------------------------------


def _make_mr(diff_refs: dict | None = None) -> MagicMock:
    """Return a mock MR with the given diff_refs."""
    mr = MagicMock()
    mr.diff_refs = diff_refs
    return mr


class TestPostReviewComment:
    def test_inline_comment_when_all_refs_present(self):
        diff_refs = {"base_sha": "aaa", "start_sha": "bbb", "head_sha": "ccc"}
        mr = _make_mr(diff_refs)
        comment = ReviewComment(
            file="src/foo.py", line=5, severity="High", body="Bug here.", context=None
        )

        post_review_comment(mr, comment)

        mr.discussions.create.assert_called_once()
        call_kwargs = mr.discussions.create.call_args[0][0]
        assert call_kwargs["body"] == "Bug here."
        position = call_kwargs["position"]
        assert position["new_path"] == "src/foo.py"
        assert position["old_path"] == "src/foo.py"
        assert position["new_line"] == 5
        assert position["position_type"] == "text"
        assert position["base_sha"] == "aaa"
        assert position["start_sha"] == "bbb"
        assert position["head_sha"] == "ccc"

    def test_falls_back_to_general_comment_on_gitlab_error(self):
        diff_refs = {"base_sha": "aaa", "start_sha": "bbb", "head_sha": "ccc"}
        mr = _make_mr(diff_refs)
        # First call raises GitlabError; second call (fallback) succeeds.
        mr.discussions.create.side_effect = [
            gitlab.exceptions.GitlabError("line not in diff"),
            MagicMock(),
        ]
        comment = ReviewComment(
            file="src/foo.py", line=5, severity="High", body="Bug here.", context=None
        )

        post_review_comment(mr, comment)

        assert mr.discussions.create.call_count == 2
        fallback_body = mr.discussions.create.call_args[0][0]["body"]
        assert "src/foo.py:5" in fallback_body
        assert "Bug here." in fallback_body

    def test_general_comment_when_no_file(self):
        mr = _make_mr({"base_sha": "aaa", "start_sha": "bbb", "head_sha": "ccc"})
        comment = ReviewComment(
            file=None, line=None, severity="Low", body="General note.", context=None
        )

        post_review_comment(mr, comment)

        mr.discussions.create.assert_called_once()
        body = mr.discussions.create.call_args[0][0]["body"]
        assert "General note." in body
        assert "(general)" in body
        assert "(Low)" in body

    def test_general_comment_when_diff_refs_missing(self):
        mr = _make_mr(diff_refs=None)
        comment = ReviewComment(
            file="src/foo.py", line=3, severity="Low", body="No refs.", context=None
        )

        post_review_comment(mr, comment)

        mr.discussions.create.assert_called_once()
        body = mr.discussions.create.call_args[0][0]["body"]
        # Falls back to a general comment because diff_refs is None
        assert "No refs." in body

    def test_general_comment_when_line_missing(self):
        diff_refs = {"base_sha": "aaa", "start_sha": "bbb", "head_sha": "ccc"}
        mr = _make_mr(diff_refs)
        comment = ReviewComment(
            file="src/foo.py", line=None, severity="Low", body="No line.", context=None
        )

        post_review_comment(mr, comment)

        mr.discussions.create.assert_called_once()
        # No position → general comment path
        call_arg = mr.discussions.create.call_args[0][0]
        assert "position" not in call_arg
        body = call_arg["body"]
        assert "src/foo.py" in body
        assert ":None" not in body
