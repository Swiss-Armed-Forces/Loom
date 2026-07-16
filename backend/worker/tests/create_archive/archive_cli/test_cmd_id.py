import json
import subprocess
import sys
from pathlib import Path

from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_helpers import (
    build_archive,
    build_archive_with_meta,
    simple_entries,
)

from worker.create_archive.tasks.archive_cli import CLI_ENTRYPOINT_FILENAME


def _get_storage_id(archive_dir: Path, file_name: str) -> str:
    for meta_path in (archive_dir / "files_index").glob("*.json"):
        data = json.loads(meta_path.read_text())
        name = data.get("full_name") or data.get("full_path") or data.get("short_name")
        if name == file_name:
            return data["storage_data"]["service_id"]
    raise KeyError(f"No index entry found for {file_name!r}")


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


class TestCliId:
    def test_resolves_with_files_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        storage_id = _get_storage_id(archive_dir, "docs/report.pdf")

        result = _run(archive_dir, ["id", f"files/{storage_id}"])

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout

    def test_resolves_without_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"notes.txt": b"hello"}),
            file_storage_service_inmemory,
        )
        storage_id = _get_storage_id(archive_dir, "notes.txt")

        result = _run(archive_dir, ["id", storage_id])

        assert result.returncode == 0
        assert "notes.txt" in result.stdout

    def test_resolves_thumbnail(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        meta = build_archive_with_meta(
            tmp_path, file_storage_service_inmemory, with_thumbnail=True
        )

        result = _run(meta.archive_dir, ["id", f"files/{meta.thumbnail_id}"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "thumbnail" in result.stdout

    def test_resolves_rendered_file(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        meta = build_archive_with_meta(
            tmp_path, file_storage_service_inmemory, with_image=True
        )

        result = _run(meta.archive_dir, ["id", f"files/{meta.image_data_id}"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "rendered:image_data" in result.stdout

    def test_not_found_errors(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["id", "files/nonexistent-id"])

        assert result.returncode != 0
        assert "no file found with id" in result.stderr
