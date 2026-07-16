import io
import json
import zipfile
from pathlib import Path
from uuid import UUID, uuid4

from common.archive.archive_repository import LOOM_ARCHIVE_VERSION, Archive
from common.dependencies import (
    get_archive_repository,
    get_file_repository,
)
from common.file.file_repository import File, FilePurePath, RenderedFile
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    LazyBytes,
)
from create_archive.archive_helpers import (
    ArchiveEntry,
    build_archive,
    build_archive_bytes,
    make_archive,
    simple_entries,
)
from stream_zip import stream_zip

from worker.create_archive.tasks.archive_cli import (
    CLI_ENTRYPOINT_FILENAME,
    CLI_FILENAME,
    FILES_DIR,
    FILES_INDEX_DIR,
    JSON_SUFFIX,
    MANIFEST_FILENAME,
    README_FILENAME,
    SHELL_INDEX_FILENAME,
    ZIP_EXTENSION,
)
from worker.create_archive.tasks.archive_cli._db import open_shell_db
from worker.create_archive.tasks.compress_files import (
    _archive_data,
    _file_storage_fields,
)
from worker.create_archive.tasks.detect_loom_archive import detect_loom_archive
from worker.create_archive.tasks.unzip_loom_archive import (
    restore_archive_metadata_task,
    store_raw_files_task,
    upsert_file_objects_task,
)

LAZYBYTES_THRESHOLD_BYTES = 64

_ARCHIVE = make_archive()
ARCHIVE_NAME = _ARCHIVE.name.removesuffix(ZIP_EXTENSION)


def _make_file(
    *, service_id: UUID | None = None, embedded_data: bytes | None = None
) -> File:
    """Create a minimal File object for testing."""
    if service_id is not None:
        storage_data: LazyBytes | None = LazyBytes(service_id=service_id)
    elif embedded_data is not None:
        storage_data = LazyBytes(embedded_data=embedded_data)
    else:
        storage_data = None

    return File(
        full_name=FilePurePath("test_file.txt"),
        source="api-upload",
        sha256="abc123",
        size=42,
        storage_data=storage_data,
    )


# ---------------------------------------------------------------------------
# compress_files_task / _archive_data
# ---------------------------------------------------------------------------


