import pytest

from common import dependencies
from common.dependencies import mock_init
from common.services.lazybytes_service import InMemoryTempLazyBytesService

LAZYBYTES_THRESHOLD_BYTES = 64


def pytest_configure():
    mock_init()


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
