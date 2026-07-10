import re
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

_CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def _sanitize(s: str) -> str:
    """Replace terminal control characters with the Unicode replacement character."""
    return _CTRL_CHAR_RE.sub("\ufffd", s)


def _vpath(name: str) -> str:
    """Strip leading slashes for virtual-path comparisons."""
    return name.lstrip("/")


def resolve_cwd(current: str, target: str) -> str:
    """Resolve a cd target against current cwd, normalising '..' components.

    Returns the new cwd as a bare string (no leading/trailing slash).
    """
    if target.startswith("/"):
        parts: list[str] = [p for p in target.split("/") if p]
    else:
        parts = [p for p in current.split("/") if p] + [
            p for p in target.split("/") if p
        ]

    result: list[str] = []
    for part in parts:
        if part == "..":
            if result:
                result.pop()
        elif part != ".":
            result.append(part)

    return "/".join(result)


def format_path(path: Path) -> str:
    path = path.resolve()

    try:
        return str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


class _FieldValue(NamedTuple):
    key_path: str
    value: str


def _iter_values(data: object, prefix: str = "") -> Iterator[_FieldValue]:
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{prefix}.{k}" if prefix else k
            yield from _iter_values(v, path)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            yield from _iter_values(v, f"{prefix}[{i}]")
    elif data is not None:
        yield _FieldValue(key_path=prefix, value=str(data))
