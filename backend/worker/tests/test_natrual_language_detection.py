from random import randrange

import pytest

from worker.utils.natural_language_detection import (
    MIN_TEXT_ENTROPY,
    _average_word_length,
    _get_entropy,
)

ENGLISH_SENTENCE = "This is an example document that needs to be summarized. "


@pytest.mark.parametrize(
    "text",
    [ENGLISH_SENTENCE],
)
def test_average_word_length(text: str):
    avg = _average_word_length(text)
    assert avg == 4.7


@pytest.mark.parametrize(
    "text",
    [ENGLISH_SENTENCE],
)
def test_entropy_english_sentence(text: str):
    assert _get_entropy(text)


def test_entropy_random_string():
    text = "".join(chr(randrange(65, 90)) for _ in range(55))
    assert _get_entropy(text) < MIN_TEXT_ENTROPY


def test_entropy_empty_string():
    assert _get_entropy("") == 0
