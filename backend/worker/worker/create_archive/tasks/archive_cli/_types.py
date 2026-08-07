from dataclasses import dataclass
from typing import Any, NamedTuple

# Ordered sequence of sanitized path components derived from a virtual path.
RelPathParts = tuple[str, ...]


@dataclass
class IndexEntry:
    name: str
    storage_id: str
    meta: dict[str, Any]


class ServiceIdResult(NamedTuple):
    name: str
    role: str  # "file", "thumbnail", or "rendered:<name>"


class StorageEntry(NamedTuple):
    storage_id: str
    role: str  # "file", "thumbnail", or "rendered:<name>"
