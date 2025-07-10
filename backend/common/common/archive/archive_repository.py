from datetime import datetime

from elasticsearch.dsl import Date, InnerDoc, Keyword, Long, Object, Text
from pydantic import BaseModel, Field, computed_field

from common.models.es_repository import BaseEsRepository
from common.services.query_builder import QueryParameters
from common.task_object.task_object import RepositoryTaskObject, _EsTaskDocument
from common.utils.object_id_str import ObjectIdStr


class StoredArchive(BaseModel):
    storage_id: ObjectIdStr | None = None
    sha256: str | None = None
    size: int | None = None


class Archive(RepositoryTaskObject):
    query: QueryParameters
    plain_file: StoredArchive = Field(default_factory=StoredArchive)
    encrypted_file: StoredArchive = Field(default_factory=StoredArchive)
    created_at: datetime = Field(default_factory=datetime.now)

    @computed_field  # type: ignore[misc]
    @property
    def name(self) -> str:
        return f"loom_archive_{self.created_at}.zip"

    @computed_field  # type: ignore[misc]
    @property
    def name_encrypted(self) -> str:
        return f"loom_archive_{self.created_at}.loom"


class _EsQueryParameters(InnerDoc):
    query_id = Keyword()
    search_string = Text()
    languages = Text(multi=True)
    keep_alive = Keyword()


class _EsStoredArchive(InnerDoc):
    storage_id = Keyword()
    sha256 = Keyword()
    size = Long()


class _EsArchive(_EsTaskDocument):
    query = Object(_EsQueryParameters)
    langs = Text(multi=True)
    plain_file = Object(_EsStoredArchive)
    encrypted_file = Object(_EsStoredArchive)
    created_at = Date()
    name = Text()
    name_encrypted = Text()

    class Index:  # pylint: disable=too-few-public-methods
        """The index."""

        name = "archive"
        settings = {
            # we disable data replication, since we run a single node cluster
            # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/high-availability-cluster-small-clusters.html # noqa: E501, B950 # pylint: disable=line-too-long
            "number_of_replicas": 0,
        }


class ArchiveRepository(BaseEsRepository[_EsArchive, Archive]):
    @property
    def _object_type(self) -> type[Archive]:
        return Archive

    @property
    def _document_type(self) -> type[_EsArchive]:
        return _EsArchive
