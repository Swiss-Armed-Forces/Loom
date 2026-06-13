import argparse
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from common.file.file_repository import File, FilePurePath, RenderedFile
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    LazyBytes,
)

import worker.create_archive.tasks.archive_format as archive_fmt
from worker.create_archive.tasks.archive_format import CLI_FILENAME
from worker.utils.archive import ArchiveEntry, build_archive, simple_entries


def _get_storage_id(archive_dir: Path, file_name: str) -> str:
    for meta_path in (archive_dir / "files_index").glob("*.json"):
        data = json.loads(meta_path.read_text())
        name = data.get("full_name") or data.get("full_path") or data.get("short_name")
        if name == file_name:
            return data["storage_data"]["service_id"]
    raise KeyError(f"No index entry found for {file_name!r}")


def _run(archive_dir: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_FILENAME)] + args,
        capture_output=True,
        text=True,
        check=False,
    )


class TestCliLs:
    def test_lists_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"pdf"}),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls"])

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout

    def test_empty_archive(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path, simple_entries({}), file_storage_service_inmemory
        )
        result = _run(archive_dir, ["ls"])

        assert result.returncode != 0
        assert "no file found matching" in result.stderr

    def test_glob_filters_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "docs/report.pdf": b"pdf",
                    "docs/notes.txt": b"txt",
                    "images/photo.jpg": b"img",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "docs/*.txt"])

        assert result.returncode == 0
        assert "docs/notes.txt" in result.stdout
        assert "docs/report.pdf" not in result.stdout
        assert "images/photo.jpg" not in result.stdout

    def test_glob_matches_across_directories(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "a/foo.txt": b"a",
                    "b/bar.txt": b"b",
                    "c/img.png": b"c",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "*.txt"])

        assert result.returncode == 0
        assert "a/foo.txt" in result.stdout
        assert "b/bar.txt" in result.stdout
        assert "c/img.png" not in result.stdout

    def test_directory_prefix(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries(
                {
                    "docs/report.pdf": b"pdf",
                    "images/photo.jpg": b"img",
                }
            ),
            file_storage_service_inmemory,
        )
        result = _run(archive_dir, ["ls", "docs/"])

        assert result.returncode == 0
        assert "docs/report.pdf" in result.stdout
        assert "images/photo.jpg" not in result.stdout


