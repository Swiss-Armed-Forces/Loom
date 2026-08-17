"""Shared result types for AI tool calls."""

from uuid import UUID

from pydantic import BaseModel, Field


class ToolSource(BaseModel):
    """A file referenced by a tool call, with an optional citation text snippet."""

    file_id: UUID
    text: str = ""


class ToolResult(BaseModel):
    """Base for all tool results.

    Tools populate sources with files they used.
    """

    sources: list[ToolSource] = Field(default_factory=list)


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


class ExecuteQueryResult(ToolResult):
    files: list[ExecuteQueryResultFile]


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


class RagSearchResult(ToolResult):
    answer: str


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


class ListFolderContentsResult(ToolResult):
    folder_path: str
    entries: list[FolderEntry]


class FilenameSearchEntry(BaseModel):
    full_path: str
    file_id: str


class SearchByFilenameResult(ToolResult):
    query: str
    files: list[FilenameSearchEntry]
