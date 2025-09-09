import logging
from uuid import UUID

from common.dependencies import get_file_repository, get_ollama_tool_client
from common.file.file_repository import FileRepository
from common.models.es_repository import PaginationParameters
from common.services.query_builder import QueryParameters
from common.settings import settings
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from ollama import Client, Options
from pydantic import BaseModel

from api.patch_openapi_schema import patch_openapi_schema_for_app
from api.routers.files import GetFileResponse

router = APIRouter()

logger = logging.getLogger(__name__)

default_file_repository = Depends(get_file_repository)
default_ollama_tool_client = Depends(get_ollama_tool_client)

FILES_SEARCH_MAX_RESULTS = 10


@router.get("/openapi.json", include_in_schema=False)
def openapi_json():
    # Create a mini-app just for this module
    api = FastAPI(title="AI Tools API")
    api.include_router(router)
    # Call the function to patch the openapi schema
    patch_openapi_schema_for_app(api)
    return api.openapi_schema


class GetSearchResponseFile(BaseModel):
    file_id: UUID
    highlight: dict[str, list[str]] | None
    score: float | None


class GetSearchResponse(BaseModel):
    search_string: str
    files: list[GetSearchResponseFile]


@router.get("/files/search")
def search(
    query_description: str,
    ollama_tool_client: Client = default_ollama_tool_client,
    file_repository: FileRepository = default_file_repository,
) -> GetSearchResponse:
    """Perform a smart full-text search over files using natural language input.

    This endpoint enables users to describe their search intent using plain
    English. A language model translates the input into a Lucene query string,
    which is executed against an Elasticsearch index to return relevant files.

    The translation is flexible and expressive, supporting rich query features
    such as boolean logic, wildcards, fuzzy matching, ranges, and proximity.

    Parameters:
    -----------
    query_description : str
        A natural language phrase describing what to search for.
        Example: "Meeting notes with roadmap updates from 2024"

    ollama_tool_client : Client, optional
        A client that interacts with a local LLM to generate a Lucene query.
        Defaults to `default_ollama_tool_client`.

    file_repository : FileRepository, optional
        An interface for searching and retrieving file metadata.
        Defaults to `default_file_repository`.

    Returns:
    --------
    GetSearchResponse
        A structured response with:
        - search_string (str): The Lucene query generated from the input.
        - files (list[GetSearchResponseFile]):
            - file_id (UUID): Unique ID of the matching file.
            - highlight (dict[str, list[str]] | None):
              Highlighted content snippets.
            - score (float | None): Relevance score from Elasticsearch.

    How It Works:
    -------------
    1. The LLM receives a prompt that asks it to convert the user query into a
       Lucene-compatible search string.

    2. The generated string is used to search for matching files via the
       Elasticsearch backend.

    3. Matching files are returned with score and optional highlights.

    4. The raw search string is included in the response for debugging or reuse.

    Example Request:
    ----------------
        GET /files/search?query_description=contracts expiring before 2025

    Example Response:
    -----------------
    {
        "search_string": "contract AND (expire OR expiration) AND date:[* TO 2025]",
        "files": [
            {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "highlight": {
                    "content": [
                        "The contract is set to <em>expire</em> on January 15, 2024."
                    ]
                },
                "score": 4.75
            }
        ]
    }

    Notes:
    ------
    - The LLM prompt encourages free-text and fuzzy matching strategies.
    - Field-level filters are discouraged unless semantically necessary.
    - Results are limited to `FILES_SEARCH_MAX_RESULTS` items.
    - This endpoint is ideal for flexible search experiences and file discovery.

    Raises:
    -------
    HTTPException
        May be raised if the LLM or search backend fails to respond.
    """

    prompt = f"""
TASK: Translate the QUERY_DESCRIPTION to an Elasticsearch QUERY_STRING.
--------------------
HINT: Try to be smart and use Lucene Query features
(AND, OR, wildcards, fuzzy, proximity, Regular expression, ranges, etc.)
to make the query flexible and a generic fit for the QUERY_DESCRIPTION.
HINT: Favour free text search ("value", "value*", "*value*", etc. ) over
searches in fields ("field:value").
--------------------
IMPORTANT: Use Lucene Query syntax for the QUERY_STRING.
IMPORTANT: Do not quote the QUERY_STRING.
IMPORTANT: Only answer with the QUERY_STRING and nothing else!
--------------------
QUERY_DESCRIPTION: {query_description}
--------------------
QUERY_STRING:"""

    response = ollama_tool_client.generate(
        model=settings.llm_model_tool,
        prompt=prompt,
        system=settings.llm_system_prompt,
        options=Options(
            temperature=settings.llm_temperature,
        ),
        think=settings.llm_think,
    )
    search_string = response.response

    logger.info("Getting files with search string: '%s'", search_string)
    query = QueryParameters(
        query_id=file_repository.open_point_in_time(),
        search_string=search_string,
    )
    result = file_repository.get_by_query(
        query=query,
        pagination_params=PaginationParameters(page_size=FILES_SEARCH_MAX_RESULTS),
    )

    return GetSearchResponse(
        search_string=search_string,
        files=[
            GetSearchResponseFile(
                file_id=file.id_,
                highlight=file.es_meta.highlight,
                score=file.es_meta.score,
            )
            for file in result.objs
        ],
    )


@router.get("/files/{file_id}")
def get_file_by_id(
    file_id: UUID,
    file_repository: FileRepository = default_file_repository,
) -> GetFileResponse:
    """Retrieve detailed information about a file by its unique identifier.

    This endpoint fetches a file's metadata, extracted content, highlights,
    translations, and an optional summary using its UUID. If the file is not
    found, a 404 error is returned.

    Parameters:
    -----------
    file_id : UUID
        The unique identifier of the file. Must be a valid UUID.

    file_repository : FileRepository, optional
        Repository used to access file data. Defaults to default_file_repository.

    Returns:
    --------
    GetFileResponse
        A model containing the file's processed and raw content, highlights, and
        translations. Fields include:

        - file_id (UUID): Unique ID of the file.
        - highlight (dict[str, list[str]] | None): Highlighted text per category.
        - content (str): Extracted or processed text content.
        - name (str): Short or display name for the file.
        - libretranslate_language_translations (list[GetFileLanguageTranslations]):
          List of language translations.
        - raw (str): Original unprocessed content.
        - summary (str | None): Optional summary text.

    Raises:
    -------
    HTTPException (status_code=404)
        Raised if no file with the given ID exists in the repository.
    """

    file = file_repository.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="file not found")
    return GetFileResponse.from_file(file)
