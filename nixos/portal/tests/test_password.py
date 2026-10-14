"""Today's password, yesterday's, and how often either may be guessed at.

The grace window is the subtle half. The rotation unit runs at midnight and the password
is read off a screen, so there is a minute every day when somebody is typing a password
the box has just replaced. Refusing them is the worst possible moment for this box to be
unhelpful, because the explanation is on the screen they already read.

Nothing here sleeps. The bucket and the delay both go through the injected clock.
"""

from doubles_portal import (
    PASSWORD,
    PREVIOUS_PASSWORD,
    FakeClock,
    settings_for,
    write_passwords,
)

from loom_portal.password import AttemptBucket, PasswordFile, PasswordGate


def gate_for(tmp_path, clock=None, attempts=10, window=60.0, delay=1.0):
    clock = clock or FakeClock()
    settings = settings_for(tmp_path)
    write_passwords(settings)
    return PasswordGate(
        passwords=PasswordFile(settings.password_path, settings.previous_password_path),
        bucket=AttemptBucket(clock, attempts, window),
        clock=clock,
        wrong_delay_s=delay,
    )


def test_todays_password_is_accepted(tmp_path):
    assert gate_for(tmp_path).check(PASSWORD).accepted


def test_yesterdays_password_is_accepted_too(tmp_path):
    """The minute after midnight, on a password somebody read off the screen."""
    assert gate_for(tmp_path).check(PREVIOUS_PASSWORD).accepted


def test_anything_else_is_refused(tmp_path):
    gate = gate_for(tmp_path)
    for attempt in ["", "wrong", PASSWORD + "x", PASSWORD.upper()]:
        assert not gate.check(attempt).accepted


def test_a_box_with_no_password_yet_lets_nobody_in(tmp_path):
    """Both files are absent for the first seconds of a boot, and `"" == ""` is true."""
    settings = settings_for(tmp_path)
    clock = FakeClock()
    gate = PasswordGate(
        passwords=PasswordFile(settings.password_path, settings.previous_password_path),
        bucket=AttemptBucket(clock, 10, 60.0),
        clock=clock,
        wrong_delay_s=0.0,
    )
    assert not gate.check("").accepted
    assert not gate.check("anything").accepted


def test_a_wrong_answer_costs_a_pause_and_a_right_one_does_not(tmp_path):
    clock = FakeClock()
    gate = gate_for(tmp_path, clock=clock, delay=1.0)

    gate.check("wrong")
    assert clock.slept == 1.0

    gate.check(PASSWORD)
    assert clock.slept == 1.0


def test_the_bucket_refuses_once_the_window_is_full(tmp_path):
    clock = FakeClock()
    gate = gate_for(tmp_path, clock=clock, attempts=3, window=60.0, delay=0.0)

    for _ in range(3):
        assert not gate.check("wrong").throttled

    throttled = gate.check(PASSWORD)
    assert throttled.throttled
    assert not throttled.accepted
    # And it says when, so the page can set Retry-After rather than guess.
    assert 0 < throttled.retry_after_s <= 60.0


def test_the_bucket_recovers_after_the_window(tmp_path):
    clock = FakeClock()
    gate = gate_for(tmp_path, clock=clock, attempts=2, window=60.0, delay=0.0)

    gate.check("wrong")
    gate.check("wrong")
    assert gate.check(PASSWORD).throttled

    clock.sleep(61.0)
    assert gate.check(PASSWORD).accepted


def test_a_throttled_attempt_is_not_also_delayed(tmp_path):
    """Somebody being refused for asking too often should be told so at once."""
    clock = FakeClock()
    gate = gate_for(tmp_path, clock=clock, attempts=1, window=60.0, delay=5.0)

    gate.check("wrong")
    before = clock.slept
    assert gate.check("wrong").throttled
    assert clock.slept == before
