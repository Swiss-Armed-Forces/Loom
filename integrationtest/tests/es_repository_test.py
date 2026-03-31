from uuid import uuid4

import pytest
from common.ai_context.ai_context_repository import AiContext, AiContextRepository
from common.archive.archive_repository import Archive, ArchiveRepository
from common.dependencies import get_elasticsearch, get_pubsub_service, get_query_builder
from common.file.file_repository import File, FilePurePath, FileRepository
from common.models.base_repository import RepositoryObject
from common.models.es_repository import ES_REPOSITORY_TYPES, BaseEsRepository
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryParameters
from elasticsearch import NotFoundError

ES_REPOSITORY_MINIMAL_OBJECTS: dict[type[BaseEsRepository], RepositoryObject] = {
    FileRepository: File(
        storage_data=LazyBytes(service_id="000000000000000000000000"),
        full_name=FilePurePath("/test/test.txt"),
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

    # Create and save a minimal file:
    # Use model_copy to avoid test pollution via shared mutable state
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)

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


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_update_partial_fields(repository_type: type[BaseEsRepository]):
    """Test that update() only updates specified fields."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create and save a minimal object:
    # Use model_copy to avoid test pollution via shared mutable state
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    _object.hidden = False
    repository.save(_object)

    # Modify a field and update with include
    _object.hidden = True

    repository.update(_object, include={"hidden"})

    # Verify the update worked
    updated_object = repository.get_by_id(_object.id_)
    assert updated_object.hidden is True

    # Cleanup
    repository.delete_by_id(_object.id_)


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_is_fresh_returns_true_for_unchanged_document(
    repository_type: type[BaseEsRepository],
):
    """Test that is_fresh returns True for a freshly saved document."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create and save a minimal object
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    repository.save(_object)

    # Immediately check freshness - should be True
    assert repository.is_fresh(_object) is True


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_is_fresh_returns_false_after_external_update(
    repository_type: type[BaseEsRepository],
):
    """Test that is_fresh returns False after the document is updated externally."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create and save a minimal object
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    repository.save(_object)

    # Keep a cached copy of the object
    cached_object = _object.model_copy(deep=True)

    # Update the object in ES (this changes the version)
    _object.hidden = not _object.hidden
    repository.update(_object, include={"hidden"})

    # Check freshness of the cached copy - should be False
    assert repository.is_fresh(cached_object) is False


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_is_fresh_returns_false_for_deleted_document(
    repository_type: type[BaseEsRepository],
):
    """Test that is_fresh returns False for a deleted document."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create and save a minimal object
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    repository.save(_object)

    # Delete the object
    repository.delete_by_id(_object.id_)

    # Check freshness - should be False since document no longer exists
    assert repository.is_fresh(_object) is False


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_is_fresh_returns_false_for_object_without_version(
    repository_type: type[BaseEsRepository],
):
    """Test that is_fresh returns False for an object without version metadata."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    # Create an object WITHOUT saving (no version metadata)
    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)

    # Verify the object has no version
    assert _object.es_meta.version is None

    # Check freshness - should be False since there's no version to compare
    assert repository.is_fresh(_object) is False
