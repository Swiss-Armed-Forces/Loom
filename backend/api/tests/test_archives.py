from bson import ObjectId
from common.archive.archive_repository import Archive, StoredArchive
from common.dependencies import (
    get_archive_repository,
    get_archive_scheduling_service,
    get_file_storage_service,
)
from common.services.query_builder import QueryParameters

from api.models.archives_model import ArchivesModel
from api.routers.archives import ArchiveCreatedResponse, ArchiveRequest


def test_create_archive_with_emtpy_query_fails(client):
    # query is required -> bad request
    response = client.post("/v1/archive/", json={})
    assert response.status_code == 422


def test_create_archive(
    client,
):
    query = QueryParameters(query_id="0123456789", search_string="*")
    archive_request = ArchiveRequest(query=query)

    archive = Archive(query=query)
    get_archive_scheduling_service().create_archive.return_value = archive

    response = client.post("/v1/archive/", json=archive_request.model_dump())
    response.raise_for_status()
    assert response.status_code == 201
    archive_create_response = ArchiveCreatedResponse.model_validate(response.json())
    assert archive_create_response.archive_id == archive.id_


def test_archive_get_all(client):
    query = QueryParameters(query_id="0123456789", search_string="*")

    archive1 = Archive(query=query)
    archive2 = Archive(query=query)
    get_archive_repository().get_generator_by_query.return_value = [archive1, archive2]
    get_archive_repository().open_point_in_time.return_value = "0123456789"

    response = client.get("/v1/archive/")
    assert response.status_code == 200
    archives = ArchivesModel.model_validate(response.json())
    assert len(archives.hits) == 2
    assert archives.found == 2
    assert archives.total == 2
    assert archives.hits[0].file_id == archive1.id_
    assert archives.hits[1].file_id == archive2.id_


def test_download_archive(client):
    query = QueryParameters(query_id="0123456789", search_string="*")
    content = [b"file content", b"and", b"another", b"chunk"]
    content_encrypted = [b"encrypted file content", b"and", b"another", b"chunk"]
    archive = Archive(
        query=query,
        plain_file=StoredArchive(
            storage_id=str(ObjectId()),
            sha256="",
            size=len(content),
        ),
        encrypted_file=StoredArchive(
            storage_id=str(ObjectId()),
            sha256="",
            size=len(content_encrypted),
        ),
    )
    get_archive_repository().get_by_id.return_value = archive

    # Test encrypted:
    get_file_storage_service().open_download_iterator.return_value = (
        content_chunk for content_chunk in content_encrypted
    )
    response = client.get(f"/v1/archive/{archive.id_}")
    assert response.status_code == 200
    assert response.content == b"".join(content_encrypted)

    # Test not encrypted:
    get_file_storage_service().open_download_iterator.return_value = (
        content_chunk for content_chunk in content
    )
    response = client.get(f"/v1/archive/{archive.id_}?encrypted=false")
    assert response.status_code == 200
    assert response.content == b"".join(content)


def test_hide_archive(client):
    query = QueryParameters(query_id="0123456789", search_string="*")
    content = [b"file content", b"and", b"another", b"chunk"]
    content_encrypted = [b"encrypted file content", b"and", b"another", b"chunk"]
    archive = Archive(
        query=query,
        plain_file=StoredArchive(
            storage_id=str(ObjectId()),
            sha256="",
            size=len(content),
        ),
        encrypted_file=StoredArchive(
            storage_id=str(ObjectId()),
            sha256="",
            size=len(content_encrypted),
        ),
    )
    get_archive_repository().get_by_id.return_value = archive

    response = client.post(f"/v1/archive/{archive.id_}", json={"hidden": True})

    assert response.status_code == 200
    get_archive_repository().update.assert_called_once_with(archive, include={"hidden"})
