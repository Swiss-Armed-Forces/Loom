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


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="raise"))
def test_raise_exception(test_function: str):
    ex = CanvasTestException()
    with pytest.raises(check=_test_exception):
        get_celery_app().send_task(test_function, args=[ex]).get(timeout=GET_TIMEOUT)


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="assert_group1"))
def test_assert_group1(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)
    expected = [2, [6, 7], 8]
    assert result == expected


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="assert_group2"))
def test_assert_group2(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)
    expected = ([1, [5, 6, 7], 8], 9)
    assert result == expected


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="assert_group3"))
def test_assert_group3(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)
    expected = [1, [5, 6, 7], 8]
    assert result == expected


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="assert_group4"))
def test_assert_group4(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)
    expected = ([1, [3, 4]], 5)
    assert result == expected


# === Chord ordering tests =====================================


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="chord_ordering1"))
def test_chord_ordering1(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)

    assert sorted(result) == result


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="chord_ordering2"))
def test_chord_ordering2(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)

    assert sorted(result) == result


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="chord_ordering3"))
def test_chord_ordering3(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)

    assert sorted(result) == result


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="chord_ordering4"))
def test_chord_ordering4(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)

    assert sorted(result) == result


@pytest.mark.parametrize("test_function", _autodefine_tests(prefix="chord_ordering5"))
def test_chord_ordering5(test_function: str):
    result = get_celery_app().send_task(test_function).get(timeout=GET_TIMEOUT)

    assert sorted(result[0][0]) == result[0][0]
