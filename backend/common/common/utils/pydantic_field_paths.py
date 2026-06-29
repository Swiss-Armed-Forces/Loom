import types
from collections.abc import Iterator
from typing import Union, get_args, get_origin

from pydantic import BaseModel


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
    for field_name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)
        if origin in (Union, types.UnionType):
            non_none_args = [a for a in get_args(annotation) if a is not types.NoneType]
            annotation = non_none_args[0] if len(non_none_args) == 1 else annotation

        path = f"{_prefix}{field_name}"
        if annotation is target_type:
            yield f"{path}{suffix}"
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            yield from iter_field_paths_by_type(
                annotation, target_type, suffix, f"{path}."
            )
