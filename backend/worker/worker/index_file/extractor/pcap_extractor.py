from subprocess import CalledProcessError, run
from typing import IO

from worker.index_file.extractor.base import (
    ExtractNotSupported,
    NamedFileExtractorBase,
)


class PcapExtractor(NamedFileExtractorBase):
    def extract_file(
        self, fileobj: IO[bytes], file_type: str, __: str, out_content: IO[bytes]
    ):  # pylint: disable=duplicate-code
        cmd = [
            "tshark",
            "-r",
            fileobj.name,
        ]

        # Only process actual PCAP files. While tshark can technically read
        # other file types (e.g., images like GIF), we don't want to process
        # them as they're not network captures.
        # Example: tshark -r image.gif will output "MIME_FILE (GIF89a)" but this isn't useful.
        if file_type not in ["application/vnd.tcpdump.pcap"]:
            raise ExtractNotSupported(f"Not a supported file_type: {file_type}")

        try:
            run(
                cmd,
                check=True,
                stdout=out_content,
            )
        except CalledProcessError as ex:
            raise ExtractNotSupported from ex
