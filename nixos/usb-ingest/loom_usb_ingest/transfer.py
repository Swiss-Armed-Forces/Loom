"""Getting the bytes into the intake bucket.

`mc mirror` moves the data; this module is everything around it. Classification is
deliberately NOT done here -- the crawler decides what is a loom archive and what is an
ordinary file, from range reads on the object once it has landed
(backend/crawler/crawler/archive_prescreen.py). That is why the appliance side can be a
single mirror per volume with no per-file branching, no second endpoint and no multi-
gigabyte upload through the API.
"""

import base64
import json
import logging
import os
import subprocess
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ALIAS = "loom"
CLUSTER_WAIT_TIMEOUT_S = 3600
CLUSTER_POLL_INTERVAL_S = 15


@dataclass(frozen=True)
class TransferResult:
    objects: int
    bytes_transferred: int
    failures: int
    # What the first failure said. A count on its own tells an operator that something
    # is wrong and nothing about what, and this is the only place the message can come
    # from: mc reports per-object errors as events, not as an exit status.
    first_error: str = ""


class TransferError(RuntimeError):
    pass


def _run(argv: list[str], env: dict[str, str], timeout: int = 300) -> str:
    return subprocess.run(
        argv, check=True, capture_output=True, text=True, timeout=timeout, env=env
    ).stdout


