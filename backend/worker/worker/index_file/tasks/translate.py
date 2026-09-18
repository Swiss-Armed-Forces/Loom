import logging

from celery import chain, chord, group
from celery.canvas import Signature
from common.agent_builder import sanitize_document_text
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
    get_llm_language_detection_agent,
    get_llm_translation_agent,
)
from common.file.file_repository import DetectedLanguage, File, TranslatedLanguage
from common.services.lazybytes_service import TempLazyBytes
from common.utils.cache import cache
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from pydantic import BaseModel
from pydantic_ai import NativeOutput

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

MAX_TRANSLATION_TEXT_SIZE = TIKA_MAX_TEXT_SIZE
MAX_CHARACTERS_PER_CHUNK = 2000
TRANSLATE_MAX_RETRIES = 15


logger = logging.getLogger(__name__)

app = get_celery_app()


class _TranslationResult(BaseModel):
    text: str


class LLMError(Exception):
    pass


def signature(file: File) -> Signature:
    """Create the signature for translation."""
    if settings.skip_translate_while_indexing:
        return noop.s()

    return chain(
        translate_detect_language_task.s(file),
        group(
            translate_task.s(file),
            chain(
                translate_get_best_detected_language.s(),
                persist_best_detected_language.s(file.id_),
            ),
        ),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache(key_function=lambda _, file: file.sha256)
def translate_detect_language_task(
    text_lazy: TempLazyBytes | None,
    file: File,  # pylint: disable=unused-argument
) -> tuple[TempLazyBytes | None, list[DetectedLanguage] | None]:
    if text_lazy is None:
        return text_lazy, None

    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_TRANSLATION_TEXT_SIZE]
            .tobytes()
            .decode(errors=settings.decode_error_handler)
        )
        # limit text size used for language detection
        text = text[:MAX_CHARACTERS_PER_CHUNK]

        # Do not attempt detecting languages if the text just consists of
        # whitespace characters
        if len(text.strip()) <= 0:
            return text_lazy, None

        detected_languages = translate_detect_language(text)
    return text_lazy, detected_languages


def translate_detect_language(text: str) -> list[DetectedLanguage]:
    result: list[DetectedLanguage] = []
    if len(text) <= 0:
        return result

    prompt = (
        "Detect the language of the text in the following "
        "<document>...</document> tags:\n\n"
        f"<document>\n{sanitize_document_text(text)}\n</document>"
    )

    agent = get_llm_language_detection_agent()

    try:
        result_agent = agent.run_sync(prompt)

    except Exception as ex:
        raise LLMError("Language detection failed") from ex

    for detected_language in result_agent.output:
        if detected_language.confidence >= settings.min_language_detection_confidence:
            result.append(detected_language)

    return result


def get_translation_text_splitter() -> TextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHARACTERS_PER_CHUNK,
        chunk_overlap=0,
        separators=["\n\n", "\n", ".", "!", "?", ":", ";", " "],
        keep_separator="end",
        strip_whitespace=False,
    )


@app.task(bind=True, base=FileIndexingTask)
def translate_task(
    self: FileIndexingTask,
    translate_detect_language_result: tuple[
        TempLazyBytes | None, list[DetectedLanguage] | None
    ],
    file: File,
):
    text_lazy, detected_languages = translate_detect_language_result
    if text_lazy is None or detected_languages is None:
        return None

    text_splitter = get_translation_text_splitter()

    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[:MAX_TRANSLATION_TEXT_SIZE]
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
                        persist_translation.s(file.id_),
                    ),
                )
                for detected_language in detected_languages
            )
        )


@app.task(
    base=FileIndexingTask,
    autoretry_for=tuple([LLMError]),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache()
def translate(text: str, detected_language: DetectedLanguage) -> str:
    if len(text) <= 0:
        return text

    # Do not translate if detected language already matches the target language
    if detected_language.language == settings.translate_target:
        return text

    prompt = (
        (
            f"Translate the text in the following "
            f"<document>...</document> tags to {settings.translate_target}:\n\n"
            f"<document>\n{sanitize_document_text(text)}\n</document>"
        ),
    )

    agent = get_llm_translation_agent()

    try:
        result = agent.run_sync(prompt, output_type=NativeOutput(_TranslationResult))

    except Exception as ex:
        raise LLMError("Translation failed") from ex

    return result.output.text


@app.task(base=FileIndexingTask)
def combine_translation(
    translation_results: list[str],
    detected_language: DetectedLanguage,
) -> TranslatedLanguage:
    translation_result = "".join(translation_results)
    return TranslatedLanguage(
        confidence=detected_language.confidence,
        language=detected_language.language,
        text=translation_result,
    )


@persisting_task(app, IndexingPersister)
def persist_translation(
    persister: IndexingPersister,
    translation: TranslatedLanguage,
):
    """Persists the translation result."""
    persister.add_or_replace_translated_language(translation)


@app.task(base=FileIndexingTask)
def translate_get_best_detected_language(
    translate_detect_language_result: tuple[
        TempLazyBytes | None, list[DetectedLanguage] | None
    ],
) -> str | None:
    _, detected_languages = translate_detect_language_result
    if detected_languages is None:
        return None
    best_detected_language = (
        max(detected_languages, key=lambda x: x.confidence)
        if detected_languages
        else None
    )
    return best_detected_language.language if best_detected_language else None


@persisting_task(app, IndexingPersister)
def persist_best_detected_language(
    persister: IndexingPersister,
    best_detected_language: str | None,
):
    if best_detected_language is None:
        return
    persister.set_detected_language(best_detected_language)
