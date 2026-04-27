from unittest.mock import MagicMock

import pytest

from common.utils.retry import retry


def test_retry_succeeds_first_attempt():
    fn = MagicMock(return_value=42)
    assert retry(fn, max_attempts=3, wait_s=0) == 42
    fn.assert_called_once()


def test_retry_succeeds_after_failures():
    fn = MagicMock(side_effect=[RuntimeError("err"), RuntimeError("err"), "ok"])
    assert retry(fn, max_attempts=3, wait_s=0) == "ok"
    assert fn.call_count == 3


def test_retry_raises_after_all_attempts_exhausted():
    fn = MagicMock(side_effect=ValueError("boom"))
    with pytest.raises(ValueError, match="boom"):
        retry(fn, max_attempts=3, wait_s=0)
    assert fn.call_count == 3


def test_retry_single_attempt_raises_immediately():
    fn = MagicMock(side_effect=OSError("gone"))
    with pytest.raises(OSError):
        retry(fn, max_attempts=1, wait_s=0)
    fn.assert_called_once()


def test_retry_preserves_return_type():
    fn = MagicMock(return_value={"key": "value"})
    assert retry(fn, max_attempts=1, wait_s=0) == {"key": "value"}
