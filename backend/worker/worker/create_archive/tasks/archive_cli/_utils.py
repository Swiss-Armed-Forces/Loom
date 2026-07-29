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


_INDEX_RE = re.compile(r"\[(\d+)\]")


def _collapse_field_ranges(fields: list[str]) -> list[str]:
    """Collapse repeated array indices in field paths to [lo..hi] ranges.

    Converts e.g. ``tasks[0].name``, ``tasks[1].name`` → ``tasks[0..1].name``. Preserves
    insertion order of unique schema paths. Single-element arrays are left as ``[N]``
    without a range.
    """
    dim_sets: dict[str, list[set[int]]] = {}
    order: list[str] = []

    for path in fields:
        key = _INDEX_RE.sub("[*]", path)
        indices = [int(m.group(1)) for m in _INDEX_RE.finditer(path)]
        if key not in dim_sets:
            dim_sets[key] = [set() for _ in indices]
            order.append(key)
        for i, idx in enumerate(indices):
            dim_sets[key][i].add(idx)

    result = []
    for key in order:
        out = key
        for dim_set in dim_sets[key]:
            lo, hi = min(dim_set), max(dim_set)
            replacement = f"[{lo}..{hi}]" if lo != hi else f"[{lo}]"
            out = out.replace("[*]", replacement, 1)
        result.append(out)
    return result


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
