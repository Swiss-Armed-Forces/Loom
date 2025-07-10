from datetime import datetime
from uuid import UUID, uuid4

from elasticsearch.dsl import Date, InnerDoc, Keyword, Object, Text
from pydantic import Field

from common.models.es_repository import BaseEsRepository
from common.services.query_builder import QueryParameters
from common.task_object.task_object import RepositoryTaskObject, _EsTaskDocument


class AiContextNotFoundException(Exception):
    pass


class AiContext(RepositoryTaskObject):
    query: QueryParameters
    chat_message_history_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)


class _EsQueryParameters(InnerDoc):
    query_id = Keyword()
    search_string = Text()
    languages = Text(multi=True)
    keep_alive = Keyword()


class _EsAiContext(_EsTaskDocument):
    query = Object(_EsQueryParameters)
    chat_message_history_id = Keyword()
    created_at = Date()

    class Index:  # pylint: disable=too-few-public-methods
        """The index."""

        name = "ai_context"
        settings = {
            # we disable data replication, since we run a single node cluster
            # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/high-availability-cluster-small-clusters.html # noqa: E501, B950 # pylint: disable=line-too-long
            "number_of_replicas": 0,
        }


class AiContextRepository(BaseEsRepository[_EsAiContext, AiContext]):
    @property
    def _object_type(self) -> type[AiContext]:
        return AiContext

    @property
    def _document_type(self) -> type[_EsAiContext]:
        return _EsAiContext
