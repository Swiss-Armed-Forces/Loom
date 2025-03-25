import pytest
from common.dependencies import get_elasticsearch, get_pubsub_service, get_query_builder
from common.models.es_repository import ES_REPOSITORY_TYPES, BaseEsRepository


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_backup_repositories(repository_type: type[BaseEsRepository]):
    elasticsearch = get_elasticsearch()
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )
    backup_index_name = repository.backup_index()
    assert repository.get_index_health()["status"] == "green"
    assert elasticsearch.cluster.health(index=backup_index_name)["status"] == "green"


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_reindex_repositories(repository_type: type[BaseEsRepository]):
    elasticsearch = get_elasticsearch()
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )
    backup_index_name = repository.reindex()
    assert repository.get_index_health()["status"] == "green"
    assert elasticsearch.cluster.health(index=backup_index_name)["status"] == "green"
