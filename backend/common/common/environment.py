import logging
from os import getenv

# This module initializes logging.
# Hence, we CAN NOT import any other modules here
# other than standard library.


def get_environment() -> str:
    return str(getenv("ENVIRONMENT", "production"))


def is_development_env() -> bool:
    return get_environment() == "development"


def get_loglevel() -> int:
    return logging.INFO if not is_development_env() else logging.DEBUG


def init_logging():
    logging.basicConfig(
        level=get_loglevel(),
        format="[%(asctime)s: %(levelname)s/%(processName)s - %(name)s] %(message)s",
    )
    logging.info("Logging initialized")


# Initialize logging now
init_logging()
