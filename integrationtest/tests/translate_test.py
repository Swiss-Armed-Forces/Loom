from collections import Counter
from typing import Callable
from unittest.mock import MagicMock

import pytest
import requests
from api.models.query_model import QueryModel
from api.routers.files import GetFileLanguageTranslations, TranslateFileRequest
from api.routers.translation import TranslateAllRequest
from common.dependencies import get_lazybytes_service
from common.file.file_repository import File
from pydantic import BaseModel
from requests import Response
from worker.index_file.tasks.translate import (
    LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST,
    LibretranslateDetectedLanguage,
    translate_task,
)

from utils.consts import FILES_ENDPOINT, REQUEST_TIMEOUT, TRANSLATION_ENDPOINT
from utils.fetch_from_api import build_search_string, get_file_by_name
from utils.split_into_sentences import split_into_sentences
from utils.upload_asset import upload_bytes_asset


class TranslationFileTest(BaseModel):
    file_id: str
    name: str


TRANSLATION_TESTCASES = [
    # "content, expected_translations, expected_on_demand_translations"
    (
        "Soy dueño de esta casa azul y grande en el mar.",
        [
            GetFileLanguageTranslations(
                confidence=100.0,
                language="es",
                text="I own this blue, big house at sea.",
            )
        ],
        [
            GetFileLanguageTranslations(
                confidence=100.0,
                language="pt",
                text="Soy dueño of this big and blue house in the sea.",
            ),
        ],
    ),
    (
        # Mixing languages on purpose
        (
            "I own this big blue house at the sea. But I want to sell it.\n"
            "У меня есть большой синий дом на берегу моря. Но я хочу его продать.\n"
            "Espero que me salga bien de precio.!\n"
        ),
        [
            # Mixing languages has lowers confidence of language detection by quite a bit
        ],
        [
            GetFileLanguageTranslations(
                confidence=100.0,
                language="ru",
                text=(
                    "I own this big blue house at the sea. But I want to sell it.\nI"
                    " have a big blue house by the sea. But I want to sell"
                    " it.\nEspero que me salga bien de precio. !\n!"
                ),
            ),
        ],
    ),
]


def test_get_libretranslate_languages():
    langs = requests.get(
        f"{TRANSLATION_ENDPOINT}/languages", timeout=REQUEST_TIMEOUT
    ).json()
    assert isinstance(langs, list)
    assert len(langs) != 0


def test_translate_huge_text():
    text_piece = "Ein kurzer deutscher Satz. "
    text_repetitions = (
        LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST // len(text_piece)
    ) * 10
    text = text_piece * text_repetitions

    expected_text_piece = "A short German sentence. "
    expected_text = expected_text_piece * text_repetitions
    expected_text_sentences_counted = Counter(split_into_sentences(expected_text))

    file = MagicMock(File)
    file.sha256 = "test"

    detection_result = [LibretranslateDetectedLanguage(confidence=100, language="de")]
    text_lazy = get_lazybytes_service().from_bytes(text.encode())
    translation_result = translate_task((text_lazy, detection_result), file)
    text_translated_sentences_counted = Counter(
        split_into_sentences(translation_result[0].text)
    )
    assert expected_text_sentences_counted == text_translated_sentences_counted


def _on_demand_translate_by_query(query: QueryModel, lang: str):
    response: Response = requests.post(
        f"{TRANSLATION_ENDPOINT}/",
        json=TranslateAllRequest(
            lang=lang,
            query=query,
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _on_demand_translate_by_file(file: TranslationFileTest, lang: str):
    response: Response = requests.post(
        f"{FILES_ENDPOINT}/{file.file_id}/translate",
        json=TranslateFileRequest(
            lang=lang,
        ).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def _assert_all_translation(
    expected_translations: list[GetFileLanguageTranslations],
    libretranslate_language_translations: list[GetFileLanguageTranslations],
):
    assert len(expected_translations) == len(libretranslate_language_translations)
    for expected_translation in expected_translations:
        assert expected_translation in libretranslate_language_translations


def _translation_testcase(
    on_demand_translation: Callable[[TranslationFileTest, str], None],
    content: str,
    expected_translations: list[GetFileLanguageTranslations],
    expected_on_demand_translations: list[GetFileLanguageTranslations] | None,
):
    file_name = "text.txt"
    upload_bytes_asset(content.encode(), file_name)

    # wait for file to be processed
    file = get_file_by_name(file_name)

    # create a custome model to be able to generalize the calls
    translation_file = TranslationFileTest(file_id=str(file.file_id), name=file.name)

    # should not be translated yet:
    _assert_all_translation(
        expected_translations,
        file.libretranslate_language_translations,
    )

    if expected_on_demand_translations is not None:
        for expected_on_demand_translation in expected_on_demand_translations:
            # demand translation
            on_demand_translation(
                translation_file, expected_on_demand_translation.language
            )
        # Note: we have to wait until celery is idle, because `on_demand_translation`
        # is an async operation and `get_file_by_name` might return before
        # translation even started.
        file = get_file_by_name(file_name, wait_for_celery_idle=True)
        _assert_all_translation(
            expected_translations + expected_on_demand_translations,
            file.libretranslate_language_translations,
        )


@pytest.mark.parametrize(
    "content, expected_translations, expected_on_demand_translations",
    TRANSLATION_TESTCASES,
)
def test_on_demand_translation_by_file(
    content: str,
    expected_translations: list[GetFileLanguageTranslations],
    expected_on_demand_translations: list[GetFileLanguageTranslations] | None,
):
    _translation_testcase(
        on_demand_translation=_on_demand_translate_by_file,
        content=content,
        expected_translations=expected_translations,
        expected_on_demand_translations=expected_on_demand_translations,
    )


@pytest.mark.parametrize(
    "content, expected_translations, expected_on_demand_translations",
    TRANSLATION_TESTCASES,
)
def test_on_demand_translation_by_query(
    content: str,
    expected_translations: list[GetFileLanguageTranslations],
    expected_on_demand_translations: list[GetFileLanguageTranslations] | None,
):
    def on_demand_function(file: TranslationFileTest, lang: str):
        _on_demand_translate_by_query(
            QueryModel(
                search_string=build_search_string(
                    search_string="*", field="full_name", field_value=file.name
                )
            ),
            lang,
        )

    _translation_testcase(
        on_demand_translation=on_demand_function,
        content=content,
        expected_translations=expected_translations,
        expected_on_demand_translations=expected_on_demand_translations,
    )
