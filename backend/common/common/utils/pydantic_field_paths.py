import types
from collections.abc import Iterator
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Generic,
    NamedTuple,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel
from pydantic.fields import FieldInfo

T = TypeVar("T")


class ModelField(NamedTuple):
    """A single field entry yielded by _iter_model_fields."""

    path: str
    field_info: FieldInfo
    annotation: Any


@dataclass(frozen=True)
class FieldWithMetadata(Generic[T]):
    """A field path together with its matched metadata marker."""

    path: str
    marker: T


def _iter_model_fields(
    model_class: type[BaseModel],
    prefix: str,
) -> Iterator[ModelField]:
    """Yield ModelField(path, field_info, unwrapped_annotation) for each field at this
    level.

    Unwraps Optional[X] / X | None before yielding. Does not recurse — callers handle
    recursion decisions.
    """
    for field_name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)
        if origin in (Union, types.UnionType):
            non_none_args = [a for a in get_args(annotation) if a is not types.NoneType]
            annotation = non_none_args[0] if len(non_none_args) == 1 else annotation
        yield ModelField(
            path=f"{prefix}{field_name}", field_info=field_info, annotation=annotation
        )


def iter_field_paths_by_type(
    model_class: type[BaseModel],
    target_type: type,
    suffix: str = "",
    _prefix: str = "",
) -> Iterator[str]:
    """Recursively yield field paths for all fields of target_type in a Pydantic model.

    Unwraps Optional[X] / X | None annotations before matching. Recurses into
    nested Pydantic models. Does not recurse into Union types with more than one
    non-None arm (ambiguous).

    Args:
        model_class: The Pydantic model class to inspect.
        target_type: The type to search for.
        suffix: Appended to each yielded path when a match is found (e.g. ".service_id").
        _prefix: Internal use — accumulated dotted path prefix for nested fields.
    """
    for field in _iter_model_fields(model_class, _prefix):
        if field.annotation is target_type:
            yield f"{field.path}{suffix}"
        elif isinstance(field.annotation, type) and issubclass(
            field.annotation, BaseModel
        ):
            yield from iter_field_paths_by_type(
                field.annotation, target_type, suffix, f"{field.path}."
            )


def iter_field_paths_by_metadata(
    model_class: type[BaseModel],
    metadata_type: type[T],
    _prefix: str = "",
) -> Iterator[FieldWithMetadata[T]]:
    """Recursively yield FieldWithMetadata(path, marker) for fields annotated with
    metadata_type.

    Unwraps Optional[X] / X | None and list[X] before deciding whether to recurse.
    Recurses into nested Pydantic models and single-type list fields. Also checks
    computed fields at each level via their return type annotation.

    Args:
        model_class: The Pydantic model class to inspect.
        metadata_type: The metadata annotation type to search for.
        _prefix: Internal use — accumulated dotted path prefix for nested fields.
    """
    for field in _iter_model_fields(model_class, _prefix):
        marker = next(
            (m for m in field.field_info.metadata if isinstance(m, metadata_type)), None
        )
        if marker is not None:
            yield FieldWithMetadata(path=field.path, marker=marker)
        else:
            inner = field.annotation
            if get_origin(field.annotation) is list:
                args = get_args(field.annotation)
                inner = args[0] if args else field.annotation
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                yield from iter_field_paths_by_metadata(
                    inner, metadata_type, f"{field.path}."
                )

    for field_name, computed_info in model_class.model_computed_fields.items():
        fget = computed_info.wrapped_property.fget
        if fget is None:
            continue
        hints = get_type_hints(fget, include_extras=True)
        return_hint = hints.get("return")
        if return_hint is None or get_origin(return_hint) is not Annotated:
            continue
        marker = next(
            (m for m in get_args(return_hint)[1:] if isinstance(m, metadata_type)),
            None,
        )
        if marker is not None:
            yield FieldWithMetadata(path=f"{_prefix}{field_name}", marker=marker)
