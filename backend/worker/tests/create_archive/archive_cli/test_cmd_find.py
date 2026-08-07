from pathlib import Path

from common.file.file_repository import TranslatedLanguage
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_cli.helpers import _make_entry, _run
from create_archive.archive_helpers import build_archive, simple_entries


class TestCliFind:
    def test_no_filter_lists_all_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"alpha.txt": b"data", "beta.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["find"])

        assert result.returncode == 0
        assert "alpha.txt" in result.stdout
        assert "beta.pdf" in result.stdout

    def test_name_filter(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data", "image.jpg": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["find", "-name", "*.pdf"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "image.jpg" not in result.stdout

    def test_iname_filter_case_insensitive(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"Report.PDF": b"data", "image.jpg": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["find", "-iname", "*.pdf"])

        assert result.returncode == 0
        assert "Report.PDF" in result.stdout
        assert "image.jpg" not in result.stdout

    def test_no_match_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"image.jpg": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["find", "-name", "*.pdf"])

        assert result.returncode != 0
        assert result.stdout == ""

    def test_attr_filters_by_presence(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [
            _make_entry("with_summary.txt", summary="AI generated summary"),
            _make_entry("no_summary.txt"),
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        result = _run(archive_dir, ["find", "-attr", "summary"])

        assert result.returncode == 0
        assert "with_summary.txt" in result.stdout
        assert "no_summary.txt" not in result.stdout

    def test_attr_nested_field(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        # translations is a list of nested objects — test filtering on the whole subtree
        entries = [
            _make_entry(
                "with_translation.pdf",
                translations=[
                    TranslatedLanguage(confidence=0.9, language="de", text="Hallo")
                ],
            ),
            _make_entry("no_translation.pdf"),
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        result = _run(archive_dir, ["find", "-attr", "translations"])

        assert result.returncode == 0
        assert "with_translation.pdf" in result.stdout
        assert "no_translation.pdf" not in result.stdout

    def test_attr_no_match_exits_nonzero(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["find", "-attr", "summary"])

        assert result.returncode != 0
        assert result.stdout == ""

    def test_attr_multiple_and_semantics(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [
            _make_entry(
                "both.txt",
                summary="some summary",
                magic_file_type="text/plain",
            ),
            _make_entry("summary_only.txt", summary="some summary"),
            _make_entry("neither.txt"),
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        result = _run(
            archive_dir, ["find", "-attr", "summary", "-attr", "magic_file_type"]
        )

        assert result.returncode == 0
        assert "both.txt" in result.stdout
        assert "summary_only.txt" not in result.stdout
        assert "neither.txt" not in result.stdout

    def test_attr_composable_with_name(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [
            _make_entry("report.pdf", summary="some summary"),
            _make_entry("report.txt", summary="some summary"),
            _make_entry("image.pdf"),
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        result = _run(archive_dir, ["find", "-name", "*.pdf", "-attr", "summary"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "report.txt" not in result.stdout
        assert "image.pdf" not in result.stdout
