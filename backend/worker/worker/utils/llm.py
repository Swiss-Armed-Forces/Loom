import re
from typing import Generator, Iterator

from ollama import ChatResponse

THINKING_REGEX = re.compile(
    r"^\s*((<thinking>.*?</thinking>)|(<think>.*?</think>))\s*",
    re.IGNORECASE | re.DOTALL,
)

THINKING_BEGIN_REGEX = re.compile(
    (
        r"^\s*("
        r"(<)|(<t)|(<th)|(<thi)|(<thin)|(<think)|(<thinki)|(<thinking)|(<thinking>)"
        r"(<)|(<t)|(<th)|(<thi)|(<thin)|(<think)|(<think>)"
        r")\s*"
    ),
    re.IGNORECASE | re.DOTALL,
)


def strip_thinking(respones: str) -> str:
    response_without_thinking = re.sub(THINKING_REGEX, "", respones)
    return response_without_thinking


def strip_thinking_on_chat_response_stream(
    stream: Iterator[ChatResponse],
) -> Generator[str, None, None]:
    # first buffer and strip
    message_buffer = ""
    message_buffer_new = ""
    for token in stream:
        message_content = token.message.content
        if message_content is None:
            continue

        message_buffer += message_content
        message_buffer_new = strip_thinking(message_buffer)
        # break, if strip_thinking was successful
        if message_buffer_new != message_buffer:
            break
        # break, if not in thinking process
        if not re.match(THINKING_BEGIN_REGEX, message_buffer_new):
            break
    yield message_buffer_new
    # start yielding all tokens
    for token in stream:
        message_content = token.message.content
        if message_content is None:
            continue
        yield message_content
