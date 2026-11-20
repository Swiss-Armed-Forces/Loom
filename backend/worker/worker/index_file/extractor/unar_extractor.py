from subprocess import DEVNULL, CalledProcessError, run
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class UnarExtractor(NamedFileExtractorBase):
    """Extractor for the archive formats `unar` reads, built on the `unar` binary.

    It covers the two formats nothing else in the chain does. Tika parses RAR4
    through junrar but refuses RAR5, which junrar does not implement; it reads plain
    7z through commons-compress but declines encrypted ones. Both land here. `unar`
    also reads ISO 9660 and CFBF, which are force-routed to the fallbacks with no
    extractor of their own.

    This is the last entry in FALLBACKS, so every format-specific extractor ahead of
    it keeps first claim and `unar` only ever sees what none of them could read.
    `unar` declines what it cannot unpack - PDFs, images, mail - with a non-zero
    exit, which is the ExtractNotSupported that leaves such a file on the strings
    path.
    """

    def extract_file(self, fileobj: IO[bytes], _: str, out_dir: str, __: IO[bytes]):
        cmd = [
            "unar",
            "-quiet",
            # Members whose name repeats one already written: the archive decides
            # the order and there is nothing to prompt about.
            "-force-overwrite",
            # Without this `unar` wraps the members in a directory named after the
            # archive, which here is a random temporary filename.
            "-no-directory",
            "-output-directory",
            out_dir,
            # An encrypted archive is one we give up on, as ZipExtractor does. The
            # empty password says so explicitly rather than relying on `unar`
            # refusing to prompt.
            "-password",
            "",
            "--",
            fileobj.name,
        ]

        try:
            run(cmd, check=True, stdin=DEVNULL, capture_output=True)
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex
