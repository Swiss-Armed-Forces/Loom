"""The environment `mc` is handed.

`mc` is the only thing on this side that moves bytes, and it refuses to start at all
when the environment is wrong -- which is exactly the environment a systemd unit has.
These are cheap assertions about the values, so that the expensive way of finding out (a
stick plugged into a real box, and a journal line about `getent`) is not the way.
"""

import os
import sys

from loom_usb_ingest.transfer import _stream_json, mc_env

CONFIG_DIR = "/run/loom/usb/mc"

# What a root system service actually sees. Systemd sets `$HOME` only for units that
# set `User=` (systemd.exec(5)) and the ingest units do not, so the value is absent --
# while `PATH` is the one the wrapper built.
UNIT_ENVIRONMENT = {
    "PATH": "/nix/store/whatever/bin",
    "INVOCATION_ID": "e4a1",
}


def test_mc_has_a_home_when_the_unit_has_none() -> None:
    # Without this, mc dies building its flag set -- before MC_CONFIG_DIR is ever read
    # -- because resolving the home directory shells out to `getent`, which is not on
    # the unit's PATH.
    env = mc_env(CONFIG_DIR, UNIT_ENVIRONMENT)

    assert env["HOME"]
    assert env["MC_CONFIG_DIR"] == CONFIG_DIR


def test_an_empty_home_counts_as_none() -> None:
    # mc reads `HOME=` as unset and goes looking for `getent` just the same, so an
    # empty value has to be replaced rather than preserved.
    assert mc_env(CONFIG_DIR, dict(UNIT_ENVIRONMENT, HOME=""))["HOME"]


def test_a_real_home_is_left_alone() -> None:
    # An operator running the binary by hand keeps their own home directory: mc only
    # needs the value to exist, and overriding it would hide their `mc` state from
    # them for no gain.
    env = mc_env(CONFIG_DIR, dict(UNIT_ENVIRONMENT, HOME="/home/loom"))

    assert env["HOME"] == "/home/loom"


def test_the_rest_of_the_environment_survives() -> None:
    # The unit's PATH is in here, and every binary mc reaches for -- its mount helpers,
    # and `getent` on a box that has one -- is found through it. Building the
    # environment from scratch rather than from the unit's would drop it.
    env = mc_env(CONFIG_DIR, UNIT_ENVIRONMENT)

    assert env["PATH"] == UNIT_ENVIRONMENT["PATH"]
    assert env["INVOCATION_ID"] == UNIT_ENVIRONMENT["INVOCATION_ID"]
    assert env["MC_UPDATE"] == "off"


def test_a_variable_that_backs_a_flag_is_spelled_as_a_bool() -> None:
    # `MC_DISABLE_PAGER` feeds `--disable-pager`, and mc parses every flag-backed
    # variable with Go's `strconv.ParseBool`: `on` is not a word that accepts, and it
    # is fatal rather than ignored -- mc refuses to run at all, which on this box means
    # a stick that copies nothing. Only `true` and `false` are safe to write here.
    assert mc_env(CONFIG_DIR, UNIT_ENVIRONMENT)["MC_DISABLE_PAGER"] in ("true", "false")


def _script(source: str) -> list[str]:
    """A stand-in for mc: the events it streams are the whole of its interface."""
    return [sys.executable, "-c", source]


def test_a_command_that_dies_before_saying_anything_is_still_a_failure() -> None:
    # The `getent` failure in the flesh: mc that will not start writes plain text to
    # stderr and streams no events at all. Counted as nothing, that run is
    # indistinguishable from an empty stick -- the operator would be told that a
    # drive full of documents was copied successfully.
    events = list(
        _stream_json(
            _script(
                "import sys; sys.stderr.write('mc: <ERROR> Unable to get"
                " mcConfigDir.\\n'); sys.exit(1)"
            ),
            dict(os.environ),
        )
    )

    assert [event["status"] for event in events] == ["error"]
    assert "mcConfigDir" in events[0]["error"]["message"]


def test_a_silent_non_zero_exit_still_says_something() -> None:
    # Nothing on stderr either, which leaves the exit status as the only fact there
    # is about it. Still better than a row claiming success.
    events = list(_stream_json(_script("raise SystemExit(3)"), dict(os.environ)))

    assert "3" in events[0]["error"]["message"]


def test_events_from_a_command_that_succeeds_are_passed_through() -> None:
    events = list(
        _stream_json(
            _script('print(\'{"status": "success", "size": 12}\')'),
            dict(os.environ),
        )
    )

    assert events == [{"status": "success", "size": 12}]
