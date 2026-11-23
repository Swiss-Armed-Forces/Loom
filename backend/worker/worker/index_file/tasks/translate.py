import logging
from typing import NamedTuple

from celery import chain, chord, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
)
from common.file.file_repository import File, TranslatedLanguage
from common.llm.exceptions import (
    LLMError,
    LLMTransientError,
    classify_llm_error,
)
from common.llm.prompt_sanitizer import sanitize_document_text
from common.llm.return_types import (
    LANGUAGE_PROBABILITIES_FIELD,
    DetectedLanguage,
    LanguagesToDetect,
)
from common.services.lazybytes_service import TempLazyBytes
from common.utils.cache import cache
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter

from worker.dependencies import (
    get_llm_language_detection_agent,
    get_llm_translation_agent,
    get_llm_translation_language_detection_so_agent,
)
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TIKA_MAX_TEXT_SIZE
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

MAX_TRANSLATION_TEXT_SIZE = TIKA_MAX_TEXT_SIZE
MAX_CHARACTERS_PER_CHUNK = 2000
MAX_UTF8_BYTES_PER_CHARACTER = 4
TRANSLATE_MAX_RETRIES = 15


logger = logging.getLogger(__name__)

app = get_celery_app()


class LanguageDetection(NamedTuple):
    """A file's text and the languages detected in it, as it travels the chain.

    One value rather than two, because celery passes a task's return value to the next
    link in a chain as a single positional argument whatever its shape.
    """

    text_lazy: TempLazyBytes | None
    detected_languages: list[DetectedLanguage] | None


def signature(file: File) -> Signature:
    """Create the signature for translation."""
    if settings.skip_translate_while_indexing:
        return noop.s()

    return chain(
        detect_language_system_one_task.s(file),
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


def _load_detection_text(text_lazy: TempLazyBytes) -> str | None:
    """The leading text of a file, trimmed for language detection.

    None when what is there is only whitespace, which no detector has an answer for.

    Bounded in bytes by what the characters can need rather than by the whole text:
    four bytes is UTF-8's longest encoding of one character, so the slice still holds
    at least `MAX_CHARACTERS_PER_CHUNK` of them while copying kilobytes instead of
    `MAX_TRANSLATION_TEXT_SIZE`. Both detection passes load this, so the document's
    whole text would otherwise be copied and decoded twice for 2000 characters.
    """
    with get_lazybytes_service().load_memoryview(text_lazy) as memview:
        text = (
            memview[: MAX_CHARACTERS_PER_CHUNK * MAX_UTF8_BYTES_PER_CHARACTER]
            .tobytes()
            .decode(errors=settings.decode_error_handler)[:MAX_CHARACTERS_PER_CHUNK]
        )
    return text if text.strip() else None


@app.task(
    base=FileIndexingTask,
    bind=True,
    autoretry_for=(LLMTransientError,),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache(key_function=lambda _, __, file: file.sha256)
def detect_language_system_one_task(
    self: FileIndexingTask,
    text_lazy: TempLazyBytes | None,
    file: File,  # pylint: disable=unused-argument
) -> LanguageDetection:
    """Heads the translate chain, so a failure here is not this task's alone.

    A failed link aborts the rest of the chain, which would leave the file with no
    translation and no detected language at all -- while the whole point of this pass is
    that `translate_detect_language_task` can answer the same question without it. Once
    the retry budget is spent, the chain carries on with no languages, which is the
    signal that runs the generative detector.
    """
    if text_lazy is None:
        return LanguageDetection(None, None)

    text = _load_detection_text(text_lazy)
    if text is None:
        return LanguageDetection(text_lazy, None)

    try:
        return LanguageDetection(text_lazy, detect_language_system_one(text))
    except LLMError as ex:
        if isinstance(ex, LLMTransientError) and not self.is_last_attempt:
            raise
        logger.warning(
            "System-one language detection failed, leaving the file to the "
            "generative detector (file=%s)",
            file.full_name,
            exc_info=True,
        )
        return LanguageDetection(text_lazy, None)


@app.task(
    base=FileIndexingTask,
    autoretry_for=(LLMTransientError,),
    retry_backoff=True,
    max_retries=TRANSLATE_MAX_RETRIES,
)
@cache(key_function=lambda _, file: file.sha256)
def translate_detect_language_task(
    detection: LanguageDetection,
    file: File,  # pylint: disable=unused-argument
) -> LanguageDetection:
    text_lazy, detected_languages = detection
    if text_lazy is None:
        return LanguageDetection(None, None)

    if detected_languages:
        return detection

    text = _load_detection_text(text_lazy)
    if text is None:
        return LanguageDetection(text_lazy, None)

    return LanguageDetection(text_lazy, translate_detect_language(text))


def detect_language_system_one(text: str) -> list[DetectedLanguage]:
    """The languages a decision model is confident enough about.

    Empty when the model is only confident about "other", and when nothing clears
    `min_language_detection_system_one_confidence` -- `translate_detect_language` is
    what runs next in each case. The whole pass is behind
    `skip_translate_while_indexing`, which switches translation off wholesale.
    """
    result: list[DetectedLanguage] = []
    if len(text) <= 0:
        return result

    sanitized_text = sanitize_document_text(text)

    system_one_agent = get_llm_translation_language_detection_so_agent()

    try:
        system_one_return = system_one_agent.run_sync(sanitized_text)
        details = system_one_return.response.provider_details or {}
        # `probabilities` is empty whenever the model declined to answer, so both
        # levels are read defensively: a malformed response is the service failing
        # and belongs in classify_llm_error, not in a KeyError escaping the task.
        probs = details.get("probabilities", {}).get(LANGUAGE_PROBABILITIES_FIELD, {})
    except Exception as ex:
        raise classify_llm_error(ex, "Language detection failed (system one)") from ex

    for lang, p in probs.items():
        if (
            lang != LanguagesToDetect.OTHER
            and p * 100 >= settings.min_language_detection_system_one_confidence
        ):
            result.append(DetectedLanguage(confidence=p * 100, language=lang))

    return result


def translate_detect_language(text: str) -> list[DetectedLanguage]:
    """The languages a full generative detection pass finds.

    What runs when the system-one pass returned nothing: it is not restricted to
    `LanguagesToDetect`, so it is the only path that can answer with a language the
    decision model has no member for.
    """
    result: list[DetectedLanguage] = []
    if len(text) <= 0:
        return result

    sanitized_text = sanitize_document_text(text)

    prompt = (
        "Detect the language of the text in the following "
        "<document>...</document> tags:\n\n"
        f"<document>\n{sanitized_text}\n</document>"
    )

    agent = get_llm_language_detection_agent()

    try:
        result_agent = agent.run_sync(prompt)

    except Exception as ex:
        raise classify_llm_error(ex, "Language detection failed") from ex

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
    detection: LanguageDetection,
    file: File,
):
    text_lazy, detected_languages = detection
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
    autoretry_for=(LLMTransientError,),
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
        result = agent.run_sync(prompt)

    except Exception as ex:
        raise classify_llm_error(ex, "Translation failed") from ex

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
    detection: LanguageDetection,
) -> str | None:
    _, detected_languages = detection
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
