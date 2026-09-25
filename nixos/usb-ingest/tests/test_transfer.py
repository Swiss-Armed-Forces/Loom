"""The environment `mc` is handed.

`mc` is the only thing on this side that moves bytes, and it refuses to start at all
when the environment is wrong -- which is exactly the environment a systemd unit has.
These are cheap assertions about the values, so that the expensive way of finding out (a
stick plugged into a real box, and a journal line about `getent`) is not the way.
"""

import base64
import os
import sys

from loom_usb_ingest.transfer import (
    ALIAS,
    WaitHooks,
    _stream_json,
    install_cluster_ca,
    mc_env,
    mirror,
    wait_for_cluster,
)

CONFIG_DIR = "/run/loom/usb-state/mc"
ENDPOINT = "https://s3.loom"

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
    env = mc_env(CONFIG_DIR, ENDPOINT, UNIT_ENVIRONMENT)

    assert env["HOME"]
    assert env["MC_CONFIG_DIR"] == CONFIG_DIR


def test_an_empty_home_counts_as_none() -> None:
    # mc reads `HOME=` as unset and goes looking for `getent` just the same, so an
    # empty value has to be replaced rather than preserved.
    assert mc_env(CONFIG_DIR, ENDPOINT, dict(UNIT_ENVIRONMENT, HOME=""))["HOME"]


def test_a_real_home_is_left_alone() -> None:
    # An operator running the binary by hand keeps their own home directory: mc only
    # needs the value to exist, and overriding it would hide their `mc` state from
    # them for no gain.
    env = mc_env(CONFIG_DIR, ENDPOINT, dict(UNIT_ENVIRONMENT, HOME="/home/loom"))

    assert env["HOME"] == "/home/loom"


def test_the_rest_of_the_environment_survives() -> None:
    # The unit's PATH is in here, and every binary mc reaches for -- its mount helpers,
    # and `getent` on a box that has one -- is found through it. Building the
    # environment from scratch rather than from the unit's would drop it.
    env = mc_env(CONFIG_DIR, ENDPOINT, UNIT_ENVIRONMENT)

    assert env["PATH"] == UNIT_ENVIRONMENT["PATH"]
    assert env["INVOCATION_ID"] == UNIT_ENVIRONMENT["INVOCATION_ID"]
    assert env["MC_UPDATE"] == "off"


def test_a_variable_that_backs_a_flag_is_spelled_as_a_bool() -> None:
    # `MC_DISABLE_PAGER` feeds `--disable-pager`, and mc parses every flag-backed
    # variable with Go's `strconv.ParseBool`: `on` is not a word that accepts, and it
    # is fatal rather than ignored -- mc refuses to run at all, which on this box means
    # a stick that copies nothing. Only `true` and `false` are safe to write here.
    assert mc_env(CONFIG_DIR, ENDPOINT, UNIT_ENVIRONMENT)["MC_DISABLE_PAGER"] in (
        "true",
        "false",
    )


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


def test_the_endpoint_is_declared_in_the_environment() -> None:
    # Not registered with `mc alias set`: that command probes the endpoint and refuses
    # to record one that does not answer, so on a box still starting Loom -- the case
    # the wait below exists for -- configuring mc failed outright and the wait was
    # never reached. An environment alias needs nothing to be up.
    env = mc_env(CONFIG_DIR, ENDPOINT, UNIT_ENVIRONMENT)

    assert env[f"MC_HOST_{ALIAS}"] == ENDPOINT


def _emits(*events: str) -> str:
    """A fake mc body that streams these JSON events, one per line."""
    quoted = " ".join(f"'{event}'" for event in events)
    return f"printf '%s\\n' {quoted}"


def _fake_mc(tmp_path, body: str) -> dict[str, str]:
    """An environment whose PATH holds an `mc` that does what the test wants.

    The wait shells out, so this is the honest way to drive it: a real process, a real
    exit status, real stderr. Nothing is patched into the module.
    """
    binary = tmp_path / "bin" / "mc"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(f"#!/bin/sh\n{body}\n")
    binary.chmod(0o755)
    return {"PATH": str(binary.parent)}


def test_the_wait_ends_when_the_bucket_answers(tmp_path) -> None:
    waited = wait_for_cluster(
        "loom-intake", _fake_mc(tmp_path, "exit 0"), 5, WaitHooks(poll_s=0)
    )

    assert waited.ready
    assert waited.last_error == ""


def test_the_wait_gives_up_saying_what_it_last_heard(tmp_path) -> None:
    # The reason is the whole point of carrying it: "never answered" alone does not
    # distinguish a cluster that is still starting from a certificate the box will
    # never trust.
    env = _fake_mc(tmp_path, "echo 'mc: <ERROR> connection refused' >&2; exit 1")
    seen: list[str] = []

    waited = wait_for_cluster(
        "loom-intake", env, 0, WaitHooks(on_attempt=seen.append, poll_s=0)
    )

    assert not waited.ready
    assert "connection refused" in waited.last_error
    assert seen and "connection refused" in seen[0]


def test_the_cluster_ca_is_retried_until_it_lands(tmp_path) -> None:
    # Installing it needs the Kubernetes API, which on a box still coming up is no more
    # awake than the S3 endpoint. Done once before the wait, it never happened at all,
    # and every later call failed verification against the box's own certificate.
    attempts: list[int] = []
    probe = tmp_path / "probe"
    body = f"test -f {probe} || exit 1"

    def trust() -> bool:
        attempts.append(1)
        if len(attempts) < 3:
            return False
        probe.write_text("")
        return True

    waited = wait_for_cluster(
        "loom-intake", _fake_mc(tmp_path, body), 5, WaitHooks(trust=trust, poll_s=0)
    )

    assert waited.ready
    assert len(attempts) == 3


