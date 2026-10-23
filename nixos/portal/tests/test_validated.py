"""The marker files, and the three properties that made them files.

A set in memory would be shorter and would pass a test that only checked mark-then-has.
What it would not do is survive a restart, which is the whole reason this is on disk --
so that property is asserted here directly, by building a second `ValidatedClients` over
the same directory rather than by hoping.
"""

import os

from doubles_portal import FakeClock

from loom_portal.settings import DEFAULT_VALIDATED_TTL_S
from loom_portal.validated import ValidatedClients

CLIENT = "10.13.37.137"
OTHER = "10.13.37.138"


def clients(root, clock: FakeClock | None = None) -> ValidatedClients:
    return ValidatedClients(
        directory=str(root), clock=clock or FakeClock(), ttl_s=DEFAULT_VALIDATED_TTL_S
    )


def test_a_marked_client_is_remembered(tmp_path):
    validated = clients(tmp_path)
    assert not validated.has(CLIENT)
    assert validated.mark(CLIENT)
    assert validated.has(CLIENT)


def test_marking_one_client_does_not_mark_another(tmp_path):
    """The property a global flag would silently break.

    Without it the first visitor to press the button would hand a success answer to a
    phone that joined thirty seconds ago and has never seen the page.
    """
    validated = clients(tmp_path)
    validated.mark(CLIENT)
    assert not validated.has(OTHER)


def test_an_empty_address_is_never_anything(tmp_path):
    """Something that dialled the loopback port carries no header at all.

    The one thing that must not happen is for the absence of the header to read as
    "everybody".
    """
    validated = clients(tmp_path)
    assert not validated.mark("")
    assert not validated.has("")


def test_a_marker_outlives_the_process_that_wrote_it(tmp_path):
    """The whole justification for this being a file.

    `Restart=always` with `RestartSec=5` is a real window, and a client whose marker
    went away has its captive sheet raised again within sixty seconds -- on somebody who
    is nowhere near the box and has no idea why.
    """
    clients(tmp_path).mark(CLIENT)
    assert clients(tmp_path).has(CLIENT)


def test_a_marker_expires_at_the_lease_time(tmp_path):
    clock = FakeClock()
    validated = clients(tmp_path, clock)
    validated.mark(CLIENT)

    clock.current += DEFAULT_VALIDATED_TTL_S - 1
    assert validated.has(CLIENT)

    clock.current += 2
    assert not validated.has(CLIENT)


def test_an_expired_marker_is_removed_on_the_way_past(tmp_path):
    """Nothing enumerates this directory, so nothing else can sweep it."""
    clock = FakeClock()
    validated = clients(tmp_path, clock)
    validated.mark(CLIENT)
    assert len(_markers(tmp_path)) == 1

    clock.current += DEFAULT_VALIDATED_TTL_S + 1
    validated.has(CLIENT)
    assert _markers(tmp_path) == []


def test_the_directory_is_not_a_list_of_who_was_here(tmp_path):
    """A keyed digest, not the address.

    The address must not be joined to a path verbatim in any case, and this is the
    other half of why: a box whose premise is that it keeps no record of who used it
    should not keep one here either.
    """
    clients(tmp_path).mark(CLIENT)
    assert CLIENT not in "".join(os.listdir(tmp_path))


def test_the_key_is_drawn_once_and_reused(tmp_path):
    """A second key would not fail -- it would forget every client marked under the
    first, which is the same bug as losing the directory and harder to see."""
    clients(tmp_path).mark(CLIENT)
    before = _markers(tmp_path)

    clients(tmp_path).mark(CLIENT)
    assert _markers(tmp_path) == before


def test_a_truncated_key_heals_rather_than_poisoning_every_digest(tmp_path):
    """The failure mode a plain create-then-write leaves behind.

    An empty or short `.key` read back as the key makes every digest an *unkeyed* hash
    of the address -- which orphans every marker written under the real key, and quietly
    undoes the one property the keying is for. The server is threaded and caches the
    key, so one bad read poisons every request after it.
    """
    (tmp_path / ".key").write_bytes(b"")

    validated = clients(tmp_path)
    assert validated.mark(CLIENT)
    assert validated.has(CLIENT)
    assert (tmp_path / ".key").stat().st_size == 32


def test_a_second_reader_gets_the_first_one_s_key(tmp_path):
    """Two instances over one directory must agree, or the second forgets the first."""
    first = clients(tmp_path)
    first.mark(CLIENT)
    assert clients(tmp_path).has(CLIENT)
    # And no temporary left behind by publishing it.
    assert sorted(os.listdir(tmp_path)) == sorted([".key", *_markers(tmp_path)])


def test_an_unwritable_directory_refuses_rather_than_raises(tmp_path):
    """A visitor standing at a page is owed an answer, not a traceback."""
    unwritable = tmp_path / "gone"
    validated = clients(unwritable)
    assert not validated.mark(CLIENT)
    assert not validated.has(CLIENT)


def test_a_mark_that_failed_leaves_nothing_behind(tmp_path, monkeypatch):
    """`mark` returning False and `has` returning True would have the page tell the
    visitor the button did not take and the next probe say otherwise."""
    validated = clients(tmp_path)

    def refuse(*_args, **_kwargs):
        raise OSError("no")

    # The one call with no injectable seam: stamping the file after creating it.
    monkeypatch.setattr(os, "utime", refuse)
    assert not validated.mark(CLIENT)
    assert not validated.has(CLIENT)
    assert _markers(tmp_path) == []


def _markers(root) -> list[str]:
    """Everything but the key.

    The suite may enumerate; the service may not.
    """
    return sorted(name for name in os.listdir(root) if not name.startswith("."))
