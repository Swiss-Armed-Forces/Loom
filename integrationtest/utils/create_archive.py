import requests
from api.routers.archives import ArchiveCreatedResponse, ArchiveRequest
from common.services.query_builder import QueryParameters

from utils.consts import ARCHIVE_ENDPOINT, REQUEST_TIMEOUT


def create_archive(query: QueryParameters) -> ArchiveCreatedResponse:
    response = requests.post(
        f"{ARCHIVE_ENDPOINT}",
        json=ArchiveRequest(query=query).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return ArchiveCreatedResponse.model_validate(response.json())
