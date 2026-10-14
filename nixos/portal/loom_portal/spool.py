"""Asking root for a certificate, without being root.

Minting a client identity needs the mutual TLS CA's *private key*, which lives in a
cluster secret. The obvious implementation is for this service to run
`loom-client-certificate` itself -- and it would then be a network-facing process, the
only one a visitor can reach, holding the operator's kubeconfig. A compromise of it would
be a compromise of the cluster.

So the work is split, and this module is the visitor's side of the split:

    this service            writes  requests/<token>.req
    systemd path unit       notices the glob
    loom-portal-issue       runs as root, drains the directory, and writes
                            bundles/<token>/  or  bundles/<token>.error
    this service            reads the bundle and hands it to the browser

Three properties are worth stating, because each of them is a choice:

  * **The token is the filename and carries no meaning.** 32 hex characters from
    `secrets.token_hex`, validated on both sides before it is ever joined to a path. The
    only content of a request file is an optional label, which the issuer re-validates
    rather than trusting.

  * **The spool directories are not readable by this service.** They are `0730
    root:loom-portal`, so this process may create, stat and unlink *by name* and may not
    enumerate. A compromise of it therefore cannot list other visitors' tokens. That is
    also why the in-flight count below is kept in memory rather than by counting files:
    the obvious implementation is the one the permissions forbid.

  * **Files are written to a temporary name and renamed.** The issuer globs `*.req`, so a
    half-written request can never match; it builds its answer in `.<token>.work` and
    renames the finished directory into place, so this side can never read half a bundle.
"""

import io
import logging
import os
import re
import secrets
import threading
import zipfile
from dataclasses import dataclass
from enum import StrEnum

from loom_portal.clock import Clock

logger = logging.getLogger(__name__)

TOKEN_BYTES = 16
TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")

# What a visitor may call their certificate. Lowercase, no dots and no underscores, which
# is narrower than `generate_client_certificate.sh` accepts on purpose: this one arrives
# from a form, and the issuer builds a filename and an X.509 subject out of it.
LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")
DEFAULT_LABEL = "visitor"

REQUEST_SUFFIX = ".req"
ERROR_SUFFIX = ".error"

# How often the wait looks. Fast enough that a certificate that took two seconds to make
# is served in two seconds, slow enough that a page held open costs nothing.
POLL_INTERVAL_S = 0.1

# An error file is one word. Anything longer is not something the issuer wrote.
MAX_ERROR_BYTES = 256


class BundleFormat(StrEnum):
    """What the visitor asked to be given."""

    # The identity on its own, for a browser or a phone. This is the one almost everybody
    # wants: double-click, or tap, and the certificate is installed.
    P12 = "p12"
    # Everything the issuer produced, zipped: the PKCS#12, the PEM pair for `curl --cert`
    # and `mc`, the trust anchor and the README. For somebody who is going to use this
    # from a terminal.
    ZIP = "zip"


class IssuanceState(StrEnum):
    DELIVERED = "delivered"
    # The box is already making as many certificates as it is willing to make at once.
    BUSY = "busy"
    # Nothing came back inside the deadline.
    TIMED_OUT = "timed-out"
    # Loom has not come up far enough for a CA to exist. On a first boot this is the
    # normal answer for a long time.
    CLUSTER_NOT_READY = "cluster-not-ready"
    # The issuer ran and failed. The journal has why.
    ISSUER_FAILED = "issuer-failed"
    # The request never got as far as the issuer.
    REFUSED = "refused"


# What the root issuer may write into `<token>.error`, and what this side makes of it.
# Anything it has never heard of is a failure rather than a silence.
ERROR_STATES = {
    "cluster-not-ready": IssuanceState.CLUSTER_NOT_READY,
    "issuer-failed": IssuanceState.ISSUER_FAILED,
}


@dataclass(frozen=True)
class LabelResult:
    """A submitted label, after validation."""

    ok: bool
    label: str = DEFAULT_LABEL
    reason: str = ""


@dataclass(frozen=True)
class IssuanceOutcome:
    """What came back, ready to be turned into a response."""

    state: IssuanceState
    bundle: bytes = b""
    filename: str = ""
    content_type: str = ""
    detail: str = ""


def validate_label(given: str) -> LabelResult:
    """Accept a label, or say why not.

    An empty one is accepted and becomes `visitor`: the field is optional, and a visitor
    who ignores it should not be refused for it.
    """
    stripped = given.strip().lower()
    if not stripped:
        return LabelResult(ok=True)
    if not LABEL_PATTERN.match(stripped):
        return LabelResult(
            ok=False,
            reason="A name may use lowercase letters, digits and hyphens, "
            "and may be at most 24 characters long.",
        )
    return LabelResult(ok=True, label=stripped)


