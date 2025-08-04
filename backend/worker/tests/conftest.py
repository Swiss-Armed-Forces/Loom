from unittest.mock import patch

import pytest
from common import dependencies
from common.services.lazybytes_service import InMemoryLazyBytesService, LazyBytesService

from worker.dependencies import mock_init


def noop_cache_decorator(*_, **__):
    """Mock cache decorator that is a no-op."""

    def decorator(func):
        return func

    return decorator


def pytest_configure(config):
    """Runs early — before any test modules are imported."""
    # Patch the cache decorator early so it is a no-op
    patcher = patch("common.utils.cache.cache", new=noop_cache_decorator)
    patcher.start()

    # Store it on the config object to avoid using a global
    config.cache_patch = patcher

    # Run your other setup code
    mock_init()


def pytest_unconfigure(config):
    """Stop the patch to clean up."""
    patcher = getattr(config, "cache_patch", None)
    if patcher:
        patcher.stop()


@pytest.fixture(autouse=True)
def dependencies_init():
    mock_init()


@pytest.fixture()
def lazybytes_service_inmemory() -> LazyBytesService:
    lazybytes_service = InMemoryLazyBytesService()
    dependencies._lazybytes_service = (  # pylint: disable=protected-access
        lazybytes_service
    )
    return lazybytes_service
