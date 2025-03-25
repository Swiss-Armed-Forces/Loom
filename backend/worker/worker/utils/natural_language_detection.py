import math
from collections import Counter

MIN_WORDS_NATURAL_LANGUAGE = 10

MIN_TEXT_ENTROPY = 0.7
MAX_TEXT_ENTROPY = 1.1


def _has_min_words(text: str) -> bool:
    return len(text.split()) > MIN_WORDS_NATURAL_LANGUAGE


def _average_word_length(text: str) -> float:
    """Helper for calculating entropy, returns average length of group of characters
    separated by whitespace."""
    words = text.split()
    if len(words) == 0:
        return 0
    avg_length = sum(len(word) for word in words) / len(words)
    return avg_length


def _get_entropy(text: str) -> float:
    """Calculates shannon entropy of text per character."""
    if len(text) == 0:
        return 0
    freq = Counter(text)
    prob = {char: count / len(text) for char, count in freq.items()}
    entropy = -sum(p * math.log2(p) for p in prob.values())

    text_average_word_length = _average_word_length(text)

    if text_average_word_length == 0:
        return 0
    entropy /= text_average_word_length

    return entropy


def _has_text_entropy(text: str) -> bool:
    text_entropy = _get_entropy(text)
    return MIN_TEXT_ENTROPY < text_entropy < MAX_TEXT_ENTROPY


def is_natural_language(text: str) -> bool:
    return _has_min_words(text) and _has_text_entropy(text)
