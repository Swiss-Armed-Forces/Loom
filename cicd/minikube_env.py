"""Point a docker client at minikube's daemon.

Three scripts here talk to the cluster's docker daemon rather than the host's,
and each used to carry its own copy of this parsing. The copies drifted - one
logged every variable, one stripped quotes differently - and pylint's
duplicate-code check is what finally surfaced them.
"""

import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Mapping

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerEnvironment:
    """The variables that address minikube's docker daemon."""

    variables: Mapping[str, str]


def get_minikube_docker_environment() -> DockerEnvironment:
    """Ask minikube which variables address its daemon.

    `--shell none` prints plain `NAME=value` lines, rather than the `export ` statements
    meant for eval.
    """
    completed = subprocess.run(  # nosec B603 B607 - a fixed argv, never a shell string
        ["minikube", "-p", "minikube", "docker-env", "--shell", "none"],
        capture_output=True,
        text=True,
        check=True,
    )

    variables: dict[str, str] = {}
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        unquoted = shlex.split(value)
        variables[name] = unquoted[0] if unquoted else ""
    return DockerEnvironment(variables=variables)


def load_minikube_docker_environment() -> None:
    """Apply those variables to this process, for clients that read os.environ."""
    environment = get_minikube_docker_environment()
    for name, value in environment.variables.items():
        os.environ[name] = value
        logger.debug("Set env %s=%s", name, value)
    logger.info("Successfully loaded Minikube Docker environment.")
