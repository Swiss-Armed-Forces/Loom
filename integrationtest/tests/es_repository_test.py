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
from common.task_object.root_task_information_repository import (
    RootTaskInformation,
    RootTaskInformationRepository,
)

ES_REPOSITORY_MINIMAL_OBJECTS: dict[type[BaseEsRepository], RepositoryObject] = {
    FileRepository: File(
        storage_data=LazyBytes(service_id="000000000000000000000000"),
        full_name=FilePurePath("test/test.txt"),
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
    RootTaskInformationRepository: RootTaskInformation(
        root_task_id=uuid4(),
        object_id=uuid4(),
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
    backup_index_name = repository.reinit()
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
    assert repository.get_by_id(_object.id_) is None


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
def test_get_by_id_nonexistent_returns_none(repository_type: type[BaseEsRepository]):
    """Test that get_by_id returns None for non-existent objects."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    nonexistent_id = uuid4()
    result = repository.get_by_id(nonexistent_id)
    assert result is None


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_count(repository_type: type[BaseEsRepository]):
    """Test that count() reflects the number of saved documents."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    count_before = repository.count()
    repository.save(_object)
    assert repository.count() == count_before + 1

    # Cleanup
    repository.delete_by_id(_object.id_)


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_flush(repository_type: type[BaseEsRepository]):
    """Test that flush() removes all documents from the index."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )

    _object = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type].model_copy(deep=True)
    repository.save(_object)
    repository.flush()
    assert repository.count() == 0


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


# Must exceed _ID_SCAN_PAGE_SIZE (defined in es_repository.py) to span
# multiple scan pages.
_PAGINATION_BUG_DOC_COUNT = 11001


@pytest.mark.parametrize(
    "repository_type",
    ES_REPOSITORY_TYPES,
)
def test_get_id_generator_by_query_returns_all_ids_across_multiple_scan_pages(
    repository_type: type[BaseEsRepository],
):
    """Regression test: get_id_generator_by_query must return every indexed document
    when the result spans more than one scan page."""
    repository = repository_type(
        query_builder=get_query_builder(), pubsub_service=get_pubsub_service()
    )
    template = ES_REPOSITORY_MINIMAL_OBJECTS[repository_type]

    objects = []
    for _ in range(_PAGINATION_BUG_DOC_COUNT):
        obj = template.model_copy(deep=True)
        obj.id_ = uuid4()
        obj.sort_unique = uuid4()
        objects.append(obj)
    saved_ids = {obj.id_ for obj in objects}

    bulk_results = list(repository.bulk_save(objects))
    failed = [r for r in bulk_results if not r.success]
    assert not failed, f"{len(failed)} bulk save(s) failed: {failed[:3]}"

    returned_ids = {
        obj.id_ for obj in repository.get_id_generator_by_query(query=QueryParameters())
    }

    assert returned_ids == saved_ids
