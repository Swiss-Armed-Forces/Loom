"""Elasticsearch index initialization script.

Run as: python -m common.scripts.init_elasticsearch

Intended to be run as a Kubernetes Job (Helm post-install/post-upgrade hook) before the
API starts. Runs init() on each repository (creates indexes if missing, updates
compatible mappings).
"""

import logging

from common.dependencies import get_pubsub_service, get_query_builder, init
from common.models.es_repository import ES_REPOSITORY_TYPES

logger = logging.getLogger(__name__)

init()
query_builder = get_query_builder()
pubsub_service = get_pubsub_service()

logger.info("Starting Elasticsearch index initialization")

for repository_type in ES_REPOSITORY_TYPES:
    repository = repository_type(
        query_builder=query_builder, pubsub_service=pubsub_service
    )
    logger.info("init: %s", repository_type.__name__)
    repository.init()

logger.info("Elasticsearch index initialization complete")
