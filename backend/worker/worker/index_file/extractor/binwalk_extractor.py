import shutil
from getpass import getuser
from os.path import basename
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class BinwalkExtractor(NamedFileExtractorBase):
    """Extracts information of general binaries by using binwalk on general binaries."""

    def extract_file(
        self, fileobj: IO[bytes], file_type: str, out_dir: str, out_content: IO[bytes]
    ):
        # Extract contents
        cmd_extract = [
            "binwalk",
            f"--run-as={getuser()}",
            "--extract",
            "--subdirs",
            "--directory",
            out_dir,
            fileobj.name,
        ]
        try:
            run(
                cmd_extract,
                check=True,
                stdout=out_content,
            )
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex

        # move files out of `.extracted` directory
        extracted_dir = Path(f"{out_dir}/_{basename(fileobj.name)}.extracted")

        if not extracted_dir.is_dir():
            # nothing extracted
            raise ExtractNotSupported

        for item in extracted_dir.iterdir():
            shutil.move(item, out_dir)
        extracted_dir.rmdir()
