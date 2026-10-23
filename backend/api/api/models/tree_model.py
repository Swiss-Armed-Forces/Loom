from __future__ import annotations

from common.file.file_repository import FilePurePath, MimeTypeGroup
from pydantic import BaseModel


class GetFilesTreeResponse(BaseModel):
    nodes: list["TreeNodeModel"]
    next_page_cursor: str | None = None
    root_stats: "TreeNodeModel | None" = None
    total_count: int | None = None
    count_relation: str | None = None


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
        direct_children_count: Number of direct-child nodes (files and
            immediate sub-directories) under this node, not counting deeper
            descendants.
        mime_type: MIME type of the file at this node, tika's detection
            preferred over magic's. Set for leaf nodes only; a directory has
            no type of its own.
        mime_type_group: MIME group of the file at this node, resolved the
            same way. Set for leaf nodes only.
        recursion_depth: How many containers this file was extracted out of,
            0 for a file that came straight from the data source. Reported by
            /search_by_filename only, whose results are bare leaves with no
            tree around them; the tree itself derives nesting from its shape.
    """

    full_path: FilePurePath
    file_count: int
    file_id: str | None = None
    unseen_count: int = 0
    is_unseen: bool = False
    flagged_count: int = 0
    is_flagged: bool = False
    direct_children_count: int = 0
    mime_type: str | None = None
    mime_type_group: MimeTypeGroup | None = None
    recursion_depth: int = 0


class TreeDepthLimitsModel(BaseModel):
    """How deep the folder tree for a query goes, on each of its two axes.

    The folder view's depth controls offer a range rather than a fixed scale,
    because what is worth hiding depends on the indexed data: a flat corpus has
    no fourth path level, and one without attachments has nothing nested inside
    a file.

    Attributes:
        max_path_depth: Deepest node in path segments below the virtual root,
            so the root's own children sit at 1.
        max_extraction_depth: How many containers the most deeply extracted file
            in the result set came out of. 0 when nothing was extracted.
    """

    max_path_depth: int
    max_extraction_depth: int
