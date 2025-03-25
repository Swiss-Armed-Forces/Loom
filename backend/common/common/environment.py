import logging
from os import getenv
from pathlib import Path

# This module initializes logging.
# Hence, we CAN NOT import any other modules here
# other than standard library.


def is_running_in_kubernetes() -> bool:
    cgroup = Path("/proc/self/cgroup")
    return (
        Path("/var/run/secrets/kubernetes.io/serviceaccount").exists()
        or cgroup.is_file()
        and ("kubepods" in cgroup.read_text(encoding="utf-8"))
        or getenv("KUBERNETES_SERVICE_HOST") is not None
    )


def get_environment() -> str:
    return str(getenv("ENVIRONMENT", "production"))


def is_development_env() -> bool:
    return get_environment() == "development"


def is_test_env() -> bool:
    return get_environment() == "test"


def get_loglevel() -> int:
    return (
        logging.INFO
        if not is_development_env() and not is_test_env()
        else logging.DEBUG
    )


def init_logging():
    logging.basicConfig(
        level=get_loglevel(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Logging initialized")


# Initialize logging now
init_logging()
