import logging
from urllib.error import HTTPError

from celery import chain, chord, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_libretranslate_api,
)
from common.file.file_repository import File, LibretranslateTranslatedLanguage
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from pydantic import BaseModel

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE, TikaResult
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

LIBRETRANSLATE_MAX_TEXT_SIZE = TIKA_MAX_TEXT_SIZE
LIBRETRANSLATE_CHARACTERS_PER_SECOND = 125  # An estimated average
LIBRETRANSLATE_MAX_REQUEST_LEN_SECONDS = (
    30  # From libretranslate/Dockerfile (--timeout)
)
LIBRETRANSLATE_SAFETY_MARGIN = 0.5
LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST = int(
    LIBRETRANSLATE_CHARACTERS_PER_SECOND
    * LIBRETRANSLATE_MAX_REQUEST_LEN_SECONDS
    * LIBRETRANSLATE_SAFETY_MARGIN
)
TRANSLATE_MAX_RETRIES = 15
CORRECT_TRANSLATION_MAX_TOKENS_FACTOR = 1.5


logger = logging.getLogger(__name__)

app = get_celery_app()


class LibretranslateDetectedLanguage(BaseModel, frozen=True):
    confidence: float
    language: str


LibreTranslateLanguageDetectResult = list[LibretranslateDetectedLanguage]


class LibretranslateInternalException(Exception):
    pass


def signature(file: File) -> Signature:
    """Create the signature for translation."""
    if settings.skip_translate_while_indexing:
        return noop.s()

    return chain(
        extract_text_from_tika_result.s(),
        translate_detect_language_task.s(file),
        translate_task.s(file),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(base=FileIndexingTask)
def extract_text_from_tika_result(tika_result: TikaResult) -> LazyBytes | None:
    return tika_result.text


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LibretranslateInternalException]),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache(key_function=lambda _, file: file.sha256)
def translate_detect_language_task(
    text_lazy: LazyBytes | None,
    file: File,  # pylint: disable=unused-argument
) -> tuple[LazyBytes | None, LibreTranslateLanguageDetectResult | None]:
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
        # limit text size used for language detection
        text = text[:LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST]

        # Do not attempt detecting languages if the text just consists of
        # whitespace characters
        if len(text.strip()) < 0:
            return text_lazy, None

        detected_languages = translate_detect_language(text)
    return text_lazy, detected_languages


def translate_detect_language(text: str) -> LibreTranslateLanguageDetectResult:
    result = LibreTranslateLanguageDetectResult()
    if len(text) <= 0:
        return result

    libre_translate = get_libretranslate_api()
    try:
        detected_languages = libre_translate.detect(text)
    except HTTPError as ex:
        if 500 <= ex.code < 600:
            raise LibretranslateInternalException from ex
        raise ex
    except OSError as ex:
        raise LibretranslateInternalException from ex

    for detected_language in detected_languages:
        detected_language = LibretranslateDetectedLanguage.model_validate(
            detected_language
        )
        if detected_language.confidence >= settings.min_language_detection_confidence:
            result.append(detected_language)

    return result


def get_translation_text_splitter() -> TextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=LIBRETRANSLATE_MAX_CHARACTERS_PER_REQUEST,
        chunk_overlap=0,
        separators=["\n\n", "\n", ".", "!", "?", ":", ";", " "],
        keep_separator="end",
        strip_whitespace=False,
    )


@app.task(bind=True, base=FileIndexingTask)
def translate_task(
    self: FileIndexingTask,
    translate_detect_language_result: tuple[
        LazyBytes | None, LibreTranslateLanguageDetectResult | None
    ],
    file: File,
):
    (text_lazy, detected_languages) = translate_detect_language_result
    if text_lazy is None or detected_languages is None:
        return None

    text_splitter = get_translation_text_splitter()

    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:LIBRETRANSLATE_MAX_TEXT_SIZE]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )

        text_chunks = text_splitter.split_text(text)
        return self.replace(
            group(
                chord(
                    [
                        translate.s(text_chunk, detected_language)
                        for text_chunk in text_chunks
                    ],
                    chain(
                        combine_translation.s(detected_language),
                        persist_translation.s(file),
                    ),
                )
                for detected_language in detected_languages
            )
        )


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LibretranslateInternalException]),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache()
def translate(text: str, detected_language: LibretranslateDetectedLanguage) -> str:
    if len(text) <= 0:
        return text

    # Do not translate if detected language already matches the target language
    if detected_language.language == settings.translate_target:
        return text

    libretranslate_api = get_libretranslate_api()

    try:
        translation_result: str = libretranslate_api.translate(
            text,
            detected_language.language,
            settings.translate_target,
        )
    except HTTPError as ex:
        if 500 <= ex.code < 600:
            raise LibretranslateInternalException from ex
        raise ex
    except OSError as ex:
        raise LibretranslateInternalException from ex

    return translation_result


@app.task(base=FileIndexingTask)
def combine_translation(
    translation_results: list[str],
    detected_language: LibretranslateDetectedLanguage,
) -> LibretranslateTranslatedLanguage:
    translation_result = "".join(translation_results)
    return LibretranslateTranslatedLanguage(
        confidence=detected_language.confidence,
        language=detected_language.language,
        text=translation_result,
    )


@persisting_task(app, IndexingPersister)
def persist_translation(
    persister: IndexingPersister,
    translation: LibretranslateTranslatedLanguage,
):
    """Persists the translation result."""
    persister.add_or_replace_libretranslate_translated_language(translation)
