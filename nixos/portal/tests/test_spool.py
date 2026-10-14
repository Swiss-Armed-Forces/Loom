"""The visitor's side of the request/answer directory pair.

The root issuer is played by a callback on `FakeClock.sleep`, which fires on a tick that
costs nothing: the wait loop polls, the "issuer" drops a bundle on the third poll, and
the loop finds it. That is the whole of the concurrency here, and it is enough -- the
real issuer is a separate process and the only thing this side knows about it is what
appears in a directory.

What is asserted and why:

  * A half-written request can never match the issuer's `*.req` glob. Getting that wrong
    means the issuer reads an empty file and mints a certificate for the wrong label, at
    random, under load.
  * A timeout takes the request back. An abandoned page must not cost the box a key
    generation nobody is waiting for.
  * A delivered bundle is removed at once. It holds an unencrypted private key.
"""

import io
import os
import zipfile

from doubles_portal import (
    P12_BYTES,
    FakeClock,
    pending_tokens,
    place_bundle,
    place_error,
    settings_for,
)

from loom_portal.spool import (
    REQUEST_SUFFIX,
    TOKEN_PATTERN,
    BundleFormat,
    IssuanceState,
    Spool,
    validate_label,
)


def spool_for(settings, clock, timeout=5.0, max_in_flight=2) -> Spool:
    return Spool(
        requests_dir=settings.requests_dir,
        bundles_dir=settings.bundles_dir,
        clock=clock,
        max_in_flight=max_in_flight,
        timeout_s=timeout,
    )


def answering(settings, after_ticks: int, answer, consume: bool = True):
    """A clock whose Nth tick plays the part of the root issuer.

    It consumes the request before answering, because that is what the real issuer does
    and in the order it does it -- `rm` the `*.req` first, so that a path unit retrigger
    cannot hand the same request to a second run.
    """
    ticks = {"count": 0}

    def on_sleep(_now: float) -> None:
        ticks["count"] += 1
        if ticks["count"] != after_ticks:
            return
        tokens = pending_tokens(settings)
        assert tokens, "the issuer was woken with nothing to do"
        token = tokens[0]
        answer(token)
        if consume:
            os.unlink(os.path.join(settings.requests_dir, token + REQUEST_SUFFIX))

    return FakeClock(on_sleep=on_sleep)


def test_a_request_is_one_file_named_by_a_token(tmp_path):
    settings = settings_for(tmp_path)
    seen = {}

    def record(token):
        seen["token"] = token
        # Everything that is not a finished request, at the moment the issuer looks.
        seen["others"] = [
            name
            for name in os.listdir(settings.requests_dir)
            if not name.endswith(REQUEST_SUFFIX)
        ]
        place_bundle(settings, token)

    clock = answering(settings, 2, record)
    spool_for(settings, clock).issue("visitor", BundleFormat.P12)

    assert TOKEN_PATTERN.match(seen["token"])
    # The temporary name is dot-prefixed and gone by the time the request exists, so the
    # issuer's glob can never catch a partial write.
    assert not seen["others"]


def test_the_label_reaches_the_issuer(tmp_path):
    settings = settings_for(tmp_path)
    body = {}

    def record(token):
        with open(
            os.path.join(settings.requests_dir, token + REQUEST_SUFFIX),
            encoding="utf-8",
        ) as handle:
            body["text"] = handle.read()
        place_bundle(settings, token)

    spool_for(settings, answering(settings, 2, record)).issue(
        "alices-laptop", BundleFormat.P12
    )
    assert body["text"] == "label=alices-laptop\n"


def test_a_finished_bundle_is_delivered_and_removed(tmp_path):
    settings = settings_for(tmp_path)
    clock = answering(settings, 3, lambda token: place_bundle(settings, token))

    outcome = spool_for(settings, clock).issue("visitor", BundleFormat.P12)

    assert outcome.state is IssuanceState.DELIVERED
    assert outcome.bundle == P12_BYTES
    assert outcome.filename == "visitor-0123abcd.p12"
    assert outcome.content_type == "application/x-pkcs12"
    # The private key does not stay on the box a moment longer than it has to.
    assert not os.listdir(settings.bundles_dir)
    assert not pending_tokens(settings)


