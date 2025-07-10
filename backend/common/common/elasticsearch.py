"""Initialize elasticsearch connection and indices."""

import logging

from elasticsearch import Elasticsearch, RequestError
from elasticsearch.dsl.connections import create_connection
from elasticsearch.dsl.exceptions import ElasticsearchDslException

from common.messages.pubsub_service import PubSubService
from common.models.es_repository import ES_REPOSITORY_TYPES
from common.services.query_builder import QueryBuilder
from common.settings import settings

logger = logging.getLogger(__name__)


def init_elasticsearch(
    query_builder: QueryBuilder,
    pubsub_service: PubSubService,
    init_repositories: bool,
) -> Elasticsearch:
    """Initialize elasticsearch connection and indices."""
    elasticsearch = create_connection(
        hosts=[
            # pylint: disable=no-member
            f"{settings.es_host.scheme}://{settings.es_host.host}:{settings.es_host.port}"
        ],
        request_timeout=settings.es_timeout,
    )
    if init_repositories:
        for repository_type in ES_REPOSITORY_TYPES:
            repository = repository_type(
                query_builder=query_builder, pubsub_service=pubsub_service
            )
            try:
                repository.init()

            except (RequestError, ElasticsearchDslException):
                # We failed creating the index: reindex
                logger.warning(
                    "Could not init repository: %s, start reindexing", repository_type
                )
                repository.reindex()
    return elasticsearch
