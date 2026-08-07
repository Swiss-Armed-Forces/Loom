from pathlib import Path

from common.file.file_repository import TranslatedLanguage
from common.services.lazybytes_service import InMemoryFileStorageLazyBytesService
from create_archive.archive_cli.helpers import _make_entry, _run
from create_archive.archive_helpers import ArchiveEntry, build_archive


def _entry_with_translations(
    name: str, translations: list[TranslatedLanguage]
) -> ArchiveEntry:
    return _make_entry(name, translations=translations)


class TestCliTranslate:
    def test_lists_languages_when_no_language_given(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entry = _entry_with_translations(
            "report.pdf",
            [
                TranslatedLanguage(confidence=0.99, language="en", text="Hello"),
                TranslatedLanguage(confidence=0.85, language="de", text="Hallo"),
            ],
        )
        archive_dir = build_archive(tmp_path, [entry], file_storage_service_inmemory)

        result = _run(archive_dir, ["translate", "report.pdf"])

        assert result.returncode == 0
        assert "en" in result.stdout
        assert "de" in result.stdout

    def test_prints_translation_text(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entry = _entry_with_translations(
            "report.pdf",
            [TranslatedLanguage(confidence=0.99, language="en", text="Hello world")],
        )
        archive_dir = build_archive(tmp_path, [entry], file_storage_service_inmemory)

        result = _run(archive_dir, ["translate", "report.pdf", "en"])

        assert result.returncode == 0
        assert result.stdout.strip() == "Hello world"

    def test_unknown_language_exits_1(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entry = _entry_with_translations(
            "report.pdf",
            [TranslatedLanguage(confidence=0.99, language="en", text="Hello")],
        )
        archive_dir = build_archive(tmp_path, [entry], file_storage_service_inmemory)

        result = _run(archive_dir, ["translate", "report.pdf", "fr"])

        assert result.returncode == 1
        assert "fr" in result.stderr
        assert "en" in result.stderr

    def test_no_translations_exits_1(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            [_entry_with_translations("report.pdf", [])],
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["translate", "report.pdf"])

        assert result.returncode == 1
        assert "No translations" in result.stderr

    def test_confidence_shown_in_language_list(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entry = _entry_with_translations(
            "report.pdf",
            [TranslatedLanguage(confidence=0.95, language="en", text="Hello")],
        )
        archive_dir = build_archive(tmp_path, [entry], file_storage_service_inmemory)

        result = _run(archive_dir, ["translate", "report.pdf"])

        assert result.returncode == 0
        assert "0.95" in result.stdout

    def test_nonexistent_file_exits_1(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        archive_dir = build_archive(
            tmp_path,
            [_entry_with_translations("report.pdf", [])],
            file_storage_service_inmemory,
        )

        result = _run(archive_dir, ["translate", "does_not_exist.pdf"])

        assert result.returncode == 1

    def test_ambiguous_name_exits_1(
        self,
        tmp_path: Path,
        file_storage_service_inmemory: InMemoryFileStorageLazyBytesService,
    ) -> None:
        entries = [
            _entry_with_translations(
                "dir_a/report.pdf",
                [TranslatedLanguage(confidence=0.9, language="en", text="A")],
            ),
            _entry_with_translations(
                "dir_b/report.pdf",
                [TranslatedLanguage(confidence=0.9, language="en", text="B")],
            ),
        ]
        archive_dir = build_archive(tmp_path, entries, file_storage_service_inmemory)

        result = _run(archive_dir, ["translate", "report.pdf"])

        assert result.returncode == 1
        assert "ambiguous" in result.stderr