def test_the_zip_carries_everything_the_issuer_wrote(tmp_path):
    settings = settings_for(tmp_path)
    clock = answering(settings, 2, lambda token: place_bundle(settings, token))

    outcome = spool_for(settings, clock).issue("visitor", BundleFormat.ZIP)

    assert outcome.state is IssuanceState.DELIVERED
    assert outcome.filename == "visitor-0123abcd.zip"
    assert outcome.content_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(outcome.bundle)) as archive:
        assert sorted(archive.namelist()) == [
            "README.txt",
            "loom-server-ca.pem",
            "visitor-0123abcd.crt",
            "visitor-0123abcd.key",
            "visitor-0123abcd.p12",
        ]


def test_an_error_file_short_circuits_the_wait(tmp_path):
    settings = settings_for(tmp_path)
    clock = answering(
        settings, 2, lambda token: place_error(settings, token, "cluster-not-ready")
    )

    outcome = spool_for(settings, clock, timeout=60.0).issue(
        "visitor", BundleFormat.P12
    )

    assert outcome.state is IssuanceState.CLUSTER_NOT_READY
    # Well inside the deadline: the wait stopped on the answer rather than running out.
    assert clock.slept < 1.0
    assert not os.listdir(settings.bundles_dir)


def test_an_unknown_reason_is_a_failure_rather_than_a_silence(tmp_path):
    settings = settings_for(tmp_path)
    clock = answering(settings, 2, lambda token: place_error(settings, token, "weird"))

    outcome = spool_for(settings, clock).issue("visitor", BundleFormat.P12)
    assert outcome.state is IssuanceState.ISSUER_FAILED


def test_a_bundle_with_no_identity_in_it_is_a_failure(tmp_path):
    settings = settings_for(tmp_path)

    def empty(token):
        os.makedirs(os.path.join(settings.bundles_dir, token))

    outcome = spool_for(settings, answering(settings, 2, empty)).issue(
        "visitor", BundleFormat.P12
    )
    assert outcome.state is IssuanceState.ISSUER_FAILED


def test_a_timeout_takes_the_request_back(tmp_path):
    settings = settings_for(tmp_path)
    clock = FakeClock()

    outcome = spool_for(settings, clock, timeout=5.0).issue("visitor", BundleFormat.P12)

    assert outcome.state is IssuanceState.TIMED_OUT
    # The deadline was honoured rather than overrun, and nothing was left for the issuer
    # to pick up afterwards. The bound is loose by one poll interval because the wait is
    # a sum of floats, not a comparison against a single one.
    assert 4.8 <= clock.slept < 5.2
    assert not pending_tokens(settings)


def test_only_so_many_may_be_in_flight(tmp_path):
    """Counted in the process, because the spool directory is deliberately unreadable to
    this service on a box -- see the module header of spool.py."""
    settings = settings_for(tmp_path)
    outcomes = []

    def reenter(_now: float) -> None:
        if not outcomes:
            outcomes.append(spool.issue("visitor", BundleFormat.P12))

    clock = FakeClock(on_sleep=reenter)
    spool = spool_for(settings, clock, timeout=1.0, max_in_flight=1)
    spool.issue("visitor", BundleFormat.P12)

    assert outcomes[0].state is IssuanceState.BUSY


def test_a_label_is_validated_before_it_is_written():
    assert validate_label("").label == "visitor"
    assert validate_label("Alices-Laptop").label == "alices-laptop"

    for bad in ["../etc", "a b", "a/b", "a" * 25, "-leading", "x;y", "a.b"]:
        result = validate_label(bad)
        assert not result.ok, bad
        assert result.reason
