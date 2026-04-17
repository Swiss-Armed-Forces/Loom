import zlib
from gzip import BadGzipFile
from gzip import open as gzip_open
from os.path import join
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)

GZIP_EXTRACTOR_READ_CHUNK_SIZE_BYTES = 128 * 1024


class GzipExtractor(NamedFileExtractorBase):
    """Extractor for GZIP files, built with the `gzip` module."""

    def extract_file(self, fileobj: IO[bytes], _: str, out_dir: str, __: IO[bytes]):
        try:
            outpath = join(out_dir, "0")
            with gzip_open(filename=fileobj) as reader, open(outpath, "wb") as f:
                while chunk := reader.read(GZIP_EXTRACTOR_READ_CHUNK_SIZE_BYTES):
                    f.write(chunk)
        except (BadGzipFile, zlib.error) as exc:
            raise ExtractNotSupported from exc
