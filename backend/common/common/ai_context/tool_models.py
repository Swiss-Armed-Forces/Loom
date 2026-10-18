"""Shared result types for AI tool calls."""

from typing import NewType, Self
from uuid import UUID

from pydantic import BaseModel, Field

from common.models.cursor_pagination import SearchAfterCursor

CursorHandle = NewType("CursorHandle", str)
"""Stands in for a cursor in the agent's context.

A handle is a name, not a serialised cursor: the agent reads it out of a tool result and
passes it back on the next call, so it has to be a scalar it can echo.  The cursor it
names stays in the run's own state, which is what keeps the point-in-time id out of the
context the agent pays for.
"""


class ToolSource(BaseModel):
    """A file referenced by a tool call, with an optional citation text snippet."""

    file_id: UUID
    text: str = ""


class ToolResult(BaseModel):
    """Base for all tool results."""


class PaginatedToolResult(ToolResult):
    """Base for the paginated results the worker produces.

    Carries the cursor itself, which never leaves the backend: the API swaps it for a
    handle before the result reaches the agent.

    Cursors are tool-specific and query-specific — each one records the search that
    minted it and a digest of the arguments that defined the result set — so one that
    reaches the wrong search is rejected rather than silently paging unrelated results.
    """

    has_more: bool = False
    next_cursor: SearchAfterCursor | None = None


class PaginatedAgentResult(ToolResult):
    """Base for the paginated results the agent sees, with a handle for the cursor."""

    has_more: bool = False
    next_cursor: CursorHandle | None = None

    @classmethod
    def from_tool_result(
        cls, result: PaginatedToolResult, handle: CursorHandle | None
    ) -> Self:
        """Retype a worker result for the agent, the cursor replaced by its handle."""
        return cls(**result.model_dump(exclude={"next_cursor"}), next_cursor=handle)


class QuerySuggestion(BaseModel):
    query: str
    matching_docs: int
    max_score: float | None = None
    avg_score: float | None = None


class SuggestQueriesResult(ToolResult):
    candidates: list[QuerySuggestion]


class ExecuteQueryResultFile(BaseModel):
    file_id: str
    text: str
    score: float | None


class _ExecuteQueryFields(BaseModel):
    """Payload of an execute_query page, shared by both ends of the handle swap."""

    files: list[ExecuteQueryResultFile]
    total_count: int | None = None
    count_relation: str | None = None


class ExecuteQueryResult(_ExecuteQueryFields, PaginatedToolResult):
    """What the execute_query task returns."""


class ExecuteQueryAgentResult(_ExecuteQueryFields, PaginatedAgentResult):
    """What the execute_query tool returns to the agent."""


class FileFieldInfo(BaseModel):
    name: str
    description: str


class GetFileResult(ToolResult):
    file_id: str
    full_path: str
    available_fields: list[FileFieldInfo]


class GetFileFieldResult(ToolResult):
    file_id: str
    field: str
    value: str


class RagChunk(BaseModel):
    """A document chunk retrieved and used by the RAG pipeline."""

    file_id: UUID
    text: str


class RagSearchResult(ToolResult):
    answer: str
    chunks: list[RagChunk] = Field(default_factory=list)


class SummarizeFileResult(ToolResult):
    file_id: str
    summary: str


class TranslateFileResult(ToolResult):
    file_id: str
    source_language: str
    translation: str


class DescribeImageResult(ToolResult):
    file_id: str
    description: str


class FolderEntry(BaseModel):
    full_path: str
    is_file: bool
    file_count: int
    file_id: str | None = None


class _ListFolderContentsFields(BaseModel):
    """Payload of a list_folder_contents page, shared by both ends of the handle
    swap."""

    folder_path: str
    entries: list[FolderEntry]


class ListFolderContentsResult(_ListFolderContentsFields, PaginatedToolResult):
    """What the list_folder_contents task returns."""


class ListFolderContentsAgentResult(_ListFolderContentsFields, PaginatedAgentResult):
    """What the list_folder_contents tool returns to the agent."""


class FilenameSearchEntry(BaseModel):
    full_path: str
    file_id: str


class _SearchByFilenameFields(BaseModel):
    """Payload of a search_by_filename page, shared by both ends of the handle swap."""

    query: str
    # Echoed back so the agent can repeat it unchanged on the next page: the cursor is
    # bound to it, and a page asked for with a different one is rejected.
    search_string: str = "*"
    files: list[FilenameSearchEntry]
    total_count: int | None = None
    count_relation: str | None = None


class SearchByFilenameResult(_SearchByFilenameFields, PaginatedToolResult):
    """What the search_by_filename task returns."""


class SearchByFilenameAgentResult(_SearchByFilenameFields, PaginatedAgentResult):
    """What the search_by_filename tool returns to the agent."""
