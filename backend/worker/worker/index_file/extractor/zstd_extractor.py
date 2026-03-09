from os.path import join
from typing import IO

from zstandard import ZstdDecompressor, ZstdError

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)

ZSTD_EXTRACTOR_READ_CHUNK_SIZE__BYTES = 8192


class ZstdExtractor(NamedFileExtractorBase):
    """Extractor for zstd-compressed files."""

    def extract_file(self, fileobj: IO[bytes], _: str, out_dir: str, __: IO[bytes]):
        try:
            dctx = ZstdDecompressor()
            outpath = join(out_dir, "0")

            # Stream decompression from fileobj
            with dctx.stream_reader(fileobj) as reader:
                with open(outpath, "wb") as f:
                    # Read and write in chunks to avoid loading everything into memory
                    while chunk := reader.read(ZSTD_EXTRACTOR_READ_CHUNK_SIZE__BYTES):
                        f.write(chunk)
        except ZstdError as ex:
            raise ExtractNotSupported from ex
