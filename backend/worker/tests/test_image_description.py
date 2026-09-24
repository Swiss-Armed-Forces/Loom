from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import httpx
import pytest
from common.dependencies import get_llm_vision_agent
from openai import APIConnectionError, APIError, InternalServerError

from worker.index_file.tasks.image_description import (
    LLMError,
    describe_image,
    is_image,
)

# pylint: disable=redefined-outer-name

IMAGE_BYTES = b"not-a-real-image-but-good-enough-for-base64"


@pytest.fixture
def vision_agent() -> MagicMock:
    """The vision LLM agent, mocked and pre-set with a successful response.

    ``mock_init`` (run by the autouse ``dependencies_init`` fixture) installs the global
    vision agent as a ``MagicMock``; we fetch it through the public
    ``get_llm_vision_agent`` accessor and configure it.

    Tests that care about the response override ``run_sync.return_value`` /
    ``run_sync.side_effect``; tests that only assert on the request arguments can use it
    as-is.

    The whole run result is replaced rather than only its ``output`` attribute: reading
    ``run_sync.return_value`` off the cast makes pylint resolve ``run_sync`` to the real
    ``Agent`` method, which has no such member.
    """
    agent = cast(MagicMock, get_llm_vision_agent())
    agent.run_sync.return_value = SimpleNamespace(
        output=SimpleNamespace(description="ok")
    )
    return agent


# ---------------------------------------------------------------------------
# is_image
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "extension, mimetype, expected",
    [
        (".png", "", True),
        (".jpg", "", True),
        (".jpeg", "", True),
        (".txt", "", False),
        ("", "image/png", True),
        ("", "image/gif", True),
        ("", "image/jpeg", True),
        ("", "text/plain", False),
        # tika mimetype is enough even when the extension is not an image
        (".txt", "image/png", True),
        # neither signal present
        ("", "", False),
    ],
)
def test_is_image(extension: str, mimetype: str, expected: bool):
    assert is_image(extension, mimetype) is expected


# ---------------------------------------------------------------------------
# describe_image
# ---------------------------------------------------------------------------


def test_describe_image_returns_model_content(vision_agent: MagicMock):
    vision_agent.run_sync.return_value = SimpleNamespace(
        output=SimpleNamespace(description="A photo of a cat.")
    )

    result = describe_image(memoryview(IMAGE_BYTES))

    assert result == "A photo of a cat."
    vision_agent.run_sync.assert_called_once()


@pytest.mark.parametrize(
    "api_error",
    [
        # network failure
        APIConnectionError(request=httpx.Request("POST", "http://vision-llm")),
        # what Ollama returns for a non-image file ("image: unknown format");
        # vLLM returns a 400 "cannot identify image file" the same way.
        InternalServerError(
            "image: unknown format",
            response=httpx.Response(
                500, request=httpx.Request("POST", "http://vision-llm")
            ),
            body=None,
        ),
    ],
)
def test_describe_image_wraps_api_error(vision_agent: MagicMock, api_error: APIError):
    vision_agent.run_sync.side_effect = api_error

    with pytest.raises(LLMError):
        describe_image(memoryview(IMAGE_BYTES))


def test_describe_image_returns_empty_string_when_model_returns_no_content(
    vision_agent: MagicMock,
):
    vision_agent.run_sync.return_value = SimpleNamespace(
        output=SimpleNamespace(description="")
    )
    result = describe_image(memoryview(IMAGE_BYTES))

    assert result == ""
