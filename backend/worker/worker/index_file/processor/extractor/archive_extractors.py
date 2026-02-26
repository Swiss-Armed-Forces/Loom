import abc
import logging
import shutil
import tarfile
import zipfile
from getpass import getuser
from os.path import basename, join
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import IO

# pylint: disable=no-name-in-module
from zstd import Error as ZSTDError
from zstd import ZSTD_uncompress

# pylint: enable=no-name-in-module

logger = logging.getLogger(__name__)


class ExtractNotSupported(Exception):
    """Raised when the file is not supported by an Extractor."""


class ExtractorBase(abc.ABC):
    """Base class for Extractors."""

    @abc.abstractmethod
    def extract(self, fileobj: IO[bytes], outdir: str):
        """Extracts the file to the given output directory.

        Args:
          fileobj: the file to extract (supports: .name)
          outdir: the output directory

        Raises:
          ExtractNotSupported: if the file is not supported by this extractor
        """


class TarExtractor(ExtractorBase):
    """Extractor for TAR files, built with the `tarfile` module."""

    def extract(self, fileobj: IO[bytes], outdir: str):
        try:
            with tarfile.open(fileobj=fileobj) as f:
                # Setting the filter to 'data' mitigates directory
                # traversal, as all unix-specific information is
                # ignored or blocked, e.g. a leading slash
                # or '..'.
                f.extractall(outdir, filter="data")
        except tarfile.TarError as exc:
            raise ExtractNotSupported from exc


class ZipExtractor(ExtractorBase):
    """Extractor for ZIP files, built with the `zipfile` module."""

    def extract(self, fileobj: IO[bytes], outdir: str):
        try:
            with zipfile.ZipFile(fileobj) as f:
                # Note that directory traversal is mitigated by the
                # zipfile library, which removes leading slashes or '..'
                # elements from the filenames.
                f.extractall(outdir)
        except zipfile.BadZipFile as exc:
            raise ExtractNotSupported from exc


class PstArchiveExtractor(ExtractorBase):
    """Outlook pst file processor will create a temporary file and write the content to
    it it will then unpack the created temporary file and process each unpacked file."""

    def _extract_pst_archive(self, pst_file: str, outdir: str):
        cmd = [
            "readpst",
            "-o",
            outdir,
            "-D",
            "-j",
            "1",
            "-r",
            "-u",
            "-w",
            "-e",
            pst_file,
        ]
        run(cmd, check=True)

    def extract(self, fileobj: IO[bytes], outdir: str):
        """Process pst."""
        # extract content
        try:
            self._extract_pst_archive(fileobj.name, outdir)
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex


class PcapExtractor(ExtractorBase):
    def extract(self, fileobj: IO[bytes], outdir: str):

        cmd = [
            "tshark",
            "-r",
            fileobj.name,
        ]
        stdout_file_path = Path(outdir, "pcap_decoded").absolute().as_posix()
        with open(stdout_file_path, "wb") as stdout_file:
            try:
                run(
                    cmd,
                    check=True,
                    stdout=stdout_file,
                )
            except CalledProcessError as ex:
                raise ExtractNotSupported from ex


class ZstdExtractor(ExtractorBase):
    """Extractor for zstd-compressed files built with the zstd module."""

    def extract(self, fileobj: IO[bytes], outdir: str):
        try:
            data = ZSTD_uncompress(fileobj.read())
            outpath = join(outdir, "0")
            with open(outpath, "wb") as f:
                f.write(data)
        except ZSTDError as ex:
            raise ExtractNotSupported from ex


class BinwalkExtractor(ExtractorBase):
    """Extracts information of general binaries by using binwalk on general binaries.

    Avoids extracting archives already being processed by the other extractors.
    """

    def extract(self, fileobj: IO[bytes], outdir: str):
        # Extract contents
        cmd_extract = [
            "binwalk",
            f"--run-as={getuser()}",
            "--extract",
            "--subdirs",
            "--directory",
            outdir,
            fileobj.name,
        ]
        try:
            run(cmd_extract, check=True)
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex

        # move files out of `.extracted` directory
        extracted_dir = Path(f"{outdir}/_{basename(fileobj.name)}.extracted")

        if not extracted_dir.is_dir():
            # nothing extracted
            return

        for item in extracted_dir.iterdir():
            shutil.move(item, outdir)
        extracted_dir.rmdir()