def mc_env(config_dir: str, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Environment for every `mc` call.

    `environ` is the environment to build on, and defaults to this process's. It is a
    parameter so that the tests can hand in the environment a systemd unit has without
    editing the one they are running in.

    `MC_UPDATE=off` is policy rather than tuning, the same policy
    `OPENCODE_DISABLE_MODELS_FETCH` states in console.nix: this box makes no outbound
    connection it was not asked to make. It is a string mc compares, which is why `off`
    is the right word there and the wrong one below.

    `MC_DISABLE_PAGER` backs a *flag*, `--disable-pager`, and every environment
    variable that does is parsed by Go's `strconv.ParseBool`. `on` is not one of the
    words that accepts, and mc does not shrug it off: it refuses to run at all, with
    `could not parse on as bool value for flag disable-pager`. So `true`, for this one
    and for any other flag-backed variable added beside it.

    `HOME` is not decoration and `MC_CONFIG_DIR` does not cover for it. `mc` computes
    the *default* of its `--config-dir` flag from the home directory while it builds
    its flag set, before any environment variable is consulted, so a missing `HOME`
    kills it whatever `MC_CONFIG_DIR` says. With no `HOME` it shells out to
    `getent passwd`, which is not on the unit's PATH (usb-ingest.nix, `runtimeInputs`)
    -- and its `sh -c 'cd && pwd'` fallback is unreachable, because go-homedir compares
    the lookup failure against `exec.ErrNotFound` by identity and gets a wrapper. That
    is the whole of `mc: <ERROR> Unable to get mcConfigDir, exec "getent": executable
    file not found in $PATH`.

    Systemd is where the value goes missing: `$HOME` is set only for units that set
    `User=` (systemd.exec(5)), and the ingest units run as root without one. It is
    therefore set here rather than on the units, so that every `mc` call carries it --
    including the `--release` run from `ExecStopPost` -- and so that running the same
    binary by hand, where a login shell has already set `HOME`, exercises the same
    thing the service does.
    """
    env = dict(os.environ if environ is None else environ)
    env.update(
        {
            "MC_CONFIG_DIR": config_dir,
            "MC_UPDATE": "off",
            "MC_DISABLE_PAGER": "true",
        }
    )
    # Only when there is none: an operator debugging by hand has a real home
    # directory, and nothing is gained by hiding it from mc. An empty `HOME` counts as
    # none, because that is how mc reads it.
    if not env.get("HOME"):
        env["HOME"] = config_dir
    return env


def install_cluster_ca(config_dir: str, namespace: str, kubeconfig: str) -> bool:
    """Trust the cluster's self-signed certificate, rather than skipping checks.

    Same approach and same two secrets as console.nix's loom-chat: which one Traefik
    presents depends on how the chart was deployed, and a bundle costs nothing. Read
    through the API rather than off the wire -- pulling the chain from the server and
    then trusting it would verify nothing at all.
    """
    certs_dir = os.path.join(config_dir, "certs", "CAs")
    os.makedirs(certs_dir, mode=0o700, exist_ok=True)

    env = dict(os.environ, KUBECONFIG=kubeconfig)
    written = False

    for secret in ("self-signed-cert", "loom-certificate"):
        try:
            encoded = _run(
                [
                    "kubectl",
                    "--namespace",
                    namespace,
                    "get",
                    "secret",
                    secret,
                    "--output",
                    "jsonpath={.data.tls\\.crt}",
                ],
                env,
                timeout=60,
            ).strip()
        except (subprocess.SubprocessError, OSError):
            continue

        if not encoded:
            continue

        try:
            pem = base64.b64decode(encoded)
        except (ValueError, TypeError):
            continue

        with open(os.path.join(certs_dir, f"{secret}.crt"), "wb") as handle:
            handle.write(pem)
        written = True

    return written


def wait_for_cluster(endpoint: str, config_dir: str, deadline_s: int) -> bool:
    """Block until the S3 endpoint answers.

    A stick can be plugged in at any point, including while `loom.service` is still
    bringing the stack up -- which takes a long time on this hardware. So waiting is the
    normal case, not an error path.
    """
    env = mc_env(config_dir)
    started = time.monotonic()

    while time.monotonic() - started < deadline_s:
        try:
            _run(["mc", "--json", "ready", ALIAS], env, timeout=60)
            return True
        except (subprocess.SubprocessError, OSError):
            logger.info("Waiting for %s to answer", endpoint)
            time.sleep(CLUSTER_POLL_INTERVAL_S)

    return False


def configure_alias(endpoint: str, config_dir: str) -> None:
    """Point `mc` at the appliance's own S3 endpoint.

    Anonymous: charts/values.yaml leaves intakeStorage's access and secret keys
    null, so SeaweedFS's S3 gateway takes unauthenticated requests. Empty
    credentials are what `mc` expects for that.
    """
    try:
        _run(
            ["mc", "alias", "set", ALIAS, endpoint, "", ""],
            mc_env(config_dir),
            timeout=60,
        )
    except subprocess.CalledProcessError as error:
        raise TransferError(
            f"could not configure mc for {endpoint}: {(error.stderr or '').strip()}"
        ) from error
    except (subprocess.SubprocessError, OSError) as error:
        # An mc that hung until the timeout, or one that could not be executed at
        # all. Neither is a CalledProcessError, and letting either out of here would
        # end the unit in a traceback -- with nothing on the console, which is the one
        # place the operator is standing.
        raise TransferError(
            f"could not configure mc for {endpoint}: {error}"
        ) from error


def mirror(
    source: str,
    bucket: str,
    prefix: str,
    config_dir: str,
    on_event: Callable[[int, int], None] | None = None,
) -> TransferResult:
    """Mirror a mounted volume into the intake bucket under `prefix`.

    `mc mirror` skips objects that are already there with the same size, which is
    what makes re-plugging the same stick cheap and idempotent without this
    service keeping a state database of its own.

    `on_event` is called with the running object and byte counts as each object
    lands. It is what drives the console pane (`watch.py`), and it is a callback
    rather than a return value because a full stick is minutes to hours: by the time
    this function returns there is nothing left to report.
    """
    argv = [
        "mc",
        "--json",
        "mirror",
        "--quiet",
        source.rstrip("/") + "/",
        f"{ALIAS}/{bucket}/{prefix.rstrip('/')}/",
    ]

    objects = 0
    transferred = 0
    failures = 0
    first_error = ""

    for event in _stream_json(argv, mc_env(config_dir)):
        if event.get("status") == "error":
            failures += 1
            message = str(event.get("error", {}).get("message") or "").strip()
            logger.warning("mirror error: %s", message)
            first_error = first_error or message
            continue
        if event.get("status") == "success":
            objects += 1
            transferred += int(event.get("size") or 0)
            if on_event:
                on_event(objects, transferred)

    return TransferResult(objects, transferred, failures, first_error)


def _stream_json(argv: list[str], env: dict[str, str]) -> Iterator[dict]:
    """Run a command and yield its newline-delimited JSON events as they arrive.

    A command that fails without having said so in JSON -- mc refusing to start at all
    is the case that matters, since it writes plain text to stderr and produces no
    events -- yields one synthetic error event carrying its stderr. Otherwise such a
    run is indistinguishable from an empty volume, and the operator is told that a
    stick full of documents was copied successfully.
    """
    with subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
    ) as process:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logger.debug("Ignoring non-JSON output from mc: %s", line)

        stderr = process.stderr.read() if process.stderr else ""
        process.wait()

        if process.returncode:
            yield {
                "status": "error",
                "error": {
                    "message": (
                        stderr.strip()
                        or f"{os.path.basename(argv[0])} exited with status "
                        f"{process.returncode}"
                    )
                },
            }


def put_manifest(manifest: dict, bucket: str, key: str, config_dir: str) -> str:
    """Write the provenance record next to the data it describes.

    Returns why it could not be written, or an empty string. The caller reports it: a
    manifest that did not land means the operator cannot later tell which stick the
    documents in front of them came from, which is worth a line on the console rather
    than a warning in a journal nobody opens.
    """
    env = mc_env(config_dir)
    payload = json.dumps(manifest, indent=2, sort_keys=True).encode()

    with subprocess.Popen(
        ["mc", "pipe", f"{ALIAS}/{bucket}/{key}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ) as process:
        _, raw = process.communicate(payload, timeout=120)
        if process.returncode == 0:
            return ""

        stderr = (raw or b"").decode(errors="replace").strip()
        logger.warning("Could not write manifest %s: %s", key, stderr)
        return stderr or f"mc exited with status {process.returncode}"
