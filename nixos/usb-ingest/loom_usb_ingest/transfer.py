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
from collections.abc import Callable, Iterator
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


class TransferError(RuntimeError):
    pass


def _run(argv: list[str], env: dict[str, str], timeout: int = 300) -> str:
    return subprocess.run(
        argv, check=True, capture_output=True, text=True, timeout=timeout, env=env
    ).stdout


def mc_env(config_dir: str) -> dict[str, str]:
    """Environment for every `mc` call.

    `MC_UPDATE=off` is policy rather than tuning, the same policy
    `OPENCODE_DISABLE_MODELS_FETCH` states in console.nix: this box makes no outbound
    connection it was not asked to make.
    """
    env = dict(os.environ)
    env.update(
        {
            "MC_CONFIG_DIR": config_dir,
            "MC_UPDATE": "off",
            "MC_DISABLE_PAGER": "on",
        }
    )
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

    for event in _stream_json(argv, mc_env(config_dir)):
        if event.get("status") == "error":
            failures += 1
            logger.warning("mirror error: %s", event.get("error", {}).get("message"))
            continue
        if event.get("status") == "success":
            objects += 1
            transferred += int(event.get("size") or 0)
            if on_event:
                on_event(objects, transferred)

    return TransferResult(objects, transferred, failures)


def _stream_json(argv: list[str], env: dict[str, str]) -> Iterator[dict]:
    """Run a command and yield its newline-delimited JSON events as they arrive."""
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

        process.wait()


def put_manifest(manifest: dict, bucket: str, key: str, config_dir: str) -> None:
    """Write the provenance record next to the data it describes."""
    env = mc_env(config_dir)
    payload = json.dumps(manifest, indent=2, sort_keys=True).encode()

    with subprocess.Popen(
        ["mc", "pipe", f"{ALIAS}/{bucket}/{key}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ) as process:
        process.communicate(payload, timeout=120)
        if process.returncode != 0:
            logger.warning("Could not write manifest %s", key)
