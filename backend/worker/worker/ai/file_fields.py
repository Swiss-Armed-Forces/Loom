import json
from collections.abc import Iterator
from datetime import datetime
from typing import Any, NamedTuple
from uuid import UUID

from common.ai_context.tool_models import FileFieldInfo
from common.llm.prompt_sanitizer import sanitize_document_text
from common.utils.pydantic_field_paths import iter_model_fields
from pydantic import BaseModel

_MAX_FIELD_CHARS = 8000


class SerializedFieldValue(NamedTuple):
    """A field rendered for the agent, and whether the cap cut it short."""

    value: str
    truncated: bool


def iter_described_fields(
    model_class: type[BaseModel], prefix: str = ""
) -> Iterator[FileFieldInfo]:
    """Recursively yield FileFieldInfo for fields that have a description.

    Fields with a description are yielded as fetchable. Fields without a description
    that are themselves a BaseModel are recursed into, allowing sub-fields to opt in
    individually via their own descriptions.
    """
    for field in iter_model_fields(model_class, prefix):
        if field.field_info.description:
            yield FileFieldInfo(
                name=field.path, description=field.field_info.description
            )
        elif isinstance(field.annotation, type) and issubclass(
            field.annotation, BaseModel
        ):
            yield from iter_described_fields(field.annotation, f"{field.path}.")

    for field_name, computed_info in model_class.model_computed_fields.items():
        if computed_info.description:
            yield FileFieldInfo(
                name=f"{prefix}{field_name}", description=computed_info.description
            )


def validate_file_id(file_id: str) -> UUID:
    try:
        return UUID(file_id)
    except ValueError as exc:
        raise ValueError(
            f"Invalid file_id '{file_id}': must be a valid UUID string."
        ) from exc


def serialize_field_value(value: Any) -> SerializedFieldValue:
    """Render one field for the agent, sanitized and capped at _MAX_FIELD_CHARS.

    Both the sanitization and the cap apply to every field. Every field is derived from
    the document, so any of them can carry role tokens and delimiters into the prompt,
    and any of them can be unbounded: a recipient header on a mailing list, an LLM
    summary whose sentence limit is prompt text rather than an enforced one, and
    arbitrary document metadata all are. The flag is what tells the agent the value it
    holds is a prefix rather than the field.
    """
    if isinstance(value, BaseModel):
        rendered = value.model_dump_json()
    elif isinstance(value, list):
        rendered = json.dumps(value, default=str)
    elif isinstance(value, datetime):
        rendered = value.isoformat()
    else:
        rendered = str(value)

    sanitized = sanitize_document_text(rendered)

    return SerializedFieldValue(
        value=sanitized[:_MAX_FIELD_CHARS],
        truncated=len(sanitized) > _MAX_FIELD_CHARS,
    )
