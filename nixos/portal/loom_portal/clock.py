"""Time, as a seam.

Two things here depend on the passage of time: the token bucket in `password.py` and the
wait for a certificate in `spool.py`. Both have deadlines measured in seconds, and a suite
that exercised them against the real clock would either sleep for real -- which makes a
check that runs at build time cost a minute -- or assert nothing about the deadline at
all.

So the clock is passed in. A class with a working implementation rather than a Protocol,
the same shape `loom_ready.cluster.Commands` has and for the same reason: the double in
`tests/doubles.py` subclasses it, so the constructor it is handed to cannot drift away
from what the double provides. `FakeClock.sleep` advances a stored float instead of
blocking, which is also how the spool test simulates the root issuer dropping a bundle
mid-wait -- the callback fires on a tick that costs nothing.

Monotonic rather than wall clock. Everything measured here is an interval, and the box
has no NTP -- it is an island -- so a wall clock that steps backwards when something
finally sets the time would hang a wait or reset a bucket.
"""

import time


class Clock:
    """The real one."""

    def now(self) -> float:
        """Seconds, from an arbitrary origin.

        Only differences are meaningful.
        """
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        """Block for roughly that long."""
        time.sleep(seconds)
