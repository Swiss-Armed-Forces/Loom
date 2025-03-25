"""Test the TIKA fallback mechanism."""

from typing import IO

import pytest
from common.services.lazybytes_service import InMemoryLazyBytesService
from common.services.tika_service import TikaResult

from worker.index_file.processor.extractor.archive_extractors import (
    ExtractNotSupported,
    ExtractorBase,
)
from worker.index_file.tasks.tika_processing import TikaExtractorFallback


# Extractor stubs for testing fallback behavior
class ExtractorSuccessStub(ExtractorBase):
    def extract(self, fileobj: IO[bytes], outdir: str):
        TikaResult()


class ExtractorNotSupported(ExtractorBase):
    def extract(self, fileobj: IO[bytes], outdir: str):
        raise ExtractNotSupported


class ExtractorException(ExtractorBase):
    def extract(self, fileobj: IO[bytes], outdir: str):
        raise ExceptionStub


class ExceptionStub(Exception):
    pass


@pytest.mark.parametrize(
    "extractor, file_bytes, excepting",
    [
        (ExtractorSuccessStub(), bytes([]), False),
        (ExtractorNotSupported(), bytes([]), False),
        (ExtractorException(), bytes([]), True),
    ],
)
def test_extractor(extractor: ExtractorBase, file_bytes: bytes, excepting: bool):
    processor = TikaExtractorFallback(extractor)
    content = InMemoryLazyBytesService().from_bytes(data=file_bytes)
    if excepting:
        with pytest.raises(ExceptionStub):
            processor.handle(content)

    else:
        processor.handle(content)
