from openai import LengthFinishReasonError
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion


def length_finish_reason_error() -> LengthFinishReasonError:
    """The failure observed in #287: reasoning tokens exhausted ``max_tokens``.

    The model never emitted the structured JSON, so the SDK's ``.parse()`` raised before
    returning a response.
    """
    return LengthFinishReasonError(
        completion=ChatCompletion(
            id="chatcmpl-test",
            choices=[],
            created=0,
            model="Qwen/Qwen3.5-122B-A10B-FP8",
            object="chat.completion",
            usage=CompletionUsage(
                completion_tokens=8192, prompt_tokens=458, total_tokens=8650
            ),
        )
    )
