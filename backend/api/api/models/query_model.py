from common.services.query_builder import QueryParameters
from pydantic import BaseModel


class QueryModel(BaseModel):
    search_string: str
    languages: list[str] | None = None

    @staticmethod
    def from_query_parameters(query: QueryParameters) -> "QueryModel":
        return QueryModel(**query.model_dump())

    def to_query_parameters(self) -> QueryParameters:
        return QueryParameters(**self.model_dump())
