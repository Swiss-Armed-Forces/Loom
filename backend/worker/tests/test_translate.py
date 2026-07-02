from math import floor
from typing import cast
from unittest.mock import MagicMock

import pytest
from common.dependencies import get_llm_translation_client
from openai import APIConnectionError

from worker.index_file.tasks.translate import (
    MAX_CHARACTERS_PER_CHUNK,
    DetectedLanguage,
    LLMTranslationException,
    _LanguageDetectionResult,
    _TranslationResult,
    get_translation_text_splitter,
    translate,
    translate_detect_language,
)
from worker.settings import settings


def _make_parse_response(
    parsed: _LanguageDetectionResult | _TranslationResult,
) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.parsed = parsed
    return response


def _llm_client() -> MagicMock:
    return cast(MagicMock, get_llm_translation_client())


@pytest.mark.parametrize(
    "text, expected_language, expected_confidence",
    [
        (
            "Dieser Text ist in deutscher Sprache verfasst.",  # spellchecker:disable-line
            "de",
            100,
        )
    ],
)
def test_translate_detect_language(text, expected_language, expected_confidence):
    detection_result = _LanguageDetectionResult(
        languages=[
            DetectedLanguage(language=expected_language, confidence=expected_confidence)
        ]
    )
    _llm_client().beta.chat.completions.parse.return_value = _make_parse_response(
        detection_result
    )

    result = translate_detect_language(text)
    assert result[0].language == expected_language
    assert result[0].confidence == expected_confidence


@pytest.mark.parametrize(
    "text, expected_language, expected_confidence",
    [("maybe german", "de", 0)],
)
def test_translate_detect_language_filters_low_confidence(
    text, expected_language, expected_confidence
):
    detection_result = _LanguageDetectionResult(
        languages=[
            DetectedLanguage(language=expected_language, confidence=expected_confidence)
        ]
    )
    _llm_client().beta.chat.completions.parse.return_value = _make_parse_response(
        detection_result
    )

    result = translate_detect_language(text)
    assert len(result) == 0


def test_translate_detect_language_empty_text():
    client = _llm_client()
    text = ""
    result = translate_detect_language(text)
    assert not client.beta.chat.completions.parse.called
    assert len(result) == 0


def test_translate_detect_llm_error():
    _llm_client().beta.chat.completions.parse.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(LLMTranslationException):
        translate_detect_language("a short text")


@pytest.mark.parametrize(
    "text, expected_text, expected_language, expected_translate_calls",
    [
        ("", "", "fr", 0),
        (
            "Don't translate for the default translation target",
            "Don't translate for the default translation target",
            settings.translate_target,
            0,
        ),
        (
            "Dieser Text ist in deutscher Sprache verfasst.",  # spellchecker:disable-line
            "This is the english translation result.",
            "de",
            1,
        ),
    ],
)
def test_translate(
    text: str, expected_text: str, expected_language: str, expected_translate_calls: int
):
    client = _llm_client()
    client.beta.chat.completions.parse.return_value = _make_parse_response(
        _TranslationResult(text=expected_text)
    )

    translation = translate(
        text, DetectedLanguage(confidence=1, language=expected_language)
    )

    assert translation == expected_text
    assert client.beta.chat.completions.parse.call_count == expected_translate_calls


def test_translate_llm_error():
    _llm_client().beta.chat.completions.parse.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(LLMTranslationException):
        translate("a short text", DetectedLanguage(confidence=1, language="es"))


@pytest.mark.parametrize(
    "expected_text_chunks",
    [0, 1, 10, 20, 100],
)
def test_translate_text_splitter_long_word(expected_text_chunks: int):
    text = "x" * MAX_CHARACTERS_PER_CHUNK * expected_text_chunks

    text_splitter = get_translation_text_splitter()
    text_chunks = text_splitter.split_text(text)
    assert (
        len(text_chunks) == expected_text_chunks
        if expected_text_chunks == 0
        else len(text_chunks) == 1  # 1: can not split
    )
    assert text == "".join(text_chunks)


@pytest.mark.parametrize(
    "expected_text_chunks",
    [0, 1, 10, 20, 100],
)
def test_translate_text_splitter_long_text(expected_text_chunks: int):
    word = "x "
    text = word * floor(MAX_CHARACTERS_PER_CHUNK / len(word)) * expected_text_chunks

    text_splitter = get_translation_text_splitter()
    text_chunks = text_splitter.split_text(text)
    assert len(text_chunks) == expected_text_chunks
    assert text == "".join(text_chunks)
