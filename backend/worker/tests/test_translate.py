from email.message import Message
from math import floor
from urllib.error import HTTPError

import pytest
from common.dependencies import get_libretranslate_api

from worker.index_file.tasks.translate import (
    LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST,
    LibretranslateDetectedLanguage,
    LibretranslateInternalException,
    get_translation_text_splitter,
    translate,
    translate_detect_language,
)
from worker.settings import settings


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

    libretranslate_api = get_libretranslate_api()
    libretranslate_api.detect.return_value = [
        {
            "language": expected_language,
            "confidence": expected_confidence,
        }
    ]

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
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.detect.return_value = [
        {
            "language": expected_language,
            "confidence": expected_confidence,
        }
    ]

    result = translate_detect_language(text)
    assert len(result) == 0


def test_translate_detect_language_empty_text():
    libretranslate_api = get_libretranslate_api()
    text = ""
    result = translate_detect_language(text)
    assert not libretranslate_api.detect.called
    assert len(result) == 0


def test_translate_detect_http_internal_server_error():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.detect.side_effect = HTTPError(
        url="http://...", code=500, msg="Internal error", fp=None, hdrs=Message()
    )

    with pytest.raises(LibretranslateInternalException):
        translate_detect_language("a short text")


def test_translate_detect_remote_disconnected():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.detect.side_effect = OSError("status line")

    with pytest.raises(LibretranslateInternalException):
        translate_detect_language("a short text")


def test_translate_detect_http_client_error():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.detect.side_effect = HTTPError(
        url="http://...", code=400, msg="Internal error", fp=None, hdrs=Message()
    )

    with pytest.raises(HTTPError):
        translate_detect_language("a short text")


@pytest.mark.parametrize(
    "text, expected_text, expected_language,expected_translate_calls",
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
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.return_value = expected_text

    translation = translate(
        text, LibretranslateDetectedLanguage(confidence=1, language=expected_language)
    )

    assert translation == expected_text
    assert libretranslate_api.translate.call_count == expected_translate_calls


def test_translate_http_internal_server_error():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.side_effect = HTTPError(
        url="http://...", code=500, msg="Internal error", fp=None, hdrs=Message()
    )

    with pytest.raises(LibretranslateInternalException):
        translate(
            "a short text", LibretranslateDetectedLanguage(confidence=1, language="es")
        )


def test_translate_remote_disconnected():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.side_effect = OSError("status line")

    with pytest.raises(LibretranslateInternalException):
        translate(
            "a short text", LibretranslateDetectedLanguage(confidence=1, language="es")
        )


def test_translate_http_client_error():
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.side_effect = HTTPError(
        url="http://...", code=400, msg="Internal error", fp=None, hdrs=Message()
    )

    with pytest.raises(HTTPError):
        translate(
            "a short text", LibretranslateDetectedLanguage(confidence=1, language="es")
        )


@pytest.mark.parametrize(
    "expected_text_chunks",
    [0, 1, 10, 20, 100],
)
def test_translate_text_splitter_long_word(expected_text_chunks: int):
    text = "x" * LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST * expected_text_chunks

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
    text = (
        word
        * floor(LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST / len(word))
        * expected_text_chunks
    )

    text_splitter = get_translation_text_splitter()
    text_chunks = text_splitter.split_text(text)
    assert len(text_chunks) == expected_text_chunks
    assert text == "".join(text_chunks)
