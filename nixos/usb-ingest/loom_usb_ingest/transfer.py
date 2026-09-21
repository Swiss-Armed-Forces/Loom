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


@dataclass(frozen=True)
class ClusterWait:
    """Whether the intake bucket answered, and what it said while it did not."""

    ready: bool
    last_error: str = ""


@dataclass(frozen=True)
class WaitHooks:
    """What the wait does between attempts, beside sleeping.

    `trust` is retried until it succeeds -- it installs the cluster's CA, which is read
    through the Kubernetes API, also not answering on a box that is still coming up.
    `on_attempt` is given the reason each failed attempt gave, for the console pane.
    `poll_s` is how long to sleep between attempts, and is a knob so the tests are not.
    """

    trust: Callable[[], bool] | None = None
    on_attempt: Callable[[str], None] | None = None
    poll_s: float = CLUSTER_POLL_INTERVAL_S


# The default for `wait_for_cluster`, as a value rather than a call in the signature:
# a call there would be evaluated once at definition time, which flake8 rightly refuses.
# Shared safely because `WaitHooks` is frozen.
NO_HOOKS = WaitHooks()


class TransferError(RuntimeError):
    pass


def _run(argv: list[str], env: Mapping[str, str], timeout: int = 300) -> str:
    return subprocess.run(
        argv, check=True, capture_output=True, text=True, timeout=timeout, env=dict(env)
    ).stdout


def _reason(error: Exception) -> str:
    """What to tell the operator about a tool that would not run."""
    if isinstance(error, subprocess.CalledProcessError):
        return (error.stderr or "").strip() or f"mc exited {error.returncode}"
    return str(error)


def mc_env(
    config_dir: str, endpoint: str, environ: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Environment for every `mc` call.

    `environ` is the environment to build on, and defaults to this process's. It is a
    parameter so that the tests can hand in the environment a systemd unit has without
    editing the one they are running in.

    The endpoint is declared here, as `MC_HOST_<alias>`, rather than registered with
    `mc alias set`. That is not a simplification: `alias set` *probes* the endpoint and
    refuses to record one that does not answer, so on a box still bringing Loom up --
    which is the ordinary case for a stick plugged in at the console, and what
    `wait_for_cluster` below exists for -- configuring mc failed outright and the wait
    was never reached. An environment alias is recorded by being read, so the only
    thing that waits for the cluster is the thing whose job that is.

    No credentials: charts/values.yaml leaves intakeStorage's keys null, so SeaweedFS's
    S3 gateway takes unauthenticated requests, and a bare URL is how mc spells that.

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
            f"MC_HOST_{ALIAS}": endpoint,
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


def wait_for_cluster(
    bucket: str,
    env: Mapping[str, str],
    deadline_s: int,
    hooks: WaitHooks = NO_HOOKS,
) -> ClusterWait:
    """Block until the intake bucket can be listed.

    A stick can be plugged in at any point, including while `loom.service` is still
    bringing the stack up -- which takes a long time on this hardware. So waiting is the
    normal case, not an error path.

    Listing the bucket, and NOT `mc ready`: that command asks for
    `/minio/health/cluster`, which is MinIO's own admin endpoint. Loom's S3 gateway is
    SeaweedFS, which answers it 404, so `mc ready` reports "the cluster is not ready"
    against a perfectly healthy Loom -- forever. Listing the bucket asks the question
    that actually matters anyway: the mirror needs this bucket, reachable and
    unauthenticated, and nothing else.

    See `WaitHooks` for what happens between attempts: the CA install that has to be
    retried for the same reason this wait exists, and the reason the pane is told.
    """
    started = time.monotonic()
    trusted = hooks.trust is None
    last_error = ""

    while True:
        if not trusted and hooks.trust is not None:
            trusted = hooks.trust()

        try:
            _run(["mc", "ls", f"{ALIAS}/{bucket}"], env, timeout=60)
            return ClusterWait(True)
        except (subprocess.SubprocessError, OSError) as error:
            last_error = _reason(error)

        logger.info("Waiting for the intake bucket: %s", last_error)
        if hooks.on_attempt:
            hooks.on_attempt(last_error)

        remaining = deadline_s - (time.monotonic() - started)
        if remaining <= 0:
            return ClusterWait(False, last_error)
        time.sleep(min(hooks.poll_s, remaining))


def mirror(
    source: str,
    bucket: str,
    prefix: str,
    env: Mapping[str, str],
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

    for event in _stream_json(argv, env):
        if event.get("status") == "error":
            failures += 1
            message = str(event.get("error", {}).get("message") or "").strip()
            logger.warning("mirror error: %s", message)
            first_error = first_error or message
            continue
        if event.get("status") == "success":
            # `mc mirror --json` closes with a summary event -- totals, duration,
            # speed -- which is a success like any other to `status` alone. Counted as
            # an object it made every copy report one more file than it moved, and an
            # empty volume report one. Only a per-object event names a target.
            if "target" not in event:
                continue
            objects += 1
            transferred += int(event.get("size") or 0)
            if on_event:
                on_event(objects, transferred)

    return TransferResult(objects, transferred, failures, first_error)


def _stream_json(argv: list[str], env: Mapping[str, str]) -> Iterator[dict]:
    """Run a command and yield its newline-delimited JSON events as they arrive.

    A command that fails without having said so in JSON -- mc refusing to start at all
    is the case that matters, since it writes plain text to stderr and produces no
    events -- yields one synthetic error event carrying its stderr. Otherwise such a
    run is indistinguishable from an empty volume, and the operator is told that a
    stick full of documents was copied successfully.
    """
    with subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(env)
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


def put_manifest(manifest: dict, bucket: str, key: str, env: Mapping[str, str]) -> str:
    """Write the provenance record next to the data it describes.

    Returns why it could not be written, or an empty string. The caller reports it: a
    manifest that did not land means the operator cannot later tell which stick the
    documents in front of them came from, which is worth a line on the console rather
    than a warning in a journal nobody opens.
    """
    payload = json.dumps(manifest, indent=2, sort_keys=True).encode()

    with subprocess.Popen(
        ["mc", "pipe", f"{ALIAS}/{bucket}/{key}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(env),
    ) as process:
        _, raw = process.communicate(payload, timeout=120)
        if process.returncode == 0:
            return ""

        stderr = (raw or b"").decode(errors="replace").strip()
        logger.warning("Could not write manifest %s: %s", key, stderr)
        return stderr or f"mc exited with status {process.returncode}"
