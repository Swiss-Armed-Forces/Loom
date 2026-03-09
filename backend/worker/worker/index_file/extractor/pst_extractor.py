from subprocess import CalledProcessError, run
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class PstExtractor(NamedFileExtractorBase):
    """Outlook pst file processor will create a temporary file and write the content to
    it it will then unpack the created temporary file and process each unpacked file."""

    def extract_file(
        self, fileobj: IO[bytes], file_type: str, out_dir: str, out_content: IO[bytes]
    ):
        # extract content
        cmd = [
            "readpst",
            "-o",
            out_dir,
            "-D",
            "-j",
            "1",
            "-r",
            "-u",
            "-w",
            "-e",
            fileobj.name,
        ]

        try:
            run(cmd, check=True, stdout=out_content)
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex
