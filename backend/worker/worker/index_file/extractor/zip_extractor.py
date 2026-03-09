import zipfile
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class ZipExtractor(NamedFileExtractorBase):
    """Extractor for ZIP files, built with the `zipfile` module."""

    def extract_file(self, fileobj: IO[bytes], _: str, out_dir: str, __: IO[bytes]):
        try:
            with zipfile.ZipFile(fileobj) as f:
                # Note that directory traversal is mitigated by the
                # zipfile library, which removes leading slashes or '..'
                # elements from the filenames.
                f.extractall(out_dir)
        except zipfile.BadZipFile as exc:
            raise ExtractNotSupported from exc
