"""Which clients have said they are finished with the page.

A connectivity probe from a client that has not pressed the button gets the same
redirect it has always got. One that has gets the answer its operating system is
looking for, and the OS then stops warning about this network -- which is the whole
feature, and the reason `portal.py` phrases it as "the redirect is the default and the
success is the exception".

A marker file per client, in a directory on tmpfs. Three things make that the shape
rather than a set in memory:

  * **It survives a restart.** The unit carries `Restart=always` with `RestartSec=5`,
    and the symptom of losing this state is precisely the symptom the feature exists to
    remove: Apple re-probes every sixty seconds, so a phone whose marker went away has
    its captive sheet raised again on an owner who is three rooms from the box and has
    no idea why.

  * **It dies at reboot**, because `/run` is tmpfs. A box that rebooted has handed out
    new leases and quite possibly has a new set of people in the room, and "this device
    agreed to be told there is internet" is not a fact worth carrying across that. The
    lie lasts one boot and no longer, with nothing to sweep it.

  * **The directory is `0730 root:loom-portal`** -- create, stat and unlink by name,
    never enumerate -- for the reason `spool.py` gives about tokens. Nothing lists it,
    and nothing has to: a /24 with a hundred-address pool caps it at a hundred empty
    files.

The filename is a keyed digest and not the address.

An address out of a header must never be joined to a path verbatim, so it has to become
*some* fixed-shape token, and a digest is the token that is also not a record of who was
here. `password.py` compares with `hmac.compare_digest` for a related reason; the rule
itself is the one this box runs on, that it keeps no record of who used it. The key is
drawn once per boot, kept beside the markers, and goes away with `/run`, so the
directory cannot be read back into addresses even by somebody who can read it.
"""

import hmac
import logging
import os
import secrets

from loom_portal.clock import Clock

logger = logging.getLogger(__name__)

# The per-boot key, beside the markers it names. Dot-prefixed so it cannot collide with
# a digest, which is hex.
KEY_NAME = ".key"
KEY_BYTES = 32


class ValidatedClients:
    """The set of clients whose probes get the vendor's success answer."""

    def __init__(self, directory: str, clock: Clock, ttl_s: float):
        self.directory = directory
        self.clock = clock
        self.ttl_s = ttl_s
        self._key: bytes | None = None

    # -- the key ---------------------------------------------------------------------

    def _load_key(self) -> bytes | None:
        """The per-boot key, drawn on first use.

        Whoever wins the race, everybody ends up with the same key. A second key would
        not fail -- it would silently forget every client marked under the first, and
        take the "this directory is not a list of addresses" property with it, since an
        unkeyed digest is just a digest of the address.

        So the file appears complete or not at all: the bytes are written to a
        temporary and `os.link` publishes them under the real name, which fails rather
        than clobbers if somebody got there first. Creating the name and then filling
        it would leave a window in which the loser reads an empty file -- and the whole
        server is threaded, so that empty value would be cached on `self._key` for
        every request after it.
        """
        if self._key is not None:
            return self._key

        path = os.path.join(self.directory, KEY_NAME)
        key = self._read_key(path)
        if key is None:
            self._publish_key(path)
            key = self._read_key(path)
        if key is None:
            logger.warning("No marker key; this client cannot be remembered.")
            return None
        self._key = key
        return self._key

    def _read_key(self, path: str) -> bytes | None:
        """The key on disk, if it is there and is a whole one.

        The length check is what makes a truncated file heal rather than poison every
        digest from here on.
        """
        try:
            with open(path, "rb") as handle:
                existing = handle.read()
        except OSError:
            return None
        return existing if len(existing) == KEY_BYTES else None

    def _publish_key(self, path: str) -> None:
        """Draw a key and put it there, unless somebody already has.

        Never raises, and never reports: the caller re-reads either way, and a failure
        here is indistinguishable from losing the race.
        """
        temporary = os.path.join(self.directory, f"{KEY_NAME}.{secrets.token_hex(8)}")
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(descriptor, secrets.token_bytes(KEY_BYTES))
            finally:
                os.close(descriptor)
            try:
                os.link(temporary, path)
            except FileExistsError:
                if self._read_key(path) is not None:
                    # Somebody else published first. Theirs is as good as ours, and
                    # the caller is about to read it.
                    return
                # There is a file and it is not a key -- truncated, or written by
                # something that died between creating and filling it. Replaced
                # rather than left, because a short key read back is an *unkeyed*
                # digest of the address, which is both a forgotten marker set and
                # the loss of the one property the keying is for. `os.replace` is
                # atomic, so a reader sees the old file or the new one.
                os.replace(temporary, path)
        except OSError as error:
            logger.warning("Could not write the marker key: %s", error)
        finally:
            try:
                os.unlink(temporary)
            except OSError:
                pass

    def _name_for(self, address: str) -> str | None:
        """The filename for a client, or `None` if there is no key to make one with."""
        key = self._load_key()
        if key is None:
            return None
        return hmac.new(key, address.encode("utf-8"), "sha256").hexdigest()

    # -- the two operations ----------------------------------------------------------

    def mark(self, address: str) -> bool:
        """Remember this client.

        False if it could not be remembered.         False rather than an exception, and
        the caller shows the page either way: the         only thing that makes this
        fail is a directory the service cannot write, and a         visitor standing at
        a page is owed an answer rather than a traceback.
        """
        if not address:
            return False
        name = self._name_for(address)
        if name is None:
            return False
        path = os.path.join(self.directory, name)
        try:
            # Truncating an existing marker is the point rather than a side effect: a
            # client that presses the button again has its clock restarted.
            with open(path, "wb"):
                pass
            # Stamped from the clock rather than left to the filesystem, so the one
            # source of time in this class is the seam the suite substitutes. An empty
            # file plus its mtime, rather than a timestamp written inside it: there is
            # then no content to parse and no half-written marker to read.
            stamp = self.clock.wall()
            os.utime(path, (stamp, stamp))
        except OSError as error:
            logger.warning("Could not mark a client as finished: %s", error)
            # Taken away again if it got as far as existing. Returning False leaves the
            # page telling the visitor the button did not take, and a marker that
            # outlived that message would have the next probe contradict it -- with the
            # filesystem's own mtime, which is not the clock this class reads.
            try:
                os.unlink(path)
            except OSError:
                pass
            return False
        return True

    def has(self, address: str) -> bool:
        """Whether this client pressed the button, recently enough.

        An empty address is never anything. Something that dialled the loopback port
        directly carries no `X-Loom-Client` at all, and the one thing that must not
        happen is for the absence of the header to read as "everybody".
        """
        if not address:
            return False
        name = self._name_for(address)
        if name is None:
            return False

        path = os.path.join(self.directory, name)
        try:
            marked = os.stat(path).st_mtime
        except OSError:
            return False

        if self.clock.wall() - marked <= self.ttl_s:
            return True

        # Expired. Removed on the way past rather than by anything periodic -- this is
        # the only code that knows the name, since nothing may enumerate the directory.
        try:
            os.unlink(path)
        except OSError:
            pass
        return False
