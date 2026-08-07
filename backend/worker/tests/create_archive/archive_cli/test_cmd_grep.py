from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_cli.helpers import _make_entry, _run
from create_archive.archive_helpers import build_archive, simple_entries


class TestCliGrep:
    def test_finds_match_shows_field_and_value(
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
        assert "important_doc.txt [full_name]: important_doc.txt" in result.stdout

    def test_keys_not_searched(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        # "full_name" is a JSON key — it should only match if also present as a value
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        # "full_name" is a key; searching for it should not match (it's not a value)
        result = _run(archive_dir, ["grep", "^full_name$"])

        assert result.returncode != 0

    def test_no_match_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "xyzzy_no_match"])

        assert result.returncode != 0
        assert result.stdout == ""

    def test_case_sensitive_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "IMPORTANT"])

        assert result.returncode != 0

    def test_ignore_case_flag(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"important_doc.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "-i", "IMPORTANT"])

        assert result.returncode == 0
        assert "important_doc.txt" in result.stdout

    def test_files_with_matches_flag(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "-l", "report"])

        assert result.returncode == 0
        assert result.stdout.strip() == "test/report.pdf"
        assert "[" not in result.stdout

    def test_regex_pattern(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"pdf", "image.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", r"report\.(pdf|txt)"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "image.jpg" not in result.stdout

    def test_invalid_regex_exits_with_error(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "[unclosed"])

        assert result.returncode == 2
        assert "invalid pattern" in result.stderr

    def test_help_describes_usage(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "--help"])

        assert result.returncode == 0
        assert "field.path" in result.stdout

    def test_file_arg_restricts_search(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"alpha.txt": b"data", "beta.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "test", "alpha.txt"])

        assert result.returncode == 0
        assert "alpha.txt" in result.stdout
        assert "beta.txt" not in result.stdout

    def test_file_arg_no_match_in_file_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"alpha.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "xyzzy_no_match", "alpha.txt"])

        assert result.returncode != 0

    def test_file_arg_nonexistent_file_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"alpha.txt": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "test", "nonexistent.txt"])

        assert result.returncode != 0

    def test_multiple_file_args(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {"alpha.txt": b"data", "beta.txt": b"data", "gamma.txt": b"data"}
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["grep", "test", "alpha.txt", "beta.txt"])

        assert result.returncode == 0
        assert "alpha.txt" in result.stdout
        assert "beta.txt" in result.stdout
        assert "gamma.txt" not in result.stdout

    def test_field_filter_restricts_search(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        # "hello" appears only in content, not in full_name
        entries = [_make_entry("doc.txt", content="hello world")]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)

        # Searching content field finds the match
        result_content = _run(archive_dir, ["grep", "hello", "-f", "content"])
        assert result_content.returncode == 0
        assert "doc.txt" in result_content.stdout

        # Searching a different field does not find it
        result_other = _run(archive_dir, ["grep", "hello", "-f", "summary"])
        assert result_other.returncode != 0

    def test_field_filter_multiple_fields_or_semantics(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [
            _make_entry("doc.txt", content="hello world", summary="hello summary")
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)

        # Either field matching is sufficient
        result = _run(archive_dir, ["grep", "hello", "-f", "content", "-f", "summary"])
        assert result.returncode == 0
        assert "content" in result.stdout
        assert "summary" in result.stdout

    def test_field_filter_with_files_with_matches(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [_make_entry("doc.txt", content="hello world")]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)

        result = _run(archive_dir, ["grep", "hello", "-f", "content", "-l"])
        assert result.returncode == 0
        assert result.stdout.strip() == "test/doc.txt"
        assert "[" not in result.stdout