def test_a_cluster_that_is_already_trusted_is_not_asked_again(tmp_path) -> None:
    attempts: list[int] = []

    wait_for_cluster(
        "loom-intake",
        _fake_mc(tmp_path, "exit 0"),
        5,
        WaitHooks(trust=lambda: bool(attempts.append(1)) or True, poll_s=0),
    )

    assert len(attempts) == 1


def test_the_summary_event_is_not_a_file(tmp_path) -> None:
    # `mc mirror --json` ends with totals rather than a file, and it carries
    # `"status": "success"` like every object before it. Counted as one, a stick with
    # ten documents reported eleven and an empty volume reported one.
    env = _fake_mc(
        tmp_path,
        "printf '%s\\n' "
        '\'{"status":"success","target":"loom/b/a.txt","size":6}\' '
        '\'{"status":"success","total":6,"transferred":6,"speed":27.5}\'',
    )
    seen: list[int] = []

    result = mirror(
        "/mnt/stick",
        "loom-intake",
        "usb-crawled/x",
        env,
        lambda objects, _bytes: seen.append(objects),
    )

    assert result.objects == 1
    assert result.bytes_transferred == 6
    assert seen == [1]


def test_a_failed_object_is_counted_and_its_reason_kept(tmp_path) -> None:
    # The count and the reason are the whole of what reaches the operator when some
    # of a stick does not copy: they drive Stage.FAILED and the row in the pane.
    env = _fake_mc(
        tmp_path, _emits('{"status":"error","error":{"message":"Access Denied."}}')
    )

    result = mirror("/mnt/stick", "loom-intake", "usb-crawled/x", env)

    assert result.objects == 0
    assert result.failures == 1
    assert result.first_error == "Access Denied."


def test_the_first_error_is_the_one_kept(tmp_path) -> None:
    # Later ones are usually consequences of the first, and only one line fits.
    env = _fake_mc(
        tmp_path,
        _emits(
            '{"status":"error","error":{"message":"I/O error on page 3"}}',
            '{"status":"error","error":{"message":"Access Denied."}}',
        ),
    )

    result = mirror("/mnt/stick", "loom-intake", "usb-crawled/x", env)

    assert result.failures == 2
    assert result.first_error == "I/O error on page 3"


def test_a_partly_failed_copy_reports_both_halves(tmp_path) -> None:
    # The realistic shape: a stick with a few unreadable files. What went across has
    # to be counted, and what did not has to be named.
    env = _fake_mc(
        tmp_path,
        _emits(
            '{"status":"success","target":"loom/b/a.txt","size":6}',
            '{"status":"error","error":{"message":"Input/output error"}}',
            '{"status":"success","target":"loom/b/c.txt","size":4}',
            '{"status":"success","total":10,"transferred":10}',
        ),
    )

    result = mirror("/mnt/stick", "loom-intake", "usb-crawled/x", env)

    assert result.objects == 2
    assert result.bytes_transferred == 10
    assert result.failures == 1
    assert result.first_error == "Input/output error"


def test_an_error_event_with_nothing_in_it_still_counts(tmp_path) -> None:
    # mc does not promise a message, and a failure that is not counted is a failure
    # the operator is never told about.
    env = _fake_mc(tmp_path, _emits('{"status":"error"}'))

    result = mirror("/mnt/stick", "loom-intake", "usb-crawled/x", env)

    assert result.failures == 1


def _fake_kubectl(tmp_path, body: str) -> dict[str, str]:
    binary = tmp_path / "bin" / "kubectl"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(f"#!/bin/sh\n{body}\n")
    binary.chmod(0o755)
    return {"PATH": str(binary.parent)}


def test_the_cluster_ca_is_written_where_mc_looks_for_it(tmp_path) -> None:
    # mc trusts what is in `<config-dir>/certs/CAs`, and nothing else: this is the
    # difference between verifying the box's own certificate and skipping the check.
    pem = b"-----BEGIN CERTIFICATE-----\nnot really\n"
    encoded = base64.b64encode(pem).decode()
    config_dir = tmp_path / "mc"

    written = install_cluster_ca(
        str(config_dir),
        "loom",
        "/dev/null",
        _fake_kubectl(tmp_path, f"printf '%s' '{encoded}'"),
    )

    assert written
    certs = config_dir / "certs" / "CAs"
    assert (certs / "self-signed-cert.crt").read_bytes() == pem
    # Both secrets, because which one Traefik presents depends on how the chart was
    # deployed and a bundle costs nothing.
    assert (certs / "loom-certificate.crt").read_bytes() == pem


def test_no_certificate_yet_is_not_an_error(tmp_path) -> None:
    # The ordinary case on a box still coming up, which is why the wait retries this.
    written = install_cluster_ca(
        str(tmp_path / "mc"),
        "loom",
        "/dev/null",
        _fake_kubectl(tmp_path, "echo 'Error from server (NotFound)' >&2; exit 1"),
    )

    assert not written


def test_a_secret_that_is_not_base64_is_skipped_rather_than_written(tmp_path) -> None:
    config_dir = tmp_path / "mc"

    written = install_cluster_ca(
        str(config_dir),
        "loom",
        "/dev/null",
        _fake_kubectl(tmp_path, "printf '%s' 'not base64 at all!'"),
    )

    assert not written
    assert not list((config_dir / "certs" / "CAs").iterdir())
