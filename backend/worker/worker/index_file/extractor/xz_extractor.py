from lzma import LZMAError
from lzma import open as xz_open
from os.path import join
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)

XZ_EXTRACTOR_READ_CHUNK_SIZE_BYTES = 131072  # 128KB


class XZExtractor(NamedFileExtractorBase):
    """Extractor for xz-compressed files, built with the `lzma` module."""

    def extract_file(self, fileobj: IO[bytes], _: str, out_dir: str, __: IO[bytes]):
        try:
            outpath = join(out_dir, "0")
            with xz_open(fileobj, mode="rb") as reader, open(outpath, "wb") as f:
                # Read and write in chunks to avoid loading everything into memory
                while chunk := reader.read(XZ_EXTRACTOR_READ_CHUNK_SIZE_BYTES):
                    f.write(chunk)
        except LZMAError as exc:
            raise ExtractNotSupported from exc
