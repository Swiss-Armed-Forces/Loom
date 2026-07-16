from worker.create_archive.tasks.archive_cli._utils import resolve_cwd


class TestResolveCwd:
    """Unit tests for resolve_cwd — a pure function, no filesystem needed."""

    def test_root_is_empty_string(self) -> None:
        assert resolve_cwd("", "") == ""

    def test_descend_one_level(self) -> None:
        assert resolve_cwd("", "docs") == "docs"

    def test_descend_two_levels(self) -> None:
        assert resolve_cwd("docs", "reports") == "docs/reports"

    def test_dotdot_goes_up(self) -> None:
        assert resolve_cwd("docs", "..") == ""

    def test_dotdot_from_root_stays_at_root(self) -> None:
        assert resolve_cwd("", "..") == ""

    def test_dotdot_beyond_root_clamps(self) -> None:
        assert resolve_cwd("docs", "../..") == ""

    def test_dot_stays(self) -> None:
        assert resolve_cwd("docs", ".") == "docs"

    def test_absolute_target(self) -> None:
        assert resolve_cwd("docs", "/images") == "images"

    def test_cd_root_slash(self) -> None:
        assert resolve_cwd("docs/reports", "/") == ""

    def test_mixed_dotdot_and_segment(self) -> None:
        assert resolve_cwd("a/b/c", "../../x") == "a/x"
