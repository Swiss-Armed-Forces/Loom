import json
from collections.abc import Iterator
from datetime import datetime
from typing import Any
from uuid import UUID

from common.ai_context.tool_models import FileFieldInfo
from common.utils.pydantic_field_paths import iter_model_fields
from pydantic import BaseModel

from worker.utils.prompt_sanitizer import sanitize_document_text

_MAX_CONTENT_CHARS = 8000


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


def validate_file_id(file_id: str) -> UUID:
    try:
        return UUID(file_id)
    except ValueError as exc:
        raise ValueError(
            f"Invalid file_id '{file_id}': must be a valid UUID string."
        ) from exc


def serialize_field_value(path: str, value: Any) -> str:
    if path == "content":
        return sanitize_document_text(str(value))[:_MAX_CONTENT_CHARS]
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    if isinstance(value, list):
        return json.dumps(value, default=str)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
