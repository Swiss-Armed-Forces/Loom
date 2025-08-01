import pytest

from common import dependencies
from common.dependencies import mock_init
from common.services.lazybytes_service import InMemoryLazyBytesService, LazyBytesService


def pytest_configure():
    mock_init()


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
