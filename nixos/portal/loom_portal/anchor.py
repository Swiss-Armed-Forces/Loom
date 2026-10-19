"""The certificate a visitor has to trust, and whether it has arrived yet.

Published by `loom-portal-certificate.service`, which is root and has the operator's
kubeconfig; read here, which is neither. Two files, the same split `loom_ready.state`
makes and for the same reason -- the fingerprint is a short string that the page prints
and a shell script could also have written, and parsing a certificate to recover it
would mean putting openssl in this service's closure to compute something it could be
handed.

It is genuinely absent for the first part of a boot. A cluster bring-up on an appliance
takes minutes at best and hours on a first-time setup, and this service starts long
before it. So "not there yet" is an ordinary state with a sentence of its own on the
page, not an error.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# A PEM certificate on this box is a couple of kilobytes. The cap is here because this
# file is read on every page load and a reader that trusted its size would be one
# wrongly synced secret away from holding a megabyte per request.
MAX_ANCHOR_BYTES = 64 * 1024

# What a SHA-256 fingerprint looks like once `loom-portal-certificate` has stripped
# openssl's `SHA256 Fingerprint=` prefix: 32 bytes as colon-separated uppercase hex.
FINGERPRINT_LENGTH = 95


@dataclass(frozen=True)
class AnchorStatus:
    """What the page knows about the box's certificate right now."""

    available: bool
    pem: bytes = b""
    fingerprint: str = ""


class AnchorFile:
    """The published pair, read fresh every time.

    Re-read rather than cached, because the certificate is replaced whenever the chart's
    pre-install Job decides it has to be -- which happens on the first deploy after a
    hostname is added, among other times. A cache here would hand out an anchor that no
    longer matches what Traefik serves, which is the one failure the whole page exists
    to prevent.
    """

    def __init__(self, pem_path: str, fingerprint_path: str):
        self.pem_path = pem_path
        self.fingerprint_path = fingerprint_path

    def read(self) -> AnchorStatus:
        pem = self._read_bytes(self.pem_path)
        if not pem or b"BEGIN CERTIFICATE" not in pem:
            return AnchorStatus(available=False)
        return AnchorStatus(available=True, pem=pem, fingerprint=self._fingerprint())

    def _fingerprint(self) -> str:
        raw = self._read_bytes(self.fingerprint_path).decode("ascii", "replace").strip()
        # Printed on the page, so anything that is not a fingerprint is dropped rather
        # than shown. A missing one costs the visitor a comparison they could have made;
        # a wrong one invites them to accept something they should not.
        if len(raw) != FINGERPRINT_LENGTH:
            return ""
        if any(character not in "0123456789ABCDEFabcdef:" for character in raw):
            return ""
        return raw.upper()

    def _read_bytes(self, path: str) -> bytes:
        try:
            with open(path, "rb") as handle:
                return handle.read(MAX_ANCHOR_BYTES)
        except OSError as error:
            logger.debug("Could not read %s: %s", path, error)
            return b""
