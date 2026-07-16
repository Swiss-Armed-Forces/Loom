import argparse
from pathlib import Path
from uuid import uuid4

import pytest
from common.file.file_repository import File, FilePurePath
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    LazyBytes,
)
from create_archive.archive_helpers import ArchiveEntry, build_archive

from worker.create_archive.tasks.archive_cli._cmd_extract import cmd_extract
from worker.create_archive.tasks.archive_cli._cmd_grep import cmd_grep
from worker.create_archive.tasks.archive_cli._cmd_id import cmd_id
from worker.create_archive.tasks.archive_cli._cmd_info import cmd_info
from worker.create_archive.tasks.archive_cli._cmd_ls import cmd_ls
from worker.create_archive.tasks.archive_cli._cmd_tree import cmd_tree
from worker.create_archive.tasks.archive_cli._db import open_shell_db

_N_ENTRIES = 50
_CONTENT_SIZE = 2 * 1024 * 1024  # 2 MiB per entry → 100 MiB total on disk


class TestMemory:
    @pytest.fixture()
    def large_archive_dir(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> Path:
        entries = [
            ArchiveEntry(
                file=File(
                    full_name=FilePurePath(f"docs/file_{i:04d}.txt"),
                    source="test",
                    sha256="abc",
                    size=4,
                    storage_data=LazyBytes(service_id=uuid4()),
                    content="x" * _CONTENT_SIZE,
                ),
                content=b"data",
            )
            for i in range(_N_ENTRIES)
        ]
        return build_archive(tmp_path, entries, file_storage_service_inmemory)

    @pytest.mark.limit_memory("30 MB")
    def test_ls_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_ls queries the DB for path stubs (no JSON reads), so only path strings
        # are live — well under the limit even for 100 MB of content in the index.
        db = open_shell_db(large_archive_dir)
        cmd_ls(
            argparse.Namespace(path="docs/file_0001.txt"),
            db=db,
        )

    @pytest.mark.limit_memory("20 MB")
    def test_tree_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_tree only reads path-component strings from the children table; no JSON reads.
        db = open_shell_db(large_archive_dir)
        cmd_tree(
            argparse.Namespace(),
            db=db,
        )

    @pytest.mark.limit_memory("30 MB")
    def test_info_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_info loads exactly one JSON file; all other entries are never read.
        db = open_shell_db(large_archive_dir)
        cmd_info(
            argparse.Namespace(name="docs/file_0001.txt", json=False, field=None),
            db=db,
            index_dir=large_archive_dir / "files_index",
            files_dir=large_archive_dir / "files",
        )

    @pytest.mark.limit_memory("20 MB")
    def test_grep_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_grep reads one JSON file at a time and discards it; no accumulation.
        db = open_shell_db(large_archive_dir)
        cmd_grep(
            argparse.Namespace(
                pattern="file_0001",
                ignore_case=False,
                files_with_matches=False,
            ),
            db=db,
            index_dir=large_archive_dir / "files_index",
        )

    @pytest.mark.limit_memory("20 MB")
    def test_id_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_id queries storage table by storage_id; no JSON reads at all.
        db = open_shell_db(large_archive_dir)
        with pytest.raises(SystemExit):
            cmd_id(
                argparse.Namespace(file_ref="nonexistent-id"),
                db=db,
            )

    @pytest.mark.limit_memory("30 MB")
    def test_extract_does_not_load_entries_twice(
        self, large_archive_dir: Path, tmp_path: Path
    ) -> None:
        # cmd_extract queries DB stubs for path resolution (no JSON accumulation)
        # and only loads JSON for the matched file, so peak memory stays low.
        db = open_shell_db(large_archive_dir)
        cmd_extract(
            argparse.Namespace(
                members=["docs/file_0001.txt"],
                directory=str(tmp_path / "out"),
                no_recursion=False,
                exclude=[],
                no_thumbnails=False,
                no_rendered=False,
                no_index=False,
                no_meta=False,
            ),
            db=db,
            index_dir=large_archive_dir / "files_index",
            files_dir=large_archive_dir / "files",
        )