def _make_archive_with_meta(
    tmp_path: Path,
    file_storage_service: InMemoryFileStorageLazyBytesService,
) -> Path:
    return build_archive(
        tmp_path,
        [
            ArchiveEntry(
                file=File(
                    full_name=FilePurePath("report.pdf"),
                    source="test",
                    sha256="abc",
                    size=3,
                    storage_data=LazyBytes(service_id=uuid4()),
                    thumbnail_data=LazyBytes(service_id=uuid4()),
                    rendered_file=RenderedFile(
                        image_data=LazyBytes(service_id=uuid4())
                    ),
                ),
                content=b"main",
            )
        ],
        file_storage_service,
    )


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
        assert (dest / "docs" / "a.txt" / "a.txt").read_bytes() == b"a"
        assert (dest / "docs" / "b.txt" / "b.txt").read_bytes() == b"b"

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
        assert (dest / "report.pdf" / "report.pdf").read_bytes() == b"pdf content"

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
            dest / "deep" / "path" / "notes.txt" / "notes.txt"
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
        assert (dest / "docs" / "a.txt" / "a.txt").read_bytes() == b"a"
        assert not (dest / "docs" / "b.md").exists()

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
        assert (dest / "a.txt" / "a.txt").read_bytes() == b"a"
        assert (dest / "b.txt" / "b.txt").read_bytes() == b"b"
        assert not (dest / "c.md").exists()

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
        assert (dest / "doc.pdf" / "doc.pdf").read_bytes() == b"pdf"
        assert (dest / "doc.pdf" / "image.png" / "image.png").read_bytes() == b"img"

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
        assert (dest / "doc.pdf" / "doc.pdf").read_bytes() == b"pdf"
        assert not (dest / "doc.pdf" / "image.png").exists()

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
        assert not (dest / "a.txt").exists()
        assert not (dest / "b.txt").exists()
        assert (dest / "c.md" / "c.md").read_bytes() == b"c"

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
        assert (dest / "report.pdf" / "thumbnail.png").exists()

    def test_extracts_rendered_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        assert (dest / "report.pdf" / "rendered-image_data.png").exists()

    def test_extracts_index_json_by_default(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "report.pdf"])

        assert result.returncode == 0
        index_path = dest / "report.pdf" / "index.json"
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
        assert not (dest / "report.pdf" / "thumbnail.png").exists()
        assert (dest / "report.pdf" / "report.pdf").exists()

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
        assert not (dest / "report.pdf" / "rendered-image_data.png").exists()
        assert (dest / "report.pdf" / "report.pdf").exists()

    def test_no_index_suppresses_index_json(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--no-index", "report.pdf"])

        assert result.returncode == 0
        assert not (dest / "report.pdf" / "index.json").exists()
        assert (dest / "report.pdf" / "report.pdf").exists()

    def test_no_meta_suppresses_all(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = _make_archive_with_meta(tmp_path, file_storage_service_inmemory)
        dest = tmp_path / "out"

        result = _run(archive_dir, ["x", "-C", str(dest), "--no-meta", "report.pdf"])

        assert result.returncode == 0
        entry_dir = dest / "report.pdf"
        assert not (entry_dir / "thumbnail.png").exists()
        assert not (entry_dir / "rendered-image_data.png").exists()
        assert not (entry_dir / "index.json").exists()
        assert (entry_dir / "report.pdf").exists()


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
        assert result.stdout.strip() == "report.pdf"
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
        thumbnail_id = uuid4()
        archive_dir = build_archive(
            tmp_path,
            [
                ArchiveEntry(
                    file=File(
                        full_name=FilePurePath("report.pdf"),
                        source="test",
                        sha256="abc",
                        size=3,
                        storage_data=LazyBytes(service_id=uuid4()),
                        thumbnail_data=LazyBytes(service_id=thumbnail_id),
                    ),
                    content=b"img",
                )
            ],
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["id", f"files/{thumbnail_id}"])

        assert result.returncode == 0
        assert "report.pdf" in result.stdout
        assert "thumbnail" in result.stdout

    def test_resolves_rendered_file(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        rendered_id = uuid4()
        archive_dir = build_archive(
            tmp_path,
            [
                ArchiveEntry(
                    file=File(
                        full_name=FilePurePath("report.pdf"),
                        source="test",
                        sha256="abc",
                        size=3,
                        storage_data=LazyBytes(service_id=uuid4()),
                        rendered_file=RenderedFile(
                            image_data=LazyBytes(service_id=rendered_id)
                        ),
                    ),
                    content=b"img",
                )
            ],
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["id", f"files/{rendered_id}"])

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


def _run_shell(archive_dir: Path, commands: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(archive_dir / CLI_FILENAME)],
        input=commands,
        capture_output=True,
        text=True,
        check=False,
    )


class TestCliShell:
    def test_no_args_launches_shell(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "exit\n")

        assert result.returncode == 0
        assert "loom>" in result.stdout

    def test_shell_subcommand_launches_shell(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = subprocess.run(
            [sys.executable, str(archive_dir / CLI_FILENAME), "shell"],
            input="exit\n",
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "loom>" in result.stdout

    def test_shell_ls_lists_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "ls\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_shell_search_finds_file(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "grep report\nexit\n")

        assert result.returncode == 0
        assert "report.pdf" in result.stdout

    def test_shell_tree_shows_hierarchy(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"pdf", "images/photo.jpg": b"img"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "tree\nexit\n")

        assert result.returncode == 0
        assert "docs" in result.stdout
        assert "images" in result.stdout

    def test_shell_invalid_command_stays_running(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "invalidcmd\nexit\n")

        assert result.returncode == 0

    def test_shell_error_command_stays_running(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "ls nonexistent\nexit\n")

        assert result.returncode == 0
        assert "no file found matching" in result.stderr

    def test_shell_help_prints_help(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "help\nexit\n")

        assert result.returncode == 0
        assert "Loom archive CLI" in result.stdout

    def test_shell_eof_exits_cleanly(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        result = _run_shell(archive_dir, "")

        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Memory tests
# ---------------------------------------------------------------------------

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
        # Exact match: resolve_name holds at most 1 IndexEntry at a time.
        # If load_entries returned a list, all 100 MB would be live → fails limit.
        archive_fmt.cmd_ls(
            argparse.Namespace(path="docs/file_0001.txt"),
            index_dir=large_archive_dir / "files_index",
        )

    @pytest.mark.limit_memory("20 MB")
    def test_tree_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # cmd_tree only stores path-component strings; meta is discarded each iteration.
        archive_fmt.cmd_tree(
            argparse.Namespace(),
            index_dir=large_archive_dir / "files_index",
        )

    @pytest.mark.limit_memory("30 MB")
    def test_info_does_not_load_all_entries(self, large_archive_dir: Path) -> None:
        # First pass: 1 matched entry live. Second pass builds id→name strings only.
        # If entries_by_id stored full IndexEntry objects, all 100 MB would be live.
        archive_fmt.cmd_info(
            argparse.Namespace(name="docs/file_0001.txt", json=False),
            index_dir=large_archive_dir / "files_index",
            files_dir=large_archive_dir / "files",
        )
