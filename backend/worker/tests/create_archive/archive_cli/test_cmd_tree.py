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


class TestCliTree:
    def test_shows_hierarchy(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"pdf", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["tree"])

        assert result.returncode == 0
        assert "docs" in result.stdout
        assert "images" in result.stdout
        assert "report.pdf" in result.stdout
        assert "photo.jpg" in result.stdout
