import logging
import time
from abc import abstractmethod
from contextlib import contextmanager
from typing import Any, Callable, Generator, Generic, Literal, TypeVar
from uuid import UUID, uuid4

import typing_extensions
from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import (  # type: ignore[import-untyped]
    Boolean,
    Document,
    Index,
    Keyword,
    Search,
)
from elasticsearch_dsl.connections import get_connection  # type: ignore[import-untyped]
from elasticsearch_dsl.response import Response  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, computed_field

from common.messages.messages import MessageFileUpdate, PubSubMessage
from common.messages.pubsub_service import PubSubService
from common.models.base_repository import BaseRepository, RepositoryObject
from common.services.query_builder import QueryBuilder, QueryParameters

logger = logging.getLogger(__name__)

# This is here and set to a very large value because
# I didn't find a way to disable the timeout. None and False
# does not work...
INDEX_OPERATION_TIMEOUT = "9999d"
DEFAULT_PAGE_SIZE = 10
UPDATE_RETRY_ON_CONFLICT_COUNT = 5

# Default keepalive for point in time
PIT_KEEPALIVE = "5m"

# copied from: pydantic/main.py:
IncEx: typing_extensions.TypeAlias = (
    set[int] | set[str] | dict[int, Any] | dict[str, Any] | None
)


class InvalidSortFieldExceptions(Exception):
    pass


