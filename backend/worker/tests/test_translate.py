import logging
from math import floor
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from common.file.file_repository import File, FilePurePath
from common.llm.exceptions import LLMError, LLMTransientError
from common.llm.return_types import DetectedLanguage, LanguagesToDetect
from common.services.lazybytes_service import InMemoryTempLazyBytesService
from openai import APIConnectionError
from pydantic_ai.exceptions import ModelHTTPError

from worker.dependencies import (
    get_llm_language_detection_agent,
    get_llm_translation_agent,
    get_llm_translation_language_detection_so_agent,
)
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.tasks.translate import (
    MAX_CHARACTERS_PER_CHUNK,
    LanguageDetection,
    detect_language_system_one,
    detect_language_system_one_task,
    get_translation_text_splitter,
    translate,
    translate_detect_language,
    translate_detect_language_task,
)
from worker.settings import settings


def _llm_language_detection_agent() -> MagicMock:
    return cast(MagicMock, get_llm_language_detection_agent())


def _llm_translate_agent() -> MagicMock:
    return cast(MagicMock, get_llm_translation_agent())


def _assert_call_count(mock: MagicMock, expected: int) -> None:
    assert mock.call_count == expected


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
    detection_result = [
        DetectedLanguage(language=expected_language, confidence=expected_confidence)
    ]

    _llm_language_detection_agent().run_sync.return_value = SimpleNamespace(
        output=detection_result
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
    detection_result = [
        DetectedLanguage(language=expected_language, confidence=expected_confidence)
    ]

    _llm_language_detection_agent().run_sync.return_value = SimpleNamespace(
        output=detection_result
    )

    result = translate_detect_language(text)
    assert len(result) == 0


def test_translate_detect_language_empty_text():
    _llm_language_detection_agent()
    text = ""
    result = translate_detect_language(text)
    assert len(result) == 0


def test_translate_detect_llm_error():
    agent = get_llm_language_detection_agent()
    agent.run_sync.side_effect = APIConnectionError(request=MagicMock())

    with pytest.raises(LLMError):
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
    agent = _llm_translate_agent()
    agent.run_sync.return_value = SimpleNamespace(
        output=SimpleNamespace(text=expected_text)
    )

    translation = translate(
        text, DetectedLanguage(confidence=1, language=expected_language)
    )

    assert translation == expected_text
    _assert_call_count(agent.run_sync, expected_translate_calls)


def test_translate_llm_error():
    _llm_translate_agent().run_sync.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(LLMError):
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


def _bound_task(*, is_last_attempt: bool) -> FileIndexingTask:
    """Stand in for the ``self`` of a bound task.

    ``BaseTask.is_last_attempt`` reads the live retry state, which only exists inside a
    worker, so the attribute is set directly here.
    """
    task = MagicMock(spec=FileIndexingTask)
    task.is_last_attempt = is_last_attempt
    return cast(FileIndexingTask, task)


def _file() -> File:
    return File(
        full_name=FilePurePath("report.pdf"),
        source="api-upload",
        sha256="abc123",
        size=42,
    )


def _system_one_agent_reporting(probabilities: dict[str, float] | None) -> MagicMock:
    """The decision agent, answering with one distribution.

    ``None`` stands for a response that carries no ``provider_details`` at all, which is
    the shape the defensive read in `detect_language_system_one` exists for.
    """
    agent = cast(MagicMock, get_llm_translation_language_detection_so_agent())
    details = (
        None
        if probabilities is None
        else {"probabilities": {"language": probabilities}}
    )
    agent.run_sync.return_value = SimpleNamespace(
        response=SimpleNamespace(provider_details=details)
    )
    return agent


def test_other_is_never_a_detected_language():
    """ "other" says the text carries no language signal, so it cannot be translated
    from -- not even when the model is certain of it."""
    _system_one_agent_reporting({LanguagesToDetect.OTHER.value: 1.0})

    assert not detect_language_system_one("a short text")


def test_a_language_below_the_confidence_gate_is_dropped():
    """Behind the gate is one LLM call per 2000 characters, per language."""
    gate = settings.min_language_detection_system_one_confidence / 100
    _system_one_agent_reporting({"de": gate - 0.01, "en": gate})

    assert [
        detected.language for detected in detect_language_system_one("a short text")
    ] == ["en"]


def test_a_response_without_provider_details_detects_nothing():
    """A decision model that declined to answer reports no distribution; reading it must
    leave the file to the generative pass rather than raise a TypeError."""
    _system_one_agent_reporting(None)

    assert not detect_language_system_one("a short text")


def test_a_failing_decision_model_does_not_abort_the_translate_chain(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    caplog: pytest.LogCaptureFixture,
):
    """A failed link aborts the rest of the chain, which would leave the file with no
    translation and no detected language -- while the generative detector can answer the
    same question."""
    agent = cast(MagicMock, get_llm_translation_language_detection_so_agent())
    agent.run_sync.side_effect = ModelHTTPError(status_code=404, model_name="typo")
    text_lazy = lazybytes_service_inmemory.from_bytes(
        "Dieser Text ist in deutscher Sprache verfasst.".encode()  # spellchecker:disable-line
    )

    with caplog.at_level(logging.WARNING):
        detection = detect_language_system_one_task(
            _bound_task(is_last_attempt=False), text_lazy, _file()
        )

    assert detection == LanguageDetection(text_lazy, None)
    assert "generative detector" in caplog.text


def test_a_transient_failure_is_raised_while_retries_remain(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
):
    agent = cast(MagicMock, get_llm_translation_language_detection_so_agent())
    agent.run_sync.side_effect = ModelHTTPError(status_code=503, model_name="tev1")
    text_lazy = lazybytes_service_inmemory.from_bytes(
        "Dieser Text ist in deutscher Sprache verfasst.".encode()  # spellchecker:disable-line
    )

    with pytest.raises(LLMTransientError):
        detect_language_system_one_task(
            _bound_task(is_last_attempt=False), text_lazy, _file()
        )


def test_an_answered_system_one_pass_skips_the_generative_detector():
    """The whole point of the first pass: a generation per file is what it saves."""
    generative = _llm_language_detection_agent()
    detection = LanguageDetection(
        MagicMock(), [DetectedLanguage(confidence=99, language="de")]
    )

    assert translate_detect_language_task(detection, _file()) == detection
    _assert_call_count(generative.run_sync, 0)
