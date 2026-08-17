from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from elasticsearch.dsl import Date, InnerDoc, Keyword, Object, Text
from pydantic import BaseModel, Field

from common.models.es_repository import BaseEsRepository
from common.settings import settings
from common.task_object.task_object import RepositoryTaskObject, _EsTaskDocument

_MAX_CONTEXTS = 100


class Capability(StrEnum):
    RESEARCH_MODE = "research_mode"


class AiContextNotFoundException(Exception):
    pass


class ReasoningActivityEntry(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    text: str


class ToolCallActivityEntry(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: str


ActivityEntry = ReasoningActivityEntry | ToolCallActivityEntry


class AiQuestionCitation(BaseModel):
    file_id: UUID
    text: str


class AiQuestion(BaseModel):
    question: str
    answer: str
    citations: list[AiQuestionCitation] = Field(default_factory=list)
    activity: list[ReasoningActivityEntry | ToolCallActivityEntry] = Field(
        default_factory=list
    )


class AiContext(RepositoryTaskObject):
    chat_message_history_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    questions: list[AiQuestion] = Field(default_factory=list)
    active_capabilities: list[Capability] = Field(default_factory=list)


class _EsAiQuestionCitation(InnerDoc):
    file_id = Keyword()
    text = Text()


class _EsActivityEntry(InnerDoc):
    type = Keyword()
    text = Text()
    tool_name = Keyword()
    input = Object()
    output = Text()


class _EsAiQuestion(InnerDoc):
    question = Text()
    answer = Text()
    citations = Object(_EsAiQuestionCitation, multi=True)
    activity = Object(_EsActivityEntry, multi=True)


class _EsAiContext(_EsTaskDocument):
    chat_message_history_id = Keyword()
    created_at = Date()
    questions = Object(_EsAiQuestion, multi=True)
    active_capabilities = Keyword(multi=True)

    class Index:  # pylint: disable=too-few-public-methods
        """The index."""

        name = "ai_context"
        settings = {
            "number_of_shards": settings.es_number_of_shards,
            "number_of_replicas": settings.es_number_of_replicas,
        }


class AiContextRepository(BaseEsRepository[_EsAiContext, AiContext]):
    @property
    def _object_type(self) -> type[AiContext]:
        return AiContext

    @property
    def _document_type(self) -> type[_EsAiContext]:
        return _EsAiContext

    def list_all(self) -> list[AiContext]:
        search = (
            self._document_type.search().sort("-created_at").extra(size=_MAX_CONTEXTS)
        )
        return [self._document_to_object(hit) for hit in search.execute()]
