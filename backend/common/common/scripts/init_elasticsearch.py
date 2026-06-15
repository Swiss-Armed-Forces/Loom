"""Elasticsearch index initialization script.

Run as: python -m common.scripts.init_elasticsearch

Intended to be run as a Kubernetes Job (Helm post-install/post-upgrade hook) before the
API starts. By default, runs init() on each repository (creates indexes if missing,
updates compatible mappings). When settings.es_recreate_schema is true
(ES_RECREATE_SCHEMA env var), runs reindex() instead, which backs up, recreates and
migrates all data.
"""

import logging

from common.dependencies import get_pubsub_service, get_query_builder, init
from common.models.es_repository import ES_REPOSITORY_TYPES
from common.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init()
query_builder = get_query_builder()
pubsub_service = get_pubsub_service()

_mode = "reindex" if settings.es_recreate_schema else "init"
logger.info("Starting Elasticsearch index initialization (mode: %s)", _mode)

for repository_type in ES_REPOSITORY_TYPES:
    repository = repository_type(
        query_builder=query_builder, pubsub_service=pubsub_service
    )
    logger.info("%s: %s", _mode, repository_type.__name__)
    if settings.es_recreate_schema:
        repository.reindex()
    else:
        repository.init()

logger.info("Elasticsearch index initialization complete")
