from typing import IO

import pytest
from common.services.lazybytes_service import LazyBytes, LazyBytesService

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    ExtractorBase,
)
from worker.index_file.tasks.tika_processing import TikaExtractorFallback
from worker.services.tika_service import TikaResult


# Extractor stubs for testing fallback behavior
class ExtractorSuccessStub(ExtractorBase):
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        TikaResult()


class ExtractorNotSupportedStub(ExtractorBase):
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        raise ExtractNotSupported


class ExtractorExceptionStub(ExtractorBase):
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        raise ExceptionStub


class ExceptionStub(Exception):
    pass


@pytest.mark.parametrize(
    "extractor, file_bytes, excepting",
    [
        (ExtractorSuccessStub(), bytes([]), False),
        (ExtractorNotSupportedStub(), bytes([]), False),
        (ExtractorExceptionStub(), bytes([]), True),
    ],
)
def test_extractor(
    extractor: ExtractorBase,
    file_bytes: bytes,
    excepting: bool,
    lazybytes_service_inmemory: LazyBytesService,
):
    processor = TikaExtractorFallback(extractor)
    content = lazybytes_service_inmemory.from_bytes(data=file_bytes)
    file_type = "application/octet-stream"
    if excepting:
        with pytest.raises(ExceptionStub):
            processor.handle(content, file_type)

    else:
        processor.handle(content, file_type)
