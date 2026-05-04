from uuid import UUID

from elasticsearch.dsl import Keyword

from common.models.es_repository import (
    BaseEsRepository,
    EsRepositoryObject,
    _EsRepositoryDocument,
)
from common.settings import settings


class RootTaskInformation(EsRepositoryObject):
    root_task_id: UUID
    object_id: UUID


class _EsRootTaskInformation(_EsRepositoryDocument):
    root_task_id = Keyword()
    object_id = Keyword()

    class Index:  # pylint: disable=too-few-public-methods
        """The index."""

        name = "root_task_information"
        settings = {
            "number_of_shards": settings.es_number_of_shards,
            "number_of_replicas": settings.es_number_of_replicas,
        }


class RootTaskInformationRepository(
    BaseEsRepository[_EsRootTaskInformation, RootTaskInformation]
):
    @property
    def _object_type(self) -> type[RootTaskInformation]:
        return RootTaskInformation

    @property
    def _document_type(self) -> type[_EsRootTaskInformation]:
        return _EsRootTaskInformation

    def get_by_root_task_id(self, root_task_id: UUID) -> RootTaskInformation:
        search = self._document_type.search(using=self._elasticsearch)
        search = search.query("match", root_task_id=str(root_task_id))
        response = search.execute()
        if len(response) <= 0:
            raise ValueError(f"Root task info with id {root_task_id} not found")
        document = response[0]
        obj = self._document_to_object(document)
        return obj
