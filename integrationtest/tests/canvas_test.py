import logging

import pytest
from celery.exceptions import ChordError
from common.dependencies import get_celery_app
from worker.test.canvas_test_task import (
    GET_TIMEOUT,
    CanvasTestException,
    _autodefine_tests,
)

logger = logging.getLogger(__name__)


def _test_exception(ex: BaseException):
    match ex:
        case CanvasTestException():
            return True
        case ChordError():
            return "raised CanvasTestException()" in str(ex)
        case _:
            return False


@pytest.mark.parametrize("test_function", _autodefine_tests())
def test_raise_exception(test_function: str):
    ex = CanvasTestException()
    with pytest.raises(check=_test_exception):
        get_celery_app().send_task(test_function, args=[ex]).get(timeout=GET_TIMEOUT)
