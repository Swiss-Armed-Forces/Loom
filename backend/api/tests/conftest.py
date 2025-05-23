from typing import Generator

import pytest
from fastapi.testclient import TestClient

from api.api import init_api
from api.dependencies import mock_init


def pytest_configure():
    mock_init()


@pytest.fixture(autouse=True)
def dependencies_init():
    mock_init()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    api = init_api()
    with TestClient(api) as test_client:
        yield test_client
        api.dependency_overrides = {}
