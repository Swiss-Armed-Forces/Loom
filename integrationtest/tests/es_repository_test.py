from pathlib import PurePath
from uuid import uuid4

import pytest
from common.ai_context.ai_context_repository import AiContext, AiContextRepository
from common.archive.archive_repository import Archive, ArchiveRepository
from common.dependencies import get_elasticsearch, get_pubsub_service, get_query_builder
from common.file.file_repository import File, FileRepository
from common.models.base_repository import RepositoryObject
from common.models.es_repository import ES_REPOSITORY_TYPES, BaseEsRepository
from common.services.query_builder import QueryParameters
from elasticsearch import NotFoundError

ES_REPOSITORY_MINIMAL_OBJECTS: dict[type[BaseEsRepository], RepositoryObject] = {
    FileRepository: File(
        storage_id="000000000000000000000000",
        full_name=PurePath("/test/test.txt"),
        source="test-source",
        parent_id=None,
        sha256="abc123",
        size=100,
    ),
    ArchiveRepository: Archive(
        query=QueryParameters(
            query_id="000000000000000000000000",
        ),
    ),
    AiContextRepository: AiContext(
        query=QueryParameters(
            query_id="000000000000000000000000",
        ),
    ),
}


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_open_point_in_time(repository_type: type[BaseEsRepository]):
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )
    query_id1 = repository.open_point_in_time()
    query_id2 = repository.open_point_in_time()
    assert query_id1 != query_id2


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


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_delete_by_id_existing_document(repository_type: type[BaseEsRepository]):
    """Test that delete_by_id removes an existing document."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create and save a minimal file
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type]

    repository.save(_object)

    # Verify it exists
    saved_object = repository.get_by_id(_object.id_)
    assert saved_object is not None

    # Delete it
    result = repository.delete_by_id(_object.id_)
    assert result is True

    # Verify it's gone
    with pytest.raises(NotFoundError):
        repository.get_by_id(_object.id_)


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_delete_by_id_nonexistent_objects(repository_type: type[BaseEsRepository]):
    """Test that delete_by_id returns False for non-existent objects."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Try to delete a non-existent object
    nonexistent_id = uuid4()
    result = repository.delete_by_id(nonexistent_id)
    assert result is False
