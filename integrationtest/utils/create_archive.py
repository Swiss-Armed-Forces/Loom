import requests
from api.models.query_model import QueryModel
from api.routers.archives import ArchiveCreatedResponse, ArchiveRequest

from utils.consts import ARCHIVE_ENDPOINT, REQUEST_TIMEOUT


def create_archive(query: QueryModel) -> ArchiveCreatedResponse:
    response = requests.post(
        f"{ARCHIVE_ENDPOINT}",
        json=ArchiveRequest(query=query).model_dump(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return ArchiveCreatedResponse(**response.json())