class _EsMeta(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    index: str | None = None
    highlight: dict[str, list[str]] | None = None
    score: float | None = None
    version: int | None = None
    seq_no: int | None = None
    primary_term: int | None = None


class EsRepositoryObject(RepositoryObject):
    @property
    def id_(self) -> UUID:
        return self.es_meta.id  # pylint: disable=no-member

    @id_.setter
    def id_(self, id_: UUID):
        self.es_meta.id = id_  # pylint: disable=assigning-non-slot

    @computed_field  # type: ignore[misc]
    @property
    def deduplication_fingerprint(self) -> str:
        return str(self.id_)

    es_meta: _EsMeta = Field(default_factory=_EsMeta, exclude=True)
    # The sort_unique field is required for sorted pagination requests using `search_after`
    # When issue a sorted pagination request, we always implicitly add `sort_unique` to
    # the sort fields so that elasticsearch pagination correctly works for entries which
    # have an exact match on all other sort fields.
    sort_unique: UUID = Field(default_factory=uuid4)
    hidden: bool = False

    def to_es_dict(self) -> dict:
        es_dict = self.model_dump(mode="json")
        return es_dict


class EsIdObject(RepositoryObject):
    @property
    def id_(self) -> UUID:
        return self.es_meta.id  # pylint: disable=no-member

    @id_.setter
    def id_(self, id_: UUID):
        self.es_meta.id = id_  # pylint: disable=assigning-non-slot

    es_meta: _EsMeta = Field(default_factory=_EsMeta, exclude=True)
    sort_value: str
    sort: list[Any]


class _EsRepositoryDocument(Document):
    deduplication_fingerprint = Keyword()
    sort_unique = (
        Keyword()
    )  # see comment in EsRepositoryObject why this field is needed
    hidden = Boolean()

    def to_es_dict(self) -> dict:
        document_dict = self.to_dict()

        # populate es_meta
        es_meta_dict = {**document_dict.get("es_meta", {}), **self.meta.to_dict()}
        if len(es_meta_dict) > 0:
            document_dict["es_meta"] = es_meta_dict

        return document_dict


EsRepositoryObjectT = TypeVar("EsRepositoryObjectT", bound=EsRepositoryObject)
EsRepositoryDocumentT = TypeVar("EsRepositoryDocumentT", bound=_EsRepositoryDocument)


class QuerySearchResult(BaseModel, Generic[EsRepositoryObjectT]):
    """Result of searching files in the database."""

    objs: list[EsRepositoryObjectT]
    total: int


class SortingParameters(BaseModel):
    sort_by_field: str = "_score"
    sort_direction: Literal["asc", "desc"] = "asc"


class PaginationParameters(BaseModel):
    sort_id: list[Any] | None = None
    page_size: int = DEFAULT_PAGE_SIZE


class BaseEsRepository(
    BaseRepository[EsRepositoryObjectT],
    Generic[EsRepositoryDocumentT, EsRepositoryObjectT],
):
    """Repository for CRUD operations backed by ElasticSearch."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            ES_REPOSITORY_TYPES.append(cls)

    def __init__(self, query_builder: QueryBuilder, pubsub_service: PubSubService):
        super().__init__()
        self._query_builder = query_builder
        self._pubsub_service = pubsub_service

    @property
    @abstractmethod
    def _document_type(self) -> type[EsRepositoryDocumentT]:
        pass

    @property
    def _index(self) -> Index:
        return self._document_type._index  # pylint: disable=protected-access

    @property
    def _index_name(self) -> str:
        return self._index._name  # pylint: disable=protected-access

    @property
    def _elasticsearch(self) -> Elasticsearch:
        return get_connection()

    def _object_to_document(
        self,
        obj: EsRepositoryObjectT,
    ) -> EsRepositoryDocumentT:
        obj_dict = obj.to_es_dict()

        meta = {}
        for meta_field, meta_value in obj.es_meta.model_dump(mode="json").items():
            meta[meta_field] = meta_value

        document = self._document_type(meta, **obj_dict)
        return document

    def _document_to_object(
        self, document: EsRepositoryDocumentT
    ) -> EsRepositoryObjectT:
        document_dict = document.to_es_dict()
        obj = self._object_type.model_validate(document_dict)
        return obj

    def _get_sort_by_field(self, field: str) -> str:
        field_name = field.split(".")[-1]
        field_mapping = self._index.get_field_mapping(
            using=self._elasticsearch, fields=[field]
        )
        if field == "_score":
            return field

        try:
            sort_field_mapping = field_mapping[self._index_name]["mappings"][field][
                "mapping"
            ][field_name]
        except KeyError as ex:
            raise InvalidSortFieldExceptions(f"Invalid sort field: {field}") from ex

        sort_field_type = sort_field_mapping["type"]
        match sort_field_type:
            case "text":
                try:
                    sort_field_keyword_keyword_field = sort_field_mapping["fields"][
                        "keyword"
                    ]
                    if sort_field_keyword_keyword_field["type"] != "keyword":
                        raise InvalidSortFieldExceptions(
                            f"Can not sort on text field ('{field}'): {field}.keyword"
                            " is not of type Keyword"
                        )
                    sort_field = f"{field}.keyword"
                except KeyError as ex:
                    raise InvalidSortFieldExceptions(
                        f"Can not sort on text field ('{field}') without keyword"
                        " multi-field"
                    ) from ex
            case _:
                # The default is just to return the field supplied:
                sort_field = field
        return sort_field

    def _paginate_search(
        self,
        search: Search,
        sort_params: SortingParameters,
        pagination_params: PaginationParameters | None,
        per_page_callback: Callable[[Response], Generator[Any, None, None]],
    ) -> Generator[Any, None, None]:
        """Runs the given search over several pages and calls the per_page_callback for
        every page."""

        # Create a point in time and use this point to run the query against.
        # We do this so that our search results / search ordering does not
        # change while we paginate over them.
        pit = self._elasticsearch.open_point_in_time(
            index=self._index_name, keep_alive=PIT_KEEPALIVE
        )
        pit_id: str = pit["id"]
        search = search.extra(pit={"id": pit_id, "keep_alive": PIT_KEEPALIVE})
        search = search.index()  # Remove index: pit requests run against no index

        # Make ES count the actual total values, which the query would match.
        # Even if we don't fetch that many hits due to pagination.
        search = search.extra(track_total_hits=True)

        search_after: list[Any] | None = None
        handled_hits_count = 0

        sort_by_field = self._get_sort_by_field(sort_params.sort_by_field)

        sort = {sort_by_field: {"order": sort_params.sort_direction}}
        search = search.sort(
            sort,
            # We append "sort_unique" here on purpose, see comment in EsRepositoryObject
            "sort_unique",
        )

        if pagination_params is not None and pagination_params.sort_id is not None:
            search = search.extra(
                search_after=pagination_params.sort_id,
            )

        if pagination_params is not None:
            search = search.extra(
                size=pagination_params.page_size,
            )

        while True:
            if search_after is not None:
                search = search.extra(search_after=search_after)

            results: Response = search.execute()
            hit_count = len(results.hits.hits)
            total_hits: int = results.hits.total.value

            if hit_count == 0:
                # no more hits
                break

            yield from per_page_callback(results)

            if pagination_params is not None:
                # pagination set, only returning one page
                break

            handled_hits_count += hit_count
            if handled_hits_count >= total_hits:
                break

            last_hit = results.hits.hits[-1]
            search_after = last_hit.sort

    def __get_search_by_deduplication_fingerprint(
        self,
        deduplication_fingerprint: str,
    ) -> Search:
        search: Search = self._document_type.search(using=self._elasticsearch)
        search = search.query(
            "match",
            deduplication_fingerprint=deduplication_fingerprint,
        )
        return search

    def __get_search_by_query(
        self,
        query: QueryParameters,
        full_highlight_context: bool = False,
    ) -> Search:
        search: Search = self._document_type.search(using=self._elasticsearch)
        search = search.highlight_options(
            order="score",
            pre_tags=["<highlight>"],
            post_tags=["</highlight>"],
        )
        if full_highlight_context:
            search = search.highlight("*", number_of_fragments=0)
        else:
            search = search.highlight("*")

        query_string = self._query_builder.build(query)
        search = search.query(
            "query_string",
            query=query_string,
            default_field="*",
            default_operator="AND",
        )

        return search

    def _send_file_update_message(
        self,
        obj: EsRepositoryObjectT,
    ):
        file_id = str(obj.id_)
        self._pubsub_service.publish_message(
            PubSubMessage(channel=file_id, message=MessageFileUpdate(fileId=file_id)),
        )

    def get_by_id(self, id_: UUID) -> EsRepositoryObjectT | None:
        document = self._document_type.get(id_, using=self._elasticsearch)
        if document is None:
            return document
        obj = self._document_to_object(document)
        return obj

    def get_by_deduplication_fingerprint(
        self, deduplication_fingerprint: str
    ) -> EsRepositoryObjectT | None:
        search = self.__get_search_by_deduplication_fingerprint(
            deduplication_fingerprint=deduplication_fingerprint
        )
        response = search.execute()
        if len(response) <= 0:
            return None
        if len(response) > 1:
            raise ValueError("dedeuplication_id not unique")
        document = response[0]
        obj = self._document_to_object(document)
        return obj

    def get_all(self) -> list[EsRepositoryObjectT]:
        result = list(self.get_generator_by_query(QueryParameters(search_string="*")))
        return result

    def get_by_query(
        self,
        query: QueryParameters,
        pagination_params: PaginationParameters,
        sort_params: SortingParameters | None = None,
    ) -> QuerySearchResult[EsRepositoryObjectT]:
        """Search for objects with the provided query."""
        gen = self.get_generator_by_query(query, pagination_params, sort_params)

        objs = list(gen)
        return QuerySearchResult[EsRepositoryObjectT](
            objs=objs,
            total=len(objs),
        )

    # pylint:disable=duplicate-code
    def get_generator_by_query(
        self,
        query: QueryParameters,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[EsRepositoryObjectT, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search = self.__get_search_by_query(query)

        def page_handler(result: Response):
            for hit in result.hits:
                yield self._document_to_object(hit)

        yield from self._paginate_search(
            search, sort_params, pagination_params, page_handler
        )

    def get_id_generator_by_query(
        self,
        query: QueryParameters,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[EsIdObject, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search = self.__get_search_by_query(query)

        # limit fields to fetch to just id
        sort_by_field = sort_params.sort_by_field
        search = search.source(includes=[sort_by_field], excludes=[])

        def page_handler(result: Response):
            for hit in result.hits:
                document: EsRepositoryDocumentT = hit
                document_dict = document.to_es_dict()
                if sort_by_field.startswith("_"):
                    # special handling for: _score
                    sort_value = str(
                        document_dict["es_meta"][sort_by_field.removeprefix("_")]
                    )
                else:
                    paths = sort_by_field.split(".")
                    current_val = document_dict
                    for path in paths:
                        current_val = current_val.get(path, None)
                        if current_val is None:
                            break
                    sort_value = str(current_val) if current_val is not None else ""
                document_dict.update({"sort_value": sort_value})
                document_dict.update({"sort": hit.meta.sort})
                yield EsIdObject.model_validate(document_dict)

        yield from self._paginate_search(
            search, sort_params, pagination_params, page_handler
        )

    def count_by_query(self, query: QueryParameters) -> int:
        """Counts the number of files returned by the given query."""

        search = self._document_type.search(using=self._elasticsearch)

        query_string = self._query_builder.build(query)
        search = search.query(
            "query_string", query=query_string, default_operator="AND"
        )
        return search.count()

    def get_by_id_with_query(
        self,
        id_: UUID,
        query: QueryParameters,
        full_highlight_context: bool,
    ) -> EsRepositoryObjectT | None:
        """Load details of an object, includes highlights based on the query."""
        search = self.__get_search_by_query(query, full_highlight_context)
        search = search.filter("term", _id=str(id_))
        result: Response = search.execute()
        if len(result.hits.hits) < 1:
            return None
        return self._document_to_object(result.hits[0])

    def save(self, obj: EsRepositoryObjectT):
        document = self._object_to_document(obj)
        document.save(refresh=True, using=self._elasticsearch)
        self._send_file_update_message(obj)

    def update(
        self, obj: EsRepositoryObjectT, include: IncEx = None, exclude: IncEx = None
    ):
        document = self._document_type({"_id": obj.id_})
        update_dict = obj.model_dump(
            include=include,
            exclude=exclude,
        )
        document.update(
            **update_dict,
            using=self._elasticsearch,
            refresh=True,
            retry_on_conflict=UPDATE_RETRY_ON_CONFLICT_COUNT,
        )
        self._send_file_update_message(obj)

    def init(self):
        # make sure the index is closed before initialization
        if self._index.exists(using=self._elasticsearch) and not self._index.is_closed(
            using=self._elasticsearch
        ):
            self._index.close(using=self._elasticsearch)
        # initialize
        self._document_type.init(using=self._elasticsearch)
        # after initialization: open the index
        self._index.open(using=self._elasticsearch)

    def reindex(self) -> str:
        clone_index_name = f"{self._index_name}-reindex-{time.time()}"

        backup_index_name = self.backup_index(clone_index_name)
        # Delete original index
        self._index.delete(using=self._elasticsearch)
        # Re-create new index
        self.init()
        # Re-index all data
        self._elasticsearch.reindex(
            source={"index": clone_index_name},
            dest={"index": self._index_name},
            wait_for_completion=False,
            timeout=INDEX_OPERATION_TIMEOUT,
        )
        return backup_index_name

    @contextmanager
    def make_index_readonly(self) -> Generator[None, None, None]:
        def set_index_readonly(readonly: bool):
            self._elasticsearch.indices.put_settings(
                settings={"index.blocks.write": readonly}, index=self._index_name
            )

        set_index_readonly(True)
        try:
            yield
        finally:
            set_index_readonly(False)

    def backup_index(self, backup_index_name: str | None = None) -> str:
        index_settings = self._elasticsearch.indices.get_settings(
            index=self._index_name, name="index.number_of_replicas"
        )[self._index_name]

        if backup_index_name is None:
            backup_index_name = f"{self._index_name}-backup-{time.time()}"

        with self.make_index_readonly():
            # Copy all data to temp-index
            self._elasticsearch.indices.clone(
                index=self._index_name,
                target=backup_index_name,
                settings=index_settings["settings"],
            )
            # Wait for the clone operation to complete
            self._elasticsearch.cluster.health(
                index=backup_index_name,
                wait_for_status="green",
                timeout=INDEX_OPERATION_TIMEOUT,
            )

        return backup_index_name

    def get_index_health(self) -> ObjectApiResponse[Any]:
        return self._elasticsearch.cluster.health(index=self._index_name)


# A list of all known elasticsearch repositories
ES_REPOSITORY_TYPES: list[type[BaseEsRepository]] = []
