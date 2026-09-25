from unittest.mock import patch

import pytest
from common import dependencies
from common.services.lazybytes_service import (
    InMemoryFileStorageLazyBytesService,
    InMemoryTempLazyBytesService,
)

from worker.dependencies import mock_init

LAZYBYTES_THRESHOLD_BYTES = 64


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
def lazybytes_service_inmemory() -> InMemoryTempLazyBytesService:
    lazybytes_service = InMemoryTempLazyBytesService(
        threshold_bytes=LAZYBYTES_THRESHOLD_BYTES
    )
    dependencies._lazybytes_service = (  # pylint: disable=protected-access
        lazybytes_service
    )
    return lazybytes_service


# The dependency globals a test may need to stand in for, by name. Spelled as
# strings so that installing one is `setattr` rather than an assignment to somebody
# else's private, and so both sites cannot drift apart.
FILE_STORAGE_SERVICE = "_file_storage_service"
ARCHIVE_ENCRYPTION_SERVICE = "_archive_encryption_service"


@pytest.fixture(name="install_services")
def install_services_fixture():
    """Put service doubles in place for one test, and take them out again afterwards.

    The dependency globals are the seam the worker has -- a Celery task resolves its
    services through `common.dependencies` when it runs, and takes no arguments -- so a
    test that needs a real encryptor or an instrumented storage installs it through
    here, and what was there before comes back whichever way the test ends.

    Code under test that can take its services as arguments should be handed them
    directly instead. See `index_archive.ArchiveServices`.
    """
    names = (FILE_STORAGE_SERVICE, ARCHIVE_ENCRYPTION_SERVICE)
    saved = {name: getattr(dependencies, name) for name in names}

    def install(*, file_storage=None, archive_encryption=None):
        if file_storage is not None:
            setattr(dependencies, FILE_STORAGE_SERVICE, file_storage)
        if archive_encryption is not None:
            setattr(dependencies, ARCHIVE_ENCRYPTION_SERVICE, archive_encryption)

    yield install

    for name, value in saved.items():
        setattr(dependencies, name, value)


@pytest.fixture()
def file_storage_service_inmemory() -> InMemoryFileStorageLazyBytesService:
    file_storage_service = InMemoryFileStorageLazyBytesService(
        threshold_bytes=LAZYBYTES_THRESHOLD_BYTES
    )
    dependencies._file_storage_service = (  # pylint: disable=protected-access
        file_storage_service
    )
    return file_storage_service