class TestArchiveData:
    def test_v2_structure_files_and_repo_entries(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """_archive_data yields files/ and files_index/ entries per file."""
        service_id = uuid4()
        file = _make_file(service_id=service_id)
        file_storage_service_inmemory.from_file_with_id(
            io.BytesIO(b"hello world"), service_id
        )
        get_file_repository().get_by_id.return_value = file

        entries = list(_archive_data([file.id_], _ARCHIVE))

        names = [e[0] for e in entries]
        assert f"{ARCHIVE_NAME}/{FILES_DIR}/{service_id}" in names
        assert f"{ARCHIVE_NAME}/{FILES_INDEX_DIR}/{file.id_}{JSON_SUFFIX}" in names

    def test_embedded_data_emits_only_repo_entry(self):
        """Files with embedded_data (no service_id) skip the files/ entry."""
        file = _make_file(embedded_data=b"tiny")
        get_file_repository().get_by_id.return_value = file

        entries = list(_archive_data([file.id_], _ARCHIVE))

        names = [e[0] for e in entries]
        assert all(f"/{FILES_DIR}/" not in n for n in names)
        assert f"{ARCHIVE_NAME}/{FILES_INDEX_DIR}/{file.id_}{JSON_SUFFIX}" in names

    def test_no_storage_data_skips_file(self):
        """Files without storage_data contribute no file entries."""
        file = _make_file()
        get_file_repository().get_by_id.return_value = file

        entries = list(_archive_data([file.id_], _ARCHIVE))
        names = [e[0] for e in entries]
        assert all(
            f"/{FILES_DIR}/" not in n and f"/{FILES_INDEX_DIR}/" not in n for n in names
        )

    def test_repo_entry_json_is_valid_file_model(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """The file_repository JSON can be deserialised back to a File."""
        service_id = uuid4()
        file = _make_file(service_id=service_id)
        file_storage_service_inmemory.from_file_with_id(io.BytesIO(b"data"), service_id)
        get_file_repository().get_by_id.return_value = file

        entries = list(_archive_data([file.id_], _ARCHIVE))
        repo_entry = next(e for e in entries if f"/{FILES_INDEX_DIR}/" in e[0])

        json_bytes = b"".join(repo_entry[4])
        parsed = json.loads(json_bytes)
        assert parsed["source"] == "api-upload"
        assert parsed["sha256"] == "abc123"

    def test_produces_valid_zip(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """_archive_data output can be consumed by stream_zip into a valid ZIP."""
        service_id = uuid4()
        file = _make_file(service_id=service_id)
        file_storage_service_inmemory.from_file_with_id(
            io.BytesIO(b"payload"), service_id
        )
        get_file_repository().get_by_id.return_value = file

        zip_bytes = b"".join(stream_zip(_archive_data([file.id_], _ARCHIVE)))

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            namelist = zf.namelist()
            assert f"{ARCHIVE_NAME}/{FILES_DIR}/{service_id}" in namelist
            assert (
                f"{ARCHIVE_NAME}/{FILES_INDEX_DIR}/{file.id_}{JSON_SUFFIX}" in namelist
            )
            assert zf.read(f"{ARCHIVE_NAME}/{FILES_DIR}/{service_id}") == b"payload"
            assert f"{ARCHIVE_NAME}/{README_FILENAME}" in namelist
            assert zf.read(f"{ARCHIVE_NAME}/{README_FILENAME}").startswith(
                b"# Loom Archive"
            )
            assert f"{ARCHIVE_NAME}/{MANIFEST_FILENAME}" in namelist
            manifest = json.loads(zf.read(f"{ARCHIVE_NAME}/{MANIFEST_FILENAME}"))
            assert manifest["version"] == LOOM_ARCHIVE_VERSION

    def test_all_storage_fields_are_collected(self):
        """_file_storage_fields collects storage_data, thumbnail_data, and all
        rendered_file fields."""
        ids = [uuid4() for _ in range(5)]
        file = File(
            full_name=FilePurePath("f.txt"),
            source="s",
            sha256="x",
            size=1,
            storage_data=LazyBytes(service_id=ids[0]),
            thumbnail_data=LazyBytes(service_id=ids[1]),
            rendered_file=RenderedFile(
                image_data=LazyBytes(service_id=ids[2]),
                office_pdf_data=LazyBytes(service_id=ids[3]),
                browser_pdf_data=LazyBytes(service_id=ids[4]),
            ),
        )
        collected_ids = {s.service_id for s in _file_storage_fields(file)}
        assert collected_ids == set(ids)

    def test_cli_is_included_in_archive(self):
        """cli.py entry point and archive_cli/ package are bundled into the archive."""
        zip_bytes = b"".join(stream_zip(_archive_data([], _ARCHIVE)))

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            namelist = zf.namelist()
            assert f"{ARCHIVE_NAME}/{CLI_ENTRYPOINT_FILENAME}" in namelist
            assert f"{ARCHIVE_NAME}/{CLI_FILENAME}/__init__.py" in namelist
            assert f"{ARCHIVE_NAME}/{CLI_FILENAME}/_commands.py" in namelist
            assert f"{ARCHIVE_NAME}/{CLI_FILENAME}/_parser.py" in namelist

    def test_thumbnail_data_is_exported(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """thumbnail_data is included as a separate files/ entry."""
        service_id = uuid4()
        thumbnail_id = uuid4()
        file = File(
            full_name=FilePurePath("test_file.txt"),
            source="api-upload",
            sha256="abc123",
            size=42,
            storage_data=LazyBytes(service_id=service_id),
            thumbnail_data=LazyBytes(service_id=thumbnail_id),
        )
        file_storage_service_inmemory.from_file_with_id(
            io.BytesIO(b"content"), service_id
        )
        file_storage_service_inmemory.from_file_with_id(
            io.BytesIO(b"thumb"), thumbnail_id
        )
        get_file_repository().get_by_id.return_value = file

        zip_bytes = b"".join(stream_zip(_archive_data([file.id_], _ARCHIVE)))

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            namelist = zf.namelist()
            assert f"{ARCHIVE_NAME}/{FILES_DIR}/{service_id}" in namelist
            assert f"{ARCHIVE_NAME}/{FILES_DIR}/{thumbnail_id}" in namelist
            assert zf.read(f"{ARCHIVE_NAME}/{FILES_DIR}/{thumbnail_id}") == b"thumb"


# ---------------------------------------------------------------------------
# unzip_loom_archive
# ---------------------------------------------------------------------------


class TestStoreRawFilesTask:
    def test_stores_raw_bytes_under_original_uuid(
        self,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ):
        service_id = uuid4()
        raw = b"raw file content"
        file = _make_file(service_id=service_id)
        zip_bytes = build_archive_bytes(
            [ArchiveEntry(file=file, content=raw)],
            file_storage_service_inmemory,
            _ARCHIVE,
        )
        archive_lb = file_storage_service_inmemory.from_bytes(zip_bytes)

        store_raw_files_task(archive_lb)

        result = b"".join(
            file_storage_service_inmemory.load_generator(
                LazyBytes(service_id=service_id)
            )
        )
        assert result == raw


class TestUpsertFileObjectsTask:
    def test_upserts_file_objects_with_original_id(
        self,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ):
        service_id = uuid4()
        file = _make_file(service_id=service_id)
        original_id = file.id_
        zip_bytes = build_archive_bytes(
            [ArchiveEntry(file=file, content=b"data")],
            file_storage_service_inmemory,
            _ARCHIVE,
        )
        archive_lb = file_storage_service_inmemory.from_bytes(zip_bytes)

        upsert_file_objects_task(archive_lb)

        file_repository = get_file_repository()
        assert file_repository.save.call_count == 1  # type: ignore[union-attr]
        saved_file: File = file_repository.save.call_args[0][0]  # type: ignore[union-attr]
        assert saved_file.id_ == original_id
        assert saved_file.sha256 == "abc123"


class TestRestoreArchiveMetadataTask:
    def test_restores_archive_state_and_storage_data(
        self,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ):
        zip_bytes = build_archive_bytes([], file_storage_service_inmemory, _ARCHIVE)
        archive_lb = file_storage_service_inmemory.from_bytes(zip_bytes)

        restore_archive_metadata_task(archive_lb)

        archive_repo = get_archive_repository()
        assert archive_repo.save.call_count == 1  # type: ignore[union-attr]
        saved: Archive = archive_repo.save.call_args[0][0]  # type: ignore[union-attr]
        assert saved.state == "imported"
        assert saved.plain_file.storage_data == archive_lb
        assert saved.encrypted_file.storage_data is None

    def test_no_op_when_manifest_missing(
        self,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ):
        # ZIP with no MANIFEST.json
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as zf:
            zf.writestr("other.txt", "hello")
        archive_lb = file_storage_service_inmemory.from_bytes(buf.getvalue())

        restore_archive_metadata_task(archive_lb)

        get_archive_repository().save.assert_not_called()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# detect_loom_archive
# ---------------------------------------------------------------------------


class TestDetectLoomArchive:
    def test_plain_loom_archive_is_detected(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """A ZIP with a valid MANIFEST.json is recognised as a loom archive."""
        file = _make_file(service_id=uuid4())
        zip_bytes = build_archive_bytes(
            [ArchiveEntry(file=file, content=b"data")],
            file_storage_service_inmemory,
            _ARCHIVE,
        )
        archive_lb = file_storage_service_inmemory.from_bytes(zip_bytes)

        result = detect_loom_archive(archive_lb)

        assert result is not None

    def test_non_loom_zip_returns_none(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """A plain ZIP without MANIFEST.json returns None."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as zf:
            zf.writestr("some_file.txt", b"hello")
        archive_lb = file_storage_service_inmemory.from_bytes(buf.getvalue())

        assert detect_loom_archive(archive_lb) is None

    def test_non_zip_returns_none(
        self, file_storage_service_inmemory: InMemoryFileStorageLazyBytesService
    ):
        """Random bytes (not a ZIP) return None."""
        archive_lb = file_storage_service_inmemory.from_bytes(b"not a zip file at all")

        assert detect_loom_archive(archive_lb) is None


# ---------------------------------------------------------------------------
# SHELL_INDEX.json
# ---------------------------------------------------------------------------


class TestShellIndexInArchive:
    def test_shell_index_file_is_present(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"data"}),
            file_storage_service_inmemory,
        )
        assert (archive_dir / SHELL_INDEX_FILENAME).exists()

    def test_shell_index_contains_all_files(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        # simple_entries uses source="test", so vpaths are prefixed with "test/"
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/report.pdf": b"a", "images/photo.jpg": b"b"}),
            file_storage_service_inmemory,
        )
        db = open_shell_db(archive_dir)
        vpaths = {row[0] for row in db.execute("SELECT vpath FROM files").fetchall()}
        assert "test/docs/report.pdf" in vpaths
        assert "test/images/photo.jpg" in vpaths

    def test_shell_index_children_root(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            simple_entries({"docs/a.pdf": b"a", "note.txt": b"n"}),
            file_storage_service_inmemory,
        )
        db = open_shell_db(archive_dir)
        root_children = {
            row[0]
            for row in db.execute(
                "SELECT child_name FROM children WHERE parent_path = 'test'"
            ).fetchall()
        }
        assert "docs/" in root_children
        assert "note.txt" in root_children

    def test_shell_index_by_file_id_populated(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = simple_entries({"report.pdf": b"data"})
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        file_id = str(entries[0].file.id_)
        db = open_shell_db(archive_dir)
        row = db.execute(
            "SELECT vpath FROM files WHERE file_id = ?", (file_id,)
        ).fetchone()
        assert row is not None
        assert row[0] == "test/report.pdf"

    def test_shell_index_by_storage_id_file_role(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        sid = uuid4()
        entries = [
            ArchiveEntry(
                file=File(
                    full_name=FilePurePath("report.pdf"),
                    source="test",
                    sha256="abc",
                    size=4,
                    storage_data=LazyBytes(service_id=sid),
                ),
                content=b"data",
            )
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)
        db = open_shell_db(archive_dir)
        rows = db.execute(
            "SELECT vpath, role FROM storage WHERE storage_id = ?", (str(sid),)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "test/report.pdf"
        assert rows[0][1] == "file"
