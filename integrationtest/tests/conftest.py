import pytest
from common.dependencies import init, mock_init
from common.services.encryption_service import AESMasterKey
from common.settings import settings

from utils.wipe_data import wipe_data as _wipe_data


def pytest_configure():
    mock_init()


@pytest.fixture(scope="session", autouse=True)
def global_test_init():
    # Fix AES key
    settings.archive_encryption_master_key = AESMasterKey.from_fixed_key()
    init()


@pytest.fixture(scope="class", autouse=True)
def wipe_data():
    """The cleanup will delete all data, which takes up to a few seconds.

    Initially this was run for every test, but some tests can safely share a common
    dataset. Using the class scope allows a test author to only run cleanup once for a
    group of tests by putting them into the same class and importing a testset in a
    local fixture.
    """
    _wipe_data()