class Spool:
    """The visitor's side of the request/answer directory pair."""

    def __init__(
        self,
        requests_dir: str,
        bundles_dir: str,
        clock: Clock,
        max_in_flight: int,
        timeout_s: float,
    ):
        self.requests_dir = requests_dir
        self.bundles_dir = bundles_dir
        self.clock = clock
        self.timeout_s = timeout_s
        self.max_in_flight = max_in_flight
        # A counter under a lock rather than a semaphore, because the thing being
        # expressed is "how many are in flight" and the page says that number back to the
        # visitor. A semaphore would hold the same state and refuse to be read.
        self._lock = threading.Lock()
        self._in_flight = 0

    def issue(self, label: str, want: BundleFormat) -> IssuanceOutcome:
        """Ask for a certificate and wait for it.

        Returns rather than raises for every outcome, because every one of them is a
        page the visitor has to be shown.
        """
        if not self._take_slot():
            return IssuanceOutcome(
                state=IssuanceState.BUSY,
                detail="The box is issuing a certificate for somebody else.",
            )
        try:
            token = secrets.token_hex(TOKEN_BYTES)
            if not self._write_request(token, label):
                return IssuanceOutcome(
                    state=IssuanceState.REFUSED,
                    detail="The request could not be written.",
                )
            return self._await(token, want)
        finally:
            self._give_slot()

    def _take_slot(self) -> bool:
        with self._lock:
            if self._in_flight >= self.max_in_flight:
                return False
            self._in_flight += 1
            return True

    def _give_slot(self) -> None:
        with self._lock:
            self._in_flight -= 1

    def _write_request(self, token: str, label: str) -> bool:
        temporary = os.path.join(self.requests_dir, f".{token}.tmp")
        final = os.path.join(self.requests_dir, token + REQUEST_SUFFIX)
        try:
            # The dot-prefixed name is what keeps the issuer's `*.req` glob from matching
            # a file that is still being written.
            with open(
                os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(f"label={label}\n")
            os.replace(temporary, final)
            return True
        except OSError as error:
            logger.warning("Could not write a certificate request: %s", error)
            return False

    def _await(self, token: str, want: BundleFormat) -> IssuanceOutcome:
        bundle_dir = os.path.join(self.bundles_dir, token)
        error_file = os.path.join(self.bundles_dir, token + ERROR_SUFFIX)
        deadline = self.clock.now() + self.timeout_s

        while self.clock.now() < deadline:
            if os.path.isdir(bundle_dir):
                outcome = self._collect(bundle_dir, want)
                _remove_tree(bundle_dir)
                return outcome
            if os.path.exists(error_file):
                reason = _read_reason(error_file)
                _remove(error_file)
                return IssuanceOutcome(
                    state=ERROR_STATES.get(reason, IssuanceState.ISSUER_FAILED),
                    detail=reason,
                )
            self.clock.sleep(POLL_INTERVAL_S)

        # The request may still be sitting there unread -- the issuer could be busy with
        # somebody else's. Taking it back is what keeps an abandoned page from costing the
        # box a key generation nobody is waiting for any more.
        _remove(os.path.join(self.requests_dir, token + REQUEST_SUFFIX))
        return IssuanceOutcome(
            state=IssuanceState.TIMED_OUT,
            detail="Nothing came back in time.",
        )

    def _collect(self, bundle_dir: str, want: BundleFormat) -> IssuanceOutcome:
        try:
            names = sorted(os.listdir(bundle_dir))
        except OSError as error:
            logger.warning("Could not read a finished bundle: %s", error)
            return IssuanceOutcome(
                state=IssuanceState.ISSUER_FAILED, detail="unreadable-bundle"
            )

        identity = next((name for name in names if name.endswith(".p12")), "")
        if not identity:
            return IssuanceOutcome(
                state=IssuanceState.ISSUER_FAILED, detail="incomplete-bundle"
            )

        if want is BundleFormat.P12:
            payload = _read_file(os.path.join(bundle_dir, identity))
            return IssuanceOutcome(
                state=IssuanceState.DELIVERED,
                bundle=payload,
                filename=identity,
                content_type="application/x-pkcs12",
            )

        stem = identity[: -len(".p12")]
        return IssuanceOutcome(
            state=IssuanceState.DELIVERED,
            bundle=_zip(bundle_dir, names),
            filename=f"{stem}.zip",
            content_type="application/zip",
        )


def _zip(bundle_dir: str, names: list[str]) -> bytes:
    """Everything the issuer wrote, in one archive.

    Stored rather than deflated: the five files are a few kilobytes of PEM and a README,
    and a stored archive is one that every unzip on every platform opens.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        for name in names:
            archive.writestr(name, _read_file(os.path.join(bundle_dir, name)))
    return buffer.getvalue()


def _read_file(path: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as error:
        logger.warning("Could not read %s: %s", path, error)
        return b""


def _read_reason(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read(MAX_ERROR_BYTES).strip()
    except (OSError, UnicodeDecodeError):
        return ""


def _remove(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _remove_tree(path: str) -> None:
    """Take a delivered bundle back off the disk.

    Best effort, and immediately: the PKCS#12 carries an unencrypted private key, so the
    moment it has been handed to the browser there is no reason for it to exist. The
    root issuer reaps whatever this misses.
    """
    try:
        for name in os.listdir(path):
            _remove(os.path.join(path, name))
        os.rmdir(path)
    except OSError as error:
        logger.debug("Could not remove %s: %s", path, error)
