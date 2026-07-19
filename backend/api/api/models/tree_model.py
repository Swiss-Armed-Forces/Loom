from __future__ import annotations

from common.file.file_repository import FilePurePath
from pydantic import BaseModel


class GetFilesTreeResponse(BaseModel):
    nodes: list["TreeNodeModel"]
    next_page_cursor: str | None = None
    root_stats: "TreeNodeModel | None" = None


class TreeNodeModel(BaseModel):
    """A node in the file tree returned by the /tree endpoint.

    Attributes:
        full_path: Absolute path of the node (directory or file).
        file_count: Total number of descendant files under this path.
        file_id: Set only when the node is a leaf file (not a directory).
        unseen_count: Number of unseen descendant files, excluding the node
            itself when is_unseen is True.
        is_unseen: Whether the file at this node is unseen (leaf nodes only).
        flagged_count: Number of flagged descendant files, excluding the node
            itself when is_flagged is True.
        is_flagged: Whether the file at this node is flagged (leaf nodes only).
    """

    full_path: FilePurePath
    file_count: int
    file_id: str | None = None
    unseen_count: int = 0
    is_unseen: bool = False
    flagged_count: int = 0
    is_flagged: bool = False
