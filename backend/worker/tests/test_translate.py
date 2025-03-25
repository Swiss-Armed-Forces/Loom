"""Test translate."""

import pytest

from worker.index_file.tasks.translate import (
    LIBRETRANSLATE_MAX_BACKTRACK_RANGE,
    LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST,
    LibretranslateDetectedLanguage,
    LibreTranslateLanguageDetectResult,
    translate,
    translate_detect_language,
)


@pytest.mark.parametrize(
    "text, expected_language, expected_confidence",
    [("Dieser Text ist in deutscher Sprache verfasst.", "de", 100)],
)
def test_translate_detect_language(text, expected_language, expected_confidence):
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    libre_translate_api.detect.return_value = [
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
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    libre_translate_api.detect.return_value = [
        {
            "language": expected_language,
            "confidence": expected_confidence,
        }
    ]

    result = translate_detect_language(text)
    assert len(result) == 0


def test_translate_detect_language_empty_text():
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    text = ""
    result = translate_detect_language(text)
    assert not libre_translate_api.detect.called
    assert len(result) == 0


@pytest.mark.parametrize(
    "text, expected_text, expected_language",
    [
        (
            "Dieser Text ist in deutscher Sprache verfasst.",
            "This is the english translation result.",
            "de",
        )
    ],
)
def test_translate(text: str, expected_text: str, expected_language: str):
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    libre_translate_api.translate.return_value = expected_text

    result = translate(
        text,
        LibreTranslateLanguageDetectResult(
            [LibretranslateDetectedLanguage(confidence=1, language=expected_language)]
        ),
    )

    assert len(result) == 1
    for language, translate_text in result.items():
        assert language.language == expected_language
        assert translate_text == expected_text


def test_translate_empty_text():
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    text = ""
    result = translate(text, LibreTranslateLanguageDetectResult())
    assert not libre_translate_api.translate.called
    assert len(result) == 0


@pytest.mark.parametrize(
    "expected_translation_calls",
    [0, 1, 10, 20, 100],
)
def test_translate_long_word(expected_translation_calls):
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()

    text = "x" * LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST * expected_translation_calls
    translation_mock = "mocktranslation"
    libre_translate_api.translate.return_value = translation_mock
    result = translate(
        text,
        LibreTranslateLanguageDetectResult(
            [LibretranslateDetectedLanguage(confidence=1, language="de")]
        ),
    )

    expected_text = translation_mock * libre_translate_api.translate.call_count
    assert len(result) == 1
    assert libre_translate_api.translate.call_count == expected_translation_calls
    for _, translate_text in result.items():
        assert translate_text == expected_text


@pytest.mark.parametrize(
    "expected_translation_calls",
    [0, 1, 10, 20],
)
def test_translate_long_text(expected_translation_calls):
    from common.dependencies import (  # pylint: disable=import-outside-toplevel
        get_libretranslate_api,
    )

    libre_translate_api = get_libretranslate_api()
    translation_mock = "mocktranslation"
    libre_translate_api.translate.return_value = translation_mock

    for world_len in range(LIBRETRANSLATE_MAX_BACKTRACK_RANGE * 2):
        text_word = "x" * world_len
        text = (text_word + " ") * int(
            LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST * expected_translation_calls
        )
        text = text[
            : LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST * expected_translation_calls
        ]

        result = translate(
            text,
            LibreTranslateLanguageDetectResult(
                [LibretranslateDetectedLanguage(confidence=1, language="de")]
            ),
        )

        assert libre_translate_api.translate.call_count in (
            expected_translation_calls,
            expected_translation_calls + 1,
        )
        expected_text = translation_mock * libre_translate_api.translate.call_count
        libre_translate_api.translate.reset_mock()
        assert len(result) == 1
        for _, translate_text in result.items():
            assert translate_text == expected_text
