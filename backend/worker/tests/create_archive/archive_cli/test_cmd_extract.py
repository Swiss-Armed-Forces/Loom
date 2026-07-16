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


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_ENTRYPOINT_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
        cwd=archive_dir,
    )


def _make_archive_with_meta(
    tmp_path: Path,
    file_storage_service: InMemoryFileStorageLazyBytesService,
) -> Path:
    return build_archive_with_meta(
        tmp_path, file_storage_service, with_thumbnail=True, with_image=True
    ).archive_dir


class TestCliExtract:
    def test_extracts_all_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.txt": b"a", "docs/b.txt": b"b"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest)])

        assert result.returncode == 0
        assert (dest / "test" / "docs" / "a.txt" / "a.txt").read_bytes() == b"a"
        assert (dest / "test" / "docs" / "b.txt" / "b.txt").read_bytes() == b"b"

    def test_extracts_single_member(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"pdf content"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        assert (
            dest / "test" / "report.pdf" / "report.pdf"
        ).read_bytes() == b"pdf content"

    def test_extracts_to_cwd_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"note.txt": b"hi"}),
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["x", "note.txt"])

        assert result.returncode == 0

    def test_extracts_nested_preserving_hierarchy(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"deep/path/notes.txt": b"hello"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "notes.txt"])

        assert result.returncode == 0
        assert (
            dest / "test" / "deep" / "path" / "notes.txt" / "notes.txt"
        ).read_bytes() == b"hello"

    def test_glob_pattern_extracts_matching_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.txt": b"a", "docs/b.md": b"b"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "*.txt"])

        assert result.returncode == 0
        assert (dest / "test" / "docs" / "a.txt" / "a.txt").read_bytes() == b"a"
        assert not (dest / "test" / "docs" / "b.md").exists()

    def test_multiple_explicit_members(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"a.txt": b"a", "b.txt": b"b", "c.md": b"c"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "a.txt", "b.txt"])

        assert result.returncode == 0
        assert (dest / "test" / "a.txt" / "a.txt").read_bytes() == b"a"
        assert (dest / "test" / "b.txt" / "b.txt").read_bytes() == b"b"
        assert not (dest / "test" / "c.md").exists()

    def test_dir_like_recursive_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"doc.pdf": b"pdf", "doc.pdf/image.png": b"img"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "doc.pdf"])

        assert result.returncode == 0
        assert (dest / "test" / "doc.pdf" / "doc.pdf").read_bytes() == b"pdf"
        assert (
            dest / "test" / "doc.pdf" / "image.png" / "image.png"
        ).read_bytes() == b"img"

    def test_no_recursion_extracts_only_matched_entry(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"doc.pdf": b"pdf", "doc.pdf/image.png": b"img"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--no-recursion", "doc.pdf"])

        assert result.returncode == 0
        assert (dest / "test" / "doc.pdf" / "doc.pdf").read_bytes() == b"pdf"
        assert not (dest / "test" / "doc.pdf" / "image.png").exists()

    def test_exclude_filters_output(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"a.txt": b"a", "b.txt": b"b", "c.md": b"c"}),
            file_storage_service_inmemory,
        )
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--exclude=*.txt"])

        assert result.returncode == 0
        assert not (dest / "test" / "a.txt").exists()
        assert not (dest / "test" / "b.txt").exists()
        assert (dest / "test" / "c.md" / "c.md").read_bytes() == b"c"

    def test_no_matches_errors(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"pdf"}),
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["x", "nonexistent.txt"])

        assert result.returncode != 0
        assert "no file found matching" in result.stderr

    def test_extracts_thumbnail_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        assert (dest / "test" / "report.pdf" / "thumbnail.png").exists()

    def test_extracts_rendered_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        assert (dest / "test" / "report.pdf" / "rendered-image_data.png").exists()

    def test_extracts_index_json_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        index_path = dest / "test" / "report.pdf" / "index.json"
        assert index_path.exists()
        data = json.loads(index_path.read_text())
        assert data.get("full_name") == "report.pdf"

    def test_no_thumbnails_suppresses_thumbnail(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(
            archive_dir, ["x", "-C", str(dest), "--no-thumbnails", "report.pdf"]
        )

        assert result.returncode == 0
        assert not (dest / "test" / "report.pdf" / "thumbnail.png").exists()
        assert (dest / "test" / "report.pdf" / "report.pdf").exists()

    def test_no_rendered_suppresses_rendered(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(
            archive_dir, ["x", "-C", str(dest), "--no-rendered", "report.pdf"]
        )

        assert result.returncode == 0
        assert not (dest / "test" / "report.pdf" / "rendered-image_data.png").exists()
        assert (dest / "test" / "report.pdf" / "report.pdf").exists()

    def test_no_index_suppresses_index_json(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--no-index", "report.pdf"])

        assert result.returncode == 0
        assert not (dest / "test" / "report.pdf" / "index.json").exists()
        assert (dest / "test" / "report.pdf" / "report.pdf").exists()

    def test_no_meta_suppresses_all(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--no-meta", "report.pdf"])

        assert result.returncode == 0
        entry_dir = dest / "test" / "report.pdf"
        assert not (entry_dir / "thumbnail.png").exists()
        assert not (entry_dir / "rendered-image_data.png").exists()
        assert not (entry_dir / "index.json").exists()
        assert (entry_dir / "report.pdf").exists()
