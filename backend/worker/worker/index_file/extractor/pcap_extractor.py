from subprocess import CalledProcessError, run
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class PcapExtractor(NamedFileExtractorBase):
    def extract_file(
        self, fileobj: IO[bytes], _: str, __: str, out_content: IO[bytes]
    ):  # pylint: disable=duplicate-code
        cmd = [
            "tshark",
            "-r",
            fileobj.name,
        ]

        try:
            run(
                cmd,
                check=True,
                stdout=out_content,
            )
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex
