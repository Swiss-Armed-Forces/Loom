from dataclasses import dataclass
from typing import Any, NamedTuple


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
