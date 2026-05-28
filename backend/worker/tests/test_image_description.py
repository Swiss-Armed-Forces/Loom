import base64
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import httpx
import pytest
from common.dependencies import get_llm_vision_client
from openai import APIConnectionError, APIError, InternalServerError

from worker.index_file.tasks.image_description import (
    ImageDescriptionError,
    describe_image,
    is_image,
)

# pylint: disable=redefined-outer-name

IMAGE_BYTES = b"not-a-real-image-but-good-enough-for-base64"


def _vision_response(content: str | None) -> SimpleNamespace:
    """Build a minimal stand-in for an OpenAI chat completion response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


@pytest.fixture
def vision_client() -> MagicMock:
    """The vision LLM client, mocked and pre-set with a successful response.

    ``mock_init`` (run by the autouse ``dependencies_init`` fixture) installs the global
    vision client as a ``MagicMock``; we fetch it through the public
    ``get_llm_vision_client`` accessor and configure it.

    Tests that care about the response override ``create.return_value`` /
    ``create.side_effect``; tests that only assert on the request arguments can use it
    as-is.
    """
    client = cast(MagicMock, get_llm_vision_client())
    client.chat.completions.create.return_value = _vision_response("ok")
    return client


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


def test_describe_image_returns_model_content(vision_client: MagicMock):
    vision_client.chat.completions.create.return_value = _vision_response(
        "A photo of a cat."
    )

    result = describe_image(memoryview(IMAGE_BYTES))

    assert result == "A photo of a cat."
    vision_client.chat.completions.create.assert_called_once()


def test_describe_image_sends_base64_encoded_image(vision_client: MagicMock):
    describe_image(memoryview(IMAGE_BYTES))

    messages = vision_client.chat.completions.create.call_args.kwargs["messages"]
    image_part = messages[1]["content"][1]
    expected = base64.b64encode(IMAGE_BYTES).decode("utf-8")
    assert image_part["type"] == "image_url"
    assert image_part["image_url"]["url"] == f"data:image/jpeg;base64,{expected}"


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
def test_describe_image_wraps_api_error(vision_client: MagicMock, api_error: APIError):
    # The OpenAI SDK raises openai.APIError subclasses -- never
    # httpx.HTTPError -- for transport and HTTP failures.
    vision_client.chat.completions.create.side_effect = api_error

    with pytest.raises(ImageDescriptionError):
        describe_image(memoryview(IMAGE_BYTES))


def test_describe_image_raises_when_model_returns_no_content(
    vision_client: MagicMock,
):
    vision_client.chat.completions.create.return_value = _vision_response(None)

    with pytest.raises(ImageDescriptionError):
        describe_image(memoryview(IMAGE_BYTES))
