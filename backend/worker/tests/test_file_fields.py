"""Unit tests for pure helpers in worker/ai/file_fields.py."""

import json
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from worker.ai.file_fields import iter_described_fields, serialize_field_value
from worker.utils.prompt_sanitizer import sanitize_document_text

_MAX_CONTENT_CHARS = 8000


# ---------------------------------------------------------------------------
# iter_described_fields
# ---------------------------------------------------------------------------


class _Leaf(BaseModel):
    described: str = Field(description="a leaf field")
    undescribed: str  # no description — must be skipped


class _Nested(BaseModel):
    child: _Leaf
    top_described: str = Field(description="top-level described")


class _OptionalNested(BaseModel):
    maybe_child: Optional[_Leaf] = None


class _UnionNested(BaseModel):
    union_child: _Leaf | None = None


def test_iter_described_fields_yields_described_skips_undescribed():
    fields = {f.name: f for f in iter_described_fields(_Leaf)}
    assert "described" in fields
    assert fields["described"].description == "a leaf field"
    assert "undescribed" not in fields


def test_iter_described_fields_recurses_into_nested_model():
    fields = {f.name: f for f in iter_described_fields(_Nested)}
    assert "top_described" in fields
    assert "child.described" in fields
    assert "child.undescribed" not in fields


def test_iter_described_fields_optional_unwraps_and_recurses():
    fields = {f.name: f for f in iter_described_fields(_OptionalNested)}
    assert "maybe_child.described" in fields
    assert "maybe_child.undescribed" not in fields


def test_iter_described_fields_union_none_unwraps_and_recurses():
    fields = {f.name: f for f in iter_described_fields(_UnionNested)}
    assert "union_child.described" in fields
    assert "union_child.undescribed" not in fields


# ---------------------------------------------------------------------------
# serialize_field_value
# ---------------------------------------------------------------------------


def test_serialize_field_value_content_truncated_and_sanitized():
    long_text = "A" * (_MAX_CONTENT_CHARS + 500)
    result = serialize_field_value("content", long_text)
    assert len(result) <= _MAX_CONTENT_CHARS
    assert result == sanitize_document_text(long_text)[:_MAX_CONTENT_CHARS]


def test_serialize_field_value_base_model_dumps_json():
    class _Inner(BaseModel):
        x: int = 42

    obj = _Inner()
    result = serialize_field_value("some_field", obj)
    assert json.loads(result) == {"x": 42}


def test_serialize_field_value_list_dumps_json():
    data = ["a", "b", 3]
    result = serialize_field_value("tags", data)
    assert json.loads(result) == data


def test_serialize_field_value_datetime_iso_format():
    dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = serialize_field_value("created_at", dt)
    assert result == dt.isoformat()


def test_serialize_field_value_plain_string_returned_unchanged():
    result = serialize_field_value("author", "Jane Doe")
    assert result == "Jane Doe"
