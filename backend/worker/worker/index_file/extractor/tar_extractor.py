import tarfile
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class TarExtractor(NamedFileExtractorBase):
    """Extractor for TAR files, built with the `tarfile` module."""

    def extract_file(
        self, fileobj: IO[bytes], file_type: str, out_dir: str, _: IO[bytes]
    ):
        # tarfile is very genorous when trying to extract files,
        # hence it won't raise TarError for many file types which
        # are not actually tar files: This is why we limit here
        # to what we process with this extractor.
        if file_type not in [
            "application/x-tar",
            "application/x-gtar",
            "application/x-ustar",
        ]:
            raise ExtractNotSupported(f"Not a supported file_type: {file_type}")
        try:
            with tarfile.open(fileobj=fileobj) as f:
                # Setting the filter to 'data' mitigates directory
                # traversal, as all unix-specific information is
                # ignored or blocked, e.g. a leading slash
                # or '..'.
                f.extractall(out_dir, filter="data")
        except tarfile.TarError as exc:
            raise ExtractNotSupported from exc
