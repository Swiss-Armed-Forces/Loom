import logging

from common.dependencies import get_pubsub_service, get_query_builder
from common.messages.pubsub_service import PubSubService
from common.models.es_repository import ES_REPOSITORY_TYPES
from common.services.query_builder import QueryBuilder
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

_query_builder = Depends(get_query_builder)
_pubsub_service = Depends(get_pubsub_service)


class ReinitResult(BaseModel):
    index: str
    backup_index: str


class ReinitAllResult(BaseModel):
    results: list[ReinitResult]


@router.post("")
def reinit_all_elasticsearch(
    query_builder: QueryBuilder = _query_builder,
    pubsub_service: PubSubService = _pubsub_service,
) -> ReinitAllResult:
    results = []
    for repo_type in ES_REPOSITORY_TYPES:
        repo = repo_type(query_builder=query_builder, pubsub_service=pubsub_service)
        logger.info("reinit: %s", repo_type.__name__)
        backup_index = repo.reinit()
        results.append(ReinitResult(index=repo.index_name, backup_index=backup_index))
    return ReinitAllResult(results=results)


@router.post("/{index}")
def reinit_elasticsearch_index(
    index: str,
    query_builder: QueryBuilder = _query_builder,
    pubsub_service: PubSubService = _pubsub_service,
) -> ReinitResult:
    for repo_type in ES_REPOSITORY_TYPES:
        repo = repo_type(query_builder=query_builder, pubsub_service=pubsub_service)
        if repo.index_name == index:
            logger.info("reinit: %s", repo_type.__name__)
            backup_index = repo.reinit()
            return ReinitResult(index=repo.index_name, backup_index=backup_index)
    raise HTTPException(
        status_code=404, detail=f"No repository found for index {index!r}"
    )
