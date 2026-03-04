from __future__ import annotations

from common.file.file_repository import FilePurePath
from pydantic import BaseModel


class TreeNodeModel(BaseModel):
    """Counts of children per path in the tree."""

    full_path: FilePurePath
    file_count: int
