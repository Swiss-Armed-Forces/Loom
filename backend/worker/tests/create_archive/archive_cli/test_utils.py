from worker.create_archive.tasks.archive_cli._utils import (
    _collapse_field_ranges,
    resolve_cwd,
    sanitize_win_path_component,
)


class TestCollapseFieldRanges:
    def test_no_arrays_unchanged(self) -> None:
        assert _collapse_field_ranges(["name", "size"]) == ["name", "size"]

    def test_single_element_array_no_range(self) -> None:
        assert _collapse_field_ranges(["items[0].name"]) == ["items[0].name"]

    def test_flat_array_collapsed(self) -> None:
        fields = ["items[0].name", "items[1].name", "items[2].name"]
        assert _collapse_field_ranges(fields) == ["items[0..2].name"]

    def test_nested_arrays_both_collapsed(self) -> None:
        fields = [
            "tasks[0].succeeded[0].task_id",
            "tasks[0].succeeded[1].task_id",
            "tasks[1].succeeded[0].task_id",
            "tasks[1].succeeded[1].task_id",
        ]
        assert _collapse_field_ranges(fields) == ["tasks[0..1].succeeded[0..1].task_id"]

    def test_sibling_fields_preserved(self) -> None:
        fields = [
            "tasks[0].name",
            "tasks[1].name",
            "tasks[0].count",
            "tasks[1].count",
        ]
        assert _collapse_field_ranges(fields) == [
            "tasks[0..1].name",
            "tasks[0..1].count",
        ]

    def test_mixed_array_sizes_per_element(self) -> None:
        # tasks[0] has 2 succeeded, tasks[1] has only 1 — range covers global max
        fields = [
            "tasks[0].succeeded[0].id",
            "tasks[0].succeeded[1].id",
            "tasks[1].succeeded[0].id",
        ]
        assert _collapse_field_ranges(fields) == ["tasks[0..1].succeeded[0..1].id"]

    def test_insertion_order_preserved(self) -> None:
        fields = ["b[0]", "a[0]", "b[1]", "a[1]"]
        assert _collapse_field_ranges(fields) == ["b[0..1]", "a[0..1]"]


class TestSanitizeWinPathComponentForbiddenChars:
    def test_colon(self) -> None:
        assert sanitize_win_path_component("report:.txt") == "report_.txt"

    def test_lt(self) -> None:
        assert sanitize_win_path_component("a<b") == "a_b"

    def test_gt(self) -> None:
        assert sanitize_win_path_component("a>b") == "a_b"

    def test_dquote(self) -> None:
        assert sanitize_win_path_component('a"b') == "a_b"

    def test_pipe(self) -> None:
        assert sanitize_win_path_component("a|b") == "a_b"

    def test_question(self) -> None:
        assert sanitize_win_path_component("a?b") == "a_b"

    def test_star(self) -> None:
        assert sanitize_win_path_component("a*b") == "a_b"

    def test_backslash(self) -> None:
        assert sanitize_win_path_component("a\\b") == "a_b"

    def test_multiple(self) -> None:
        assert sanitize_win_path_component("a<b>c.txt") == "a_b_c.txt"


class TestSanitizeWinPathComponentReservedAndEdge:
    def test_reserved_nul(self) -> None:
        assert sanitize_win_path_component("NUL") == "_NUL"

    def test_reserved_nul_with_ext(self) -> None:
        assert sanitize_win_path_component("NUL.txt") == "_NUL.txt"

    def test_reserved_nul_lowercase(self) -> None:
        assert sanitize_win_path_component("nul.pdf") == "_nul.pdf"

    def test_reserved_com1(self) -> None:
        assert sanitize_win_path_component("COM1.log") == "_COM1.log"

    def test_reserved_lpt9_lowercase(self) -> None:
        assert sanitize_win_path_component("lpt9") == "_lpt9"

    def test_trailing_dot(self) -> None:
        assert sanitize_win_path_component("foo.") == "foo"

    def test_multiple_trailing_dots(self) -> None:
        assert sanitize_win_path_component("foo...") == "foo"

    def test_trailing_space(self) -> None:
        assert sanitize_win_path_component("foo ") == "foo"

    def test_combined_nul_trailing_dot(self) -> None:
        # strip trailing dot first → "NUL", then detect reserved
        assert sanitize_win_path_component("NUL.") == "_NUL"

    def test_normal_txt(self) -> None:
        assert sanitize_win_path_component("normal.txt") == "normal.txt"

    def test_normal_pdf(self) -> None:
        assert sanitize_win_path_component("report.pdf") == "report.pdf"

    def test_all_dots_becomes_underscore(self) -> None:
        assert sanitize_win_path_component("...") == "_"

    def test_non_reserved_partial_match(self) -> None:
        # "CONSOLE" is not a reserved name (only "CON" is)
        assert sanitize_win_path_component("CONSOLE.txt") == "CONSOLE.txt"


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
