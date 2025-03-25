"""Tree model."""

from __future__ import annotations

from pathlib import PurePath

from pydantic import BaseModel


class TreeNodeModel(BaseModel):
    """Counts of children per path in the tree."""

    full_path: PurePath
    file_count: int
