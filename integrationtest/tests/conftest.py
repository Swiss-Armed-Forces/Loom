import pytest
from api.dependencies import init as init_api_dependencies
from common.dependencies import get_celery_inspect_service, mock_init
from common.services.encryption_service import AESMasterKey
from common.settings import settings
from crawler.dependencies import init as init_crawler_dependencies
from worker.dependencies import init as init_worker_dependencies

from utils.wipe_data import wipe_data as _wipe_data


def pytest_configure():
    mock_init()


@pytest.fixture(scope="session", autouse=True)
def global_test_init():
    # Fix AES key
    settings.archive_enc_master_key = AESMasterKey.from_fixed_key()
    init_worker_dependencies()
    init_api_dependencies()
    init_crawler_dependencies()


@pytest.fixture(scope="class", autouse=True)
def wipe_data():
    """The cleanup will delete all data, which takes up to a few seconds.

    Initially this was run for every test, but some tests can safely share a common
    dataset. Using the class scope allows a test author to only run cleanup once for a
    group of tests by putting them into the same class and importing a testset in a
    local fixture.
    """
    _wipe_data()
    # wipe_redis() flushes all Redis data including the task group registry;
    # re-register so task group lookups work correctly after a wipe.
    get_celery_inspect_service().register_task_groups()


@pytest.fixture(scope="class")
def disable_periodic_tasks(
    wipe_data,
):  # pylint: disable=redefined-outer-name,unused-argument
    service = get_celery_inspect_service()
    service.set_beat_paused(True)
    yield
    service.set_beat_paused(False)
