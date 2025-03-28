import logging
from dataclasses import dataclass
from string import punctuation

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_libretranslate_api,
)
from common.file.file_repository import (
    File,
    LibretranslateTranslatedLanguage,
    LibreTranslateTranslations,
)
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE, TikaResult
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

LIBRETRANSLATE_MAX_TEXT_SIZE = TIKA_MAX_TEXT_SIZE
LIBRETRANSLATE_CHARACTERS_PER_SECOND = 125  # An estimated average
LIBRETRANSLATE_MAX_REQUEST_LEN_SECONDS = (
    180  # From libretranslate/Dockerfile (--timeout)
)
LIBRETRANSLATE_SAFETY_MARGIN = 0.6
LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST = int(
    LIBRETRANSLATE_CHARACTERS_PER_SECOND
    * LIBRETRANSLATE_MAX_REQUEST_LEN_SECONDS
    * LIBRETRANSLATE_SAFETY_MARGIN
)
LIBRETRANSLATE_MAX_BACKTRACK_RANGE = min(
    2 * 100,  # 2 * average english sentence length
    int(
        # this is just here as a safety, so that we never backtrack too far
        LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST
        * 0.9
    ),
)


logger = logging.getLogger(__name__)

app = get_celery_app()


@dataclass(frozen=True)
class LibretranslateDetectedLanguage:
    confidence: float
    language: str


LibreTranslateLanguageDetectResult = list[LibretranslateDetectedLanguage]


def signature(file: File) -> Signature:
    """Create the signature for translation."""
    if settings.skip_translate_while_indexing:
        return noop.s()

    return chain(
        extract_text_from_tika_result.s(),
        translate_detect_language_task.s(file),
        translate_task.s(file),
        persist_translation.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(base=FileIndexingTask)
def extract_text_from_tika_result(tika_result: TikaResult) -> LazyBytes | None:
    return tika_result.text


@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, file: file.sha256)
def translate_detect_language_task(
    text_lazy: LazyBytes | None,
    file: File,  # pylint: disable=unused-argument
) -> tuple[LazyBytes | None, LibreTranslateLanguageDetectResult | None]:
    """Detect languages."""
    if text_lazy is None:
        return text_lazy, None

    # Unfortunately libretranslate does not handle memoryviews well, it will silently always
    # detect english with 0.0 confidence. We need to load it as string here.
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:LIBRETRANSLATE_MAX_TEXT_SIZE]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        # limit text size used for languge detection
        text = text[:LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST]
        result = translate_detect_language(text)
    return text_lazy, result


def translate_detect_language(text: str) -> LibreTranslateLanguageDetectResult:
    result = LibreTranslateLanguageDetectResult()
    if len(text) <= 0:
        return result

    libre_translate = get_libretranslate_api()

    detected_languages = libre_translate.detect(text)

    for detected_language in detected_languages:
        detected_language = LibretranslateDetectedLanguage(**detected_language)
        if detected_language.confidence >= settings.min_language_detection_confidence:
            result.append(detected_language)

    return result


@app.task(base=FileIndexingTask)
@cache(
    key_function=lambda translate_detect_language_result, file: (
        (
            translate_detect_language_result[1]
            if translate_detect_language_result
            else None
        ),
        file.sha256,
    ),
)
def translate_task(
    translate_detect_language_result: tuple[
        LazyBytes | None, LibreTranslateLanguageDetectResult | None
    ],
    file: File,  # pylint: disable=unused-argument
) -> LibreTranslateTranslations | None:
    (text_lazy, detected_languages) = translate_detect_language_result
    if text_lazy is None or detected_languages is None:
        return None

    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:LIBRETRANSLATE_MAX_TEXT_SIZE]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        language_translations = translate(text, detected_languages)

    result = LibreTranslateTranslations()
    for language, translation in language_translations.items():
        result.append(
            LibretranslateTranslatedLanguage(
                language=language.language,
                confidence=language.confidence,
                text=translation,
            )
        )
    return result


def translate(
    text: str, detected_languages: LibreTranslateLanguageDetectResult
) -> dict[LibretranslateDetectedLanguage, str]:
    result = {}
    libre_translate = get_libretranslate_api()

    for language in detected_languages:
        translation_result = ""

        # Do not translate if detected language already matches the target language
        if language.language == settings.translate_target:
            result[language] = text
            continue

        # split text into manageable chunks
        remaining_text = text
        while len(remaining_text) > 0:
            text_to_translate = remaining_text[
                :LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST
            ]
            remaining_text = remaining_text[LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST:]

            if len(text_to_translate) == LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST:
                # we have maxed-out the translation request size:
                # try to backtrack a few characters to the last punctuation
                for _ in range(LIBRETRANSLATE_MAX_BACKTRACK_RANGE):
                    last_char = text_to_translate[-1]
                    if last_char in punctuation:
                        break
                    text_to_translate = text_to_translate[:-1]
                    remaining_text = last_char + remaining_text
                else:
                    # backtracking failed: restore original
                    text_to_translate += remaining_text[
                        :LIBRETRANSLATE_MAX_BACKTRACK_RANGE
                    ]
                    remaining_text = remaining_text[LIBRETRANSLATE_MAX_BACKTRACK_RANGE:]

            if len(text_to_translate) > 0:
                translation_result += libre_translate.translate(
                    text_to_translate,
                    language.language,
                    settings.translate_target,
                )

        translation_result = translation_result.strip()
        result[language] = translation_result

    return result


@persisting_task(app, IndexingPersister)
def persist_translation(
    persister: IndexingPersister,
    translations: list[LibretranslateTranslatedLanguage],
):
    """Persists the translation result."""
    if translations is None:
        return

    if len(translations) > 0:
        persister.set_libretranslate_language(translations[0].language)

    for translation in translations:
        persister.add_or_replace_libretranslate_translated_language(translation)
