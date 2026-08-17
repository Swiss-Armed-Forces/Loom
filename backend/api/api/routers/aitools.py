from uuid import UUID, uuid4

from common.ai_context.tool_models import (
    DescribeImageResult,
    ExecuteQueryResult,
    GetFileFieldResult,
    GetFileResult,
    ListFolderContentsResult,
    RagSearchResult,
    SearchByFilenameResult,
    SuggestQueriesResult,
    SummarizeFileResult,
    TranslateFileResult,
)
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.dependencies import get_task_call_service
from api.patch_openapi_schema import patch_openapi_schema_for_app
from api.services.task_call_service import TaskCallService

router = APIRouter()

default_task_call_service = Depends(get_task_call_service)


@router.get("/openapi.json", include_in_schema=False)
def openapi_json() -> JSONResponse:
    # Create a mini-app just for this module
    api = FastAPI(title="AI Tools API")
    api.include_router(router)
    # Call the function to patch the openapi schema
    patch_openapi_schema_for_app(api)
    return JSONResponse(content=api.openapi())


@router.get("/files/suggest-queries")
def suggest_queries(
    query_description: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> SuggestQueriesResult:
    """Generate ranked Lucene query candidates from a natural language description.

    Translates the description into multiple Lucene query strings in parallel,
    counts Elasticsearch matches for each, deduplicates, and returns them sorted
    by match count descending.

    Parameters:
    -----------
    query_description : str
        A natural language phrase describing what to search for.

    Returns:
    --------
    SuggestQueriesResult
        - candidates (list[QuerySuggestion]):
            - query (str): Lucene query string.
            - matching_docs (int): Number of matching documents.
    """
    return task_call_service.call_suggest_queries_tool(uuid4(), query_description)


@router.get("/files/execute-query")
def execute_query(
    query_string: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> ExecuteQueryResult:
    """Execute a Lucene query string and return matching files with content snippets.

    Parameters:
    -----------
    query_string : str
        A valid Elasticsearch Lucene query string.

    Returns:
    --------
    ExecuteQueryResult
        - files (list[ExecuteQueryResultFile]):
            - file_id (str): Unique ID of the matching file.
            - text (str): Relevant content snippet from the file.
            - score (float | None): Relevance score from Elasticsearch.
    """
    return task_call_service.call_execute_query_tool(uuid4(), query_string)


@router.get("/files/search-by-filename")
def search_by_filename(
    filename: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> SearchByFilenameResult:
    """Search for files whose name contains the given substring.

    Parameters:
    -----------
    filename : str
        Substring to match against filenames (case-insensitive).

    Returns:
    --------
    SearchByFilenameResult
        - query (str): The search substring used.
        - files (list[FilenameSearchEntry]):
            - full_path (str): Full path of the matching file.
            - file_id (str): Unique ID of the matching file.
    """
    return task_call_service.call_search_by_filename_tool(uuid4(), filename)


@router.get("/files/{file_id}")
def get_file_by_id(
    file_id: UUID,
    task_call_service: TaskCallService = default_task_call_service,
) -> GetFileResult:
    """Retrieve content and metadata of a file by its unique identifier.

    This endpoint fetches a file's name, extracted content, and optional summary
    using its UUID. If the file is not found, a 404 error is returned.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the file. Must be a valid UUID.

    Returns:
    --------
    GetFileResult
        A model containing the file's content and metadata. Fields include:

        - file_id (str): Unique ID of the file.
        - name (str): Short or display name for the file.
        - content (str): Extracted text content (truncated for LLM consumption).
        - summary (str | None): Optional summary text.

    Raises:
    -------
    HTTPException (status_code=404)
        Raised if no file with the given ID exists in the repository.
    """
    try:
        return task_call_service.call_get_file_tool(uuid4(), str(file_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc


@router.get("/rag")
def rag_search(
    query: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> RagSearchResult:
    """Answer a natural language question using the full RAG pipeline.

    Retrieves relevant document chunks via vector similarity search (with HyDE
    and reranking) and synthesizes a grounded answer from the indexed corpus.

    Parameters:
    -----------
    query : str
        A natural language question to answer.
        Example: "What are the key findings from the Q3 report?"

    Returns:
    --------
    RagSearchResult
        - answer (str): The synthesized answer grounded in retrieved documents.

    Example Request:
    ----------------
        GET /rag?query=What are the contract renewal terms?

    Example Response:
    -----------------
    {
        "answer": "The contract renewal terms specify a 30-day notice period..."
    }

    Raises:
    -------
    HTTPException
        May be raised if the LLM or RAG backend fails to respond.
    """
    return task_call_service.call_rag_search_tool(uuid4(), query)


@router.get("/files/{file_id}/fields/{field}")
def get_file_field(
    file_id: UUID,
    field: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> GetFileFieldResult:
    """Retrieve the value of a specific field for a file.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the file.
    field : str
        Name of the field to retrieve (e.g. "content", "summary").

    Returns:
    --------
    GetFileFieldResult
        - file_id (str): Unique ID of the file.
        - field (str): Name of the retrieved field.
        - value (str): The field's value.
    """
    try:
        return task_call_service.call_get_file_field_tool(uuid4(), str(file_id), field)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc


@router.get("/files/{file_id}/summary")
def summarize_file(
    file_id: UUID,
    task_call_service: TaskCallService = default_task_call_service,
) -> SummarizeFileResult:
    """Generate an AI summary for a file.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the file to summarize.

    Returns:
    --------
    SummarizeFileResult
        - file_id (str): Unique ID of the file.
        - summary (str): The generated summary text.
    """
    try:
        return task_call_service.call_summarize_file_tool(uuid4(), str(file_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc


@router.get("/files/{file_id}/translate")
def translate_file(
    file_id: UUID,
    source_language: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> TranslateFileResult:
    """Translate a file's content from the given source language.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the file to translate.
    source_language : str
        BCP 47 / ISO 639-1 language code of the document's current language
        (e.g. "de", "fr", "en").

    Returns:
    --------
    TranslateFileResult
        - file_id (str): Unique ID of the file.
        - source_language (str): The source language code.
        - translation (str): The translated text.
    """
    try:
        return task_call_service.call_translate_file_tool(
            uuid4(), str(file_id), source_language
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc


@router.get("/files/{file_id}/describe-image")
def describe_image(
    file_id: UUID,
    task_call_service: TaskCallService = default_task_call_service,
) -> DescribeImageResult:
    """Generate an AI description of an image file.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the image file to describe.

    Returns:
    --------
    DescribeImageResult
        - file_id (str): Unique ID of the file.
        - description (str): The generated image description.
    """
    try:
        return task_call_service.call_describe_image_tool(uuid4(), str(file_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc


@router.get("/folders")
def list_folder_contents(
    folder_path: str,
    task_call_service: TaskCallService = default_task_call_service,
) -> ListFolderContentsResult:
    """List the direct children (subfolders and files) of a folder path.

    Parameters:
    -----------
    folder_path : str
        Absolute folder path to list, e.g. "/" or "//source/subfolder".

    Returns:
    --------
    ListFolderContentsResult
        - folder_path (str): The listed folder path.
        - entries (list[FolderEntry]):
            - full_path (str): Full path of the entry.
            - is_file (bool): Whether the entry is a file.
            - file_count (int): Number of files in the folder (0 for files).
            - file_id (str | None): File UUID if the entry is a file.
    """
    return task_call_service.call_list_folder_contents_tool(uuid4(), folder_path)
