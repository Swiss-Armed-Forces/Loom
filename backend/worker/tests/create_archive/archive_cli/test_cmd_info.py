import json
import subprocess
import sys
from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_helpers import build_archive, simple_entries

from worker.create_archive.tasks.archive_cli import CLI_ENTRYPOINT_FILENAME


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class TestCliInfo:
    def test_prints_human_readable(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "report.pdf"])

        assert result.returncode == 0
        assert "name:" in result.stdout
        assert "report.pdf" in result.stdout
        assert "file:" in result.stdout

    def test_json_flag_prints_metadata(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "--json", "report.pdf"])

        assert result.returncode == 0

        parsed = json.loads(result.stdout)
        assert parsed["full_name"] == "report.pdf"

    def test_glob_pattern_single_match(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "*.pdf"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_ambiguous_suffix_match_errors(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "src/report.pdf": b"a",
                    "docs/report.pdf": b"b",
                }
            ),
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["info", "report.pdf"])

        assert result.returncode != 0
        assert "ambiguous name" in result.stderr
        assert "src/report.pdf" in result.stderr
        assert "docs/report.pdf" in result.stderr


class TestCliInfoField:
    def test_info_prints_fields_section(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "report.pdf"])

        assert result.returncode == 0
        assert "fields:" in result.stdout
        assert "  storage_data.service_id" in result.stdout

    def test_info_field_prints_leaf_value(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "report.pdf", "full_name"])

        assert result.returncode == 0
        assert result.stdout.strip() == "report.pdf"

    def test_info_field_prints_subtree(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "report.pdf", "storage_data"])

        assert result.returncode == 0
        assert "storage_data.service_id:" in result.stdout

    def test_info_field_not_found_exits_1(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["info", "report.pdf", "nonexistent"])

        assert result.returncode == 1
        assert "nonexistent" in result.stderr
