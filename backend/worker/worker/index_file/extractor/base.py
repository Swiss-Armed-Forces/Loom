import abc
import logging
from typing import IO

# pylint: disable=no-name-in-module
from common.dependencies import get_lazybytes_service
from common.services.lazybytes_service import LazyBytes

# pylint: enable=no-name-in-module

logger = logging.getLogger(__name__)


class ExtractNotSupported(Exception):
    """Raised when the file is not supported by an Extractor."""


class ExtractorBase(abc.ABC):
    """Base class for Extractors."""

    @abc.abstractmethod
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        """Extracts the file to the given output directory.

        Args:
          file_content: the file content to extract
          file_type: MIME type of file_content
          out_dir: the output directory
          out_content: the output content

        Raises:
          ExtractNotSupported: if the file is not supported by this extractor
        """


class NamedFileExtractorBase(ExtractorBase):
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        with get_lazybytes_service().load_file_named(file_content) as fd:
            self.extract_file(fd, file_type, out_dir, out_content)

    @abc.abstractmethod
    def extract_file(
        self, fileobj: IO[bytes], file_type: str, out_dir: str, out_content: IO[bytes]
    ):
        """Extracts the file to the given output directory.

        Args:
          fileobj: the file to extract (supports: .name)
          file_type: MIME type of file_content
          out_dir: the output directory
          out_content: the output content

        Raises:
          ExtractNotSupported: if the file is not supported by this extractor
        """


class MemoryviewExtractorBase(ExtractorBase):
    def extract(
        self,
        file_content: LazyBytes,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        with get_lazybytes_service().load_memoryview(file_content) as file_memview:
            self.extract_memoryview(file_memview, file_type, out_dir, out_content)

    @abc.abstractmethod
    def extract_memoryview(
        self,
        file_memview: memoryview,
        file_type: str,
        out_dir: str,
        out_content: IO[bytes],
    ):
        """Extracts the file to the given output directory.

        Args:
          file_memview: the file to extract
          file_type: MIME type of file_content
          out_dir: the output directory
          out_content: the output content

        Raises:
          ExtractNotSupported: if the file is not supported by this extractor
        """
