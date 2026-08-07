import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from common.file.file_repository import File, FilePurePath
from common.services.lazybytes_service import LazyBytes
from create_archive.archive_helpers import ArchiveEntry

from worker.create_archive.tasks.archive_cli import CLI_ENTRYPOINT_FILENAME


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


def _make_entry(name: str, **kwargs) -> ArchiveEntry:
    return ArchiveEntry(
        file=File(
            full_name=FilePurePath(name),
            source="test",
            sha256="abc",
            size=4,
            storage_data=LazyBytes(service_id=uuid4()),
            **kwargs,
        ),
        content=b"data",
    )
