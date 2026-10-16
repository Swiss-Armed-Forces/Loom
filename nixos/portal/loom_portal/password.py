"""Today's password, and how many times it may be guessed at.

The password is what stands between anyone on the appliance segment and a client
certificate. It is generated on the box by `loom-portal-password.service`, rotated
daily, and shown on the console's own login screen -- so the authorisation it represents
is "this person has stood in front of the box", which is the same authorisation every
other thing on this appliance runs on.

Two files, not one. The rotation writes the outgoing password to `password.previous`
before writing the new one, so somebody who read the screen at 23:59 and types it at
00:01 is let in. Without that, the one minute a day when the box is least able to
explain itself is also the one minute it refuses a correct answer.

Both are read fresh on every attempt. Rotation therefore needs no restart of this
service, which matters because restarting it would drop every in-flight certificate
wait.
"""

import hmac
import logging
import threading
from dataclasses import dataclass

from loom_portal.clock import Clock

logger = logging.getLogger(__name__)

# A four-word EFF passphrase with dots is about thirty characters. The cap is not a
# policy, it is a bound on how much of a request body is worth comparing.
MAX_PASSWORD_BYTES = 256


@dataclass(frozen=True)
class AttemptAllowance:
    """Whether another attempt may be made, and when the next one may be."""

    allowed: bool
    retry_after_s: float = 0.0


@dataclass(frozen=True)
class PasswordCheck:
    """The verdict on one submitted password."""

    accepted: bool
    throttled: bool = False
    retry_after_s: float = 0.0


class PasswordFile:
    """The current password and the one it replaced."""

    def __init__(self, path: str, previous_path: str):
        self.path = path
        self.previous_path = previous_path

    def current(self) -> str:
        return self._read(self.path)

    def previous(self) -> str:
        return self._read(self.previous_path)

    def _read(self, path: str) -> str:
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read(MAX_PASSWORD_BYTES).strip()
        except (OSError, UnicodeDecodeError) as error:
            logger.debug("Could not read %s: %s", path, error)
            return ""


class AttemptBucket:
    """A token bucket over password attempts, counted for the whole process.

    Global rather than per client address, which is a deliberate trade. Per-address
    buckets are the usual shape, but they require the server to know who is asking --
    which means nginx forwarding `X-Real-IP` and this process holding a table of
    visitors. On a box whose entire premise is that it keeps no record of who used it,
    counting attempts rather than attempters is the smaller thing to build and the
    smaller thing to leak. What it costs is that one person hammering the form can
    briefly lock out the room; the window is a minute, and the console can always issue
    a certificate by hand.
    """

    def __init__(self, clock: Clock, limit: int, window_s: float):
        self.clock = clock
        self.limit = limit
        self.window_s = window_s
        self._attempts: list[float] = []
        # `server.serve` is a ThreadingHTTPServer with daemon threads, so `take` runs
        # concurrently -- and the rebuild-then-append below is not atomic: two threads
        # can both read `len(...) == limit - 1` and both append, and the comprehension
        # can drop an entry a third appended between the read and the rebind. This is
        # the one shared mutable object on the request path of the listener that gates
        # getting into Loom, and `Spool._take_slot` next door already takes the same
        # care.
        self._lock = threading.Lock()

    def take(self) -> AttemptAllowance:
        now = self.clock.now()
        with self._lock:
            self._attempts = [at for at in self._attempts if now - at < self.window_s]
            if len(self._attempts) >= self.limit:
                oldest = min(self._attempts)
                return AttemptAllowance(
                    allowed=False, retry_after_s=self.window_s - (now - oldest)
                )
            self._attempts.append(now)
        return AttemptAllowance(allowed=True)


class PasswordGate:
    """The bucket and the comparison, as one decision."""

    def __init__(
        self,
        passwords: PasswordFile,
        bucket: AttemptBucket,
        clock: Clock,
        wrong_delay_s: float,
    ):
        self.passwords = passwords
        self.bucket = bucket
        self.clock = clock
        self.wrong_delay_s = wrong_delay_s

    def check(self, given: str) -> PasswordCheck:
        allowance = self.bucket.take()
        if not allowance.allowed:
            return PasswordCheck(
                accepted=False, throttled=True, retry_after_s=allowance.retry_after_s
            )

        if given and self._matches(given):
            return PasswordCheck(accepted=True)

        # Only on a wrong answer, and only after the bucket has already been charged, so
        # a visitor who is being throttled is told so immediately rather than made to
        # wait for the privilege.
        self.clock.sleep(self.wrong_delay_s)
        return PasswordCheck(accepted=False)

    def _matches(self, given: str) -> bool:
        current = self.passwords.current()
        previous = self.passwords.previous()

        # Compared as bytes, not as str. `hmac.compare_digest` raises TypeError for a
        # str argument containing any non-ASCII character, and `given` is whatever a
        # browser sent: `parse_form` UTF-8-decodes arbitrary bytes and is documented
        # never to raise, `server.py` has no try/except around `portal.handle`, so one
        # umlaut typed into the form drops the connection and leaves a traceback in
        # the journal instead of saying "wrong password". On the one image built with
        # `--keymap` support, where a non-US layout is the expected case. The encoding
        # is deterministic, so the constant-time property is preserved.
        given_bytes = given.encode()

        # Both comparisons always run, and an empty stored password never matches. A box
        # whose rotation unit has not run yet has no password, and `"" == ""` would
        # otherwise let everybody in during exactly that window.
        matched = False
        if current:
            matched |= hmac.compare_digest(given_bytes, current.encode())
        if previous:
            matched |= hmac.compare_digest(given_bytes, previous.encode())
        return matched
