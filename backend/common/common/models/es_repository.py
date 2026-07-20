import logging
import time
from abc import abstractmethod
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterator,
    Literal,
    Sequence,
    TypeVar,
)
from uuid import UUID, uuid4

from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.dsl import Boolean, Document, Index, Keyword, Q, Search
from elasticsearch.dsl.connections import get_connection
from elasticsearch.dsl.response import Response
from elasticsearch.helpers import streaming_bulk
from pydantic import BaseModel, Field, computed_field, model_validator
from pydantic.main import IncEx

from common.messages.messages import (
    MessageFileUpdate,
    MessageQueryIdExpired,
    PubSubMessage,
)
from common.messages.pubsub_service import PubSubService
from common.models.base_repository import (
    BaseRepository,
    BulkOperationResult,
    RepositoryBulkSaveError,
    RepositoryObject,
)
from common.services.lazybytes_service import FileStorageLazyBytes
from common.services.query_builder import (
    DEFAULT_PIT_KEEPALIVE,
    KeepAlive,
    QueryBuilder,
    QueryParameters,
)
from common.utils.pydantic_field_paths import iter_field_paths_by_type

logger = logging.getLogger(__name__)

# This is here and set to a very large value because
# I didn't find a way to disable the timeout. None and False
# does not work...
INDEX_OPERATION_TIMEOUT = "9999d"
INDEX_CLOSE_TIMEOUT_S = 60
INDEX_CLOSE_POLL_INTERVAL_S = 0.5
DEFAULT_PAGE_SIZE = 10
_ID_SCAN_PAGE_SIZE = 5000


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
    @model_validator(mode="before")
    @classmethod
    def _load_id(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        es_meta = data.get("es_meta", {})
        es_meta_id = es_meta.get("id") if isinstance(es_meta, dict) else None
        if es_meta_id is None:
            # Loading from serialised JSON (e.g. MANIFEST): promote id_ or id → es_meta.id
            id_val = data.get("id_") or data.get("id")
            if id_val is not None:
                if isinstance(es_meta, dict):
                    data["es_meta"] = {"id": id_val, **es_meta}
                else:
                    data["es_meta"] = {"id": id_val}
        return data

    @computed_field  # type: ignore[misc]
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

    def to_es_dict(
        self, include: IncEx | None = None, exclude: IncEx | None = None
    ) -> dict:
        es_dict = self.model_dump(mode="json", include=include, exclude=exclude)
        # Expose id_ as 'id' in the ES body so it is searchable as id:<uuid>
        if "id_" in es_dict:
            es_dict["id"] = es_dict.pop("id_")
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
    id = Keyword()
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

    @classmethod
    def get_default_fields(cls) -> list[str]:
        """Extract all field names from the document mapping, including nested fields
        and multi-fields.

        Returns a list of field names that can be used for index.query.default_field
        setting to limit default search scope and improve performance.
        """

        def extract_fields(mapping: dict, prefix: str = "") -> list[str]:
            """Recursively extract field names from mapping dictionary.

            Args:
                mapping: The mapping dictionary (can contain 'properties' or 'fields')
                prefix: The current field path prefix (for nested fields)

            Returns:
                List of field names including nested paths
                (e.g., 'parent.child', 'title.keyword')
            """
            fields = []
            for field_name, field_config in mapping.items():
                # Build the full field path
                full_path = f"{prefix}.{field_name}" if prefix else field_name
                fields.append(full_path)

                if isinstance(field_config, dict):
                    # Recurse into nested object properties
                    if "properties" in field_config:
                        nested_fields = extract_fields(
                            field_config["properties"], full_path
                        )
                        fields.extend(nested_fields)

                    # Recurse into multi-fields
                    if "fields" in field_config:
                        multi_fields = extract_fields(field_config["fields"], full_path)
                        fields.extend(multi_fields)

            return fields

        mapping_dict = cls._doc_type.mapping.to_dict()
        field_names = extract_fields(mapping_dict.get("properties", {}))
        return field_names


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
    sort_id: list[Any] = Field(default_factory=list)
    page_size: int = DEFAULT_PAGE_SIZE


class BaseEsRepository(  # pylint: disable=too-many-public-methods
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
    def index_name(self) -> str:
        return self._index_name

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
                # text fields can only be sorted via their keyword sub-field (if existent)
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

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _paginate_search(
        self,
        search: Search[EsRepositoryDocumentT],
        query: QueryParameters,
        sort_params: SortingParameters,
        pagination_params: PaginationParameters | None,
        per_page_callback: Callable[
            [Response[EsRepositoryDocumentT]], Generator[Any, None, None]
        ],
        scan_page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Generator[Any, None, None]:
        """Runs the given search over several pages and calls the per_page_callback for
        every page."""
        search_after: list[Any] | None = None

        sort_by_field = self._get_sort_by_field(sort_params.sort_by_field)

        # When scanning all results (no pagination_params), _score sorting is
        # non-deterministic: identical scores cause search_after to skip or
        # duplicate documents across pages. Fall back to sort_unique which is
        # guaranteed unique and stable.
        if pagination_params is None and sort_by_field == "_score":
            search = search.sort(
                {"sort_unique": {"order": sort_params.sort_direction}},
            )
        else:
            search = search.sort(
                {sort_by_field: {"order": sort_params.sort_direction}},
                # We append "sort_unique" here on purpose, see comment in
                # EsRepositoryObject
                "sort_unique",
            )

        if pagination_params is not None:
            if pagination_params.sort_id:
                search = search.extra(
                    search_after=pagination_params.sort_id,
                )
            search = search.extra(
                size=pagination_params.page_size,
            )
        else:
            if query.query_id is None:
                query.query_id = self.open_point_in_time()
            search = search.extra(size=scan_page_size)

        while True:
            if search_after is not None:
                search = search.extra(search_after=search_after)

            result = self._execute_search_with_query(search=search, query=query)
            page_hits = result.hits

            if len(page_hits) <= 0:
                # no more hits: last page
                break

            yield from per_page_callback(result)

            if pagination_params is not None:
                # pagination set, only returning one page
                break

            last_hit = page_hits.hits[-1]  # type: ignore
            search_after = last_hit.sort

    def _get_search_by_query(
        self,
        query: QueryParameters,
        full_highlight_context: bool = False,
    ) -> Search[EsRepositoryDocumentT]:
        search: Search[EsRepositoryDocumentT] = self._document_type.search(
            using=self._elasticsearch
        )

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
            default_operator="AND",
            # Be lenient because the index-level default fields are set dynamically
            # (index.query.default_field). Those fields can span multiple data types
            # (text, numeric, boolean, date), and query_string parsing would otherwise
            # fail when a term is incompatible with a field's type.
            lenient=True,
        )

        return search

    def _send_file_update_message_by_id(self, id_: UUID):
        file_id = str(id_)
        self._pubsub_service.publish_message(
            PubSubMessage(channel=file_id, message=MessageFileUpdate(fileId=file_id)),
        )

    def open_point_in_time(
        self,
        keep_alive: KeepAlive = DEFAULT_PIT_KEEPALIVE,
    ) -> str:
        point_in_time = self._elasticsearch.open_point_in_time(
            index=self._index_name, keep_alive=keep_alive
        )
        point_in_time_id: str = point_in_time["id"]
        return point_in_time_id

    def get_by_id(self, id_: UUID) -> EsRepositoryObjectT | None:
        try:
            document = self._document_type.get(str(id_), using=self._elasticsearch)
        except NotFoundError:
            return None
        if document is None:
            return document
        obj = self._document_to_object(document)
        return obj

    def get_by_deduplication_fingerprint(
        self, deduplication_fingerprint: str
    ) -> EsRepositoryObjectT | None:
        search: Search[EsRepositoryDocumentT] = self._document_type.search(
            using=self._elasticsearch
        )
        search = search.query(
            "match",
            deduplication_fingerprint=deduplication_fingerprint,
        )
        response = search.execute()
        if len(response) <= 0:
            return None
        if len(response) > 1:
            logger.warning(
                "deduplication_fingerprint (%s) not unique.", deduplication_fingerprint
            )
        document = response[0]
        obj = self._document_to_object(document)
        return obj

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

        search = self._get_search_by_query(query=query)

        def page_handler(result: Response[EsRepositoryDocumentT]):
            for hit in result.hits:
                yield self._document_to_object(hit)

        yield from self._paginate_search(
            search=search,
            query=query,
            sort_params=sort_params,
            pagination_params=pagination_params,
            per_page_callback=page_handler,
        )

    def get_id_generator_by_query(
        self,
        query: QueryParameters,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[EsIdObject, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search = self._get_search_by_query(query=query)

        # limit fields to fetch to just id
        sort_by_field = sort_params.sort_by_field
        search = search.source(includes=[sort_by_field], excludes=[])

        def page_handler(result: Response[EsRepositoryDocumentT]):
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
                    # descend into document
                    for path in paths:
                        try:
                            current_val = current_val[path]
                        except KeyError:
                            break
                    sort_value = str(current_val) if current_val is not None else ""
                document_dict.update({"sort_value": sort_value})
                document_dict.update({"sort": hit.meta.sort})
                yield EsIdObject.model_validate(document_dict)

        yield from self._paginate_search(
            search=search,
            query=query,
            sort_params=sort_params,
            pagination_params=pagination_params,
            per_page_callback=page_handler,
            scan_page_size=_ID_SCAN_PAGE_SIZE,
        )

    def _execute_search_with_query(
        self, search: Search[EsRepositoryDocumentT], query: QueryParameters
    ) -> Response[EsRepositoryDocumentT]:
        if query.query_id is None:
            return search.execute()
        try:
            return (
                search.index()  # Remove index: pit requests run against no index
                .extra(pit={"id": query.query_id, "keep_alive": query.keep_alive})
                .execute()
            )
        except NotFoundError:
            # Returned when the PIT for the query is not found. Probably expired.
            logger.info("Query %s expired, creating new one", query)
            old_query_id = query.query_id
            # Mutate the query's PIT so the caller has access to the new PIT
            query.query_id = self.open_point_in_time()

            self._pubsub_service.publish_message(
                PubSubMessage(
                    channel=old_query_id,
                    message=MessageQueryIdExpired(
                        old_id=old_query_id, new_id=query.query_id
                    ),
                ),
            )
            return self._execute_search_with_query(search, query)

    def count_by_query(self, query: QueryParameters) -> int:
        """Counts the number of files returned by the given query."""
        # search.count() is not pit aware so we use a query instead
        search = self._get_search_by_query(query=query)
        search = search[0:0]  # do not fetch hits
        # Make ES count fetch the actual total values, which the query would match.
        search = search.extra(track_total_hits=True)

        result = self._execute_search_with_query(search=search, query=query)
        # Cf. https://github.com/elastic/elasticsearch-dsl-py/issues/1897
        return result.hits.total.value  # type: ignore

    def is_file_storage_service_id_referenced(self, service_id: UUID) -> bool:
        """Return True if service_id is referenced by any FileStorageLazyBytes field in
        this repository's index."""
        paths = list(
            iter_field_paths_by_type(
                self._object_type, FileStorageLazyBytes, suffix=".service_id"
            )
        )
        if not paths:
            return False
        return (
            Search(using=self._elasticsearch, index=self._index_name)
            .filter(
                "bool",
                should=[
                    Q("term", **{p.replace(".", "__"): str(service_id)}) for p in paths
                ],
                minimum_should_match=1,
            )
            .count()
            > 0
        )

    def get_by_id_with_query(
        self,
        id_: UUID,
        query: QueryParameters,
        full_highlight_context: bool,
    ) -> EsRepositoryObjectT | None:
        """Load details of an object, includes highlights based on the query."""
        search: Search[EsRepositoryDocumentT] = self._get_search_by_query(
            query=query, full_highlight_context=full_highlight_context
        )
        search = search.filter("term", _id=str(id_))
        result = self._execute_search_with_query(search=search, query=query)
        if len(result.hits) < 1:
            return None
        return self._document_to_object(result.hits[0])

    def save(self, obj: EsRepositoryObjectT):
        """Persists the object and updates its ES metadata in-place."""
        document = self._object_to_document(obj)
        document.save(refresh="wait_for", using=self._elasticsearch)

        # Update object metadata
        new_obj = self._document_to_object(document)
        obj.es_meta = new_obj.es_meta

        self._send_file_update_message_by_id(obj.id_)

    def update(
        self,
        obj: EsRepositoryObjectT,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
    ):
        """Update the object and updates its ES metadata in-place."""
        document = self._object_to_document(obj)
        es_dict = obj.to_es_dict(include=include, exclude=exclude)

        # Build update kwargs with optimistic concurrency control
        update_kwargs: dict[str, Any] = {
            "using": self._elasticsearch,
            "refresh": "wait_for",
        }
        if obj.es_meta.seq_no is not None and obj.es_meta.primary_term is not None:
            update_kwargs["if_seq_no"] = obj.es_meta.seq_no
            update_kwargs["if_primary_term"] = obj.es_meta.primary_term

        document.update(**es_dict, **update_kwargs)

        # Update object metadata
        new_obj = self._document_to_object(document)
        obj.es_meta = new_obj.es_meta

        self._send_file_update_message_by_id(obj.id_)

    def bulk_save(
        self, objects: Sequence[EsRepositoryObjectT]
    ) -> Iterator[BulkOperationResult]:
        """Persist multiple objects using ES streaming bulk API."""
        if not objects:
            return

        actions = []
        for obj in objects:
            doc = self._object_to_document(obj)
            action: dict[str, Any] = {
                "_op_type": "index",
                "_index": self._index._name,  # pylint: disable=protected-access
                "_id": str(obj.id_),
                "_source": doc.to_dict(),
            }
            # Add optimistic concurrency if available
            if obj.es_meta.seq_no is not None and obj.es_meta.primary_term is not None:
                action["if_seq_no"] = obj.es_meta.seq_no
                action["if_primary_term"] = obj.es_meta.primary_term
            actions.append(action)

        # streaming_bulk yields results in same order as input actions
        for obj, (ok, item) in zip(
            objects,
            streaming_bulk(
                self._elasticsearch,
                actions,
                raise_on_error=False,
                raise_on_exception=False,
                refresh="wait_for",
            ),
        ):
            _op_type, info = item.popitem()

            if ok:
                # Update object's es_meta with new seq_no/primary_term
                obj.es_meta.seq_no = info.get("_seq_no")
                obj.es_meta.primary_term = info.get("_primary_term")
                self._send_file_update_message_by_id(obj.id_)
                yield BulkOperationResult(object_id=obj.id_, success=True)
            else:
                yield BulkOperationResult(
                    object_id=obj.id_,
                    success=False,
                    error=RepositoryBulkSaveError(f"Bulk save failed: {info}"),
                )

    def delete_by_id(self, id_: UUID) -> bool:
        """Delete a document by ID.

        Returns:
            True if the document was deleted, False if it didn't exist.
        """
        try:
            document = self._document_type({"_id": id_})
            document.delete(using=self._elasticsearch, refresh="wait_for")
            self._send_file_update_message_by_id(id_)
            return True
        except NotFoundError:
            return False

    def count(self) -> int:
        """Count all documents in this index."""
        search = self._document_type.search(using=self._elasticsearch)
        search = search[0:0].extra(track_total_hits=True)
        response = search.execute()
        return response.hits.total.value  # type: ignore

    def flush(self) -> None:
        """Delete all documents in this index."""
        search = self._document_type.search(using=self._elasticsearch)
        search = search.query("match_all")
        search.params(refresh=True).delete()

    def init(self):
        with self._temporarily_closed_index():
            # set settings before initializing
            self._index.settings(
                query={"default_field": self._document_type.get_default_fields()},
                # When reinit() reindexes into a new index with updated mappings, a document
                # whose stored value is incompatible with the new field type would otherwise be
                # dropped entirely. With ignore_malformed=True, ES silently skips the offending
                # field and still indexes the rest of the document (best-effort preservation).
                mapping={"ignore_malformed": True},
            )
            # initialize
            self._document_type.init(using=self._elasticsearch)

    @contextmanager
    def _temporarily_closed_index(self) -> Generator[None, None, None]:
        """Close the index for the duration of the block, reopening it afterwards.

        Guarantees the index is reopened even if an exception is raised inside the
        block.

        This is a workaround for a gap in elasticsearch-py's Index.save(): it uses the
        old close-manually -> put_settings -> open-manually pattern instead of the
        put_settings(reopen=True) API introduced in ES 8.12, which handles the
        close/update/open atomically. Without closing the index first, ES rejects
        put_settings with non-dynamic settings (e.g. analysis) on open indices with a
        BadRequestError. There is currently no upstream issue or PR tracking this in
        elastic/elasticsearch-py.
        """
        if self._index.exists(using=self._elasticsearch) and not self._index.is_closed(
            using=self._elasticsearch
        ):
            self._close_index_blocking()
        try:
            yield
        finally:
            self._open_index_blocking()

    def _close_index_blocking(self) -> None:
        """Close the index, polling until cluster state confirms it is closed.

        Falls back to polling is_closed() if shards_acknowledged is False in the close
        response. Note: the semantics of shards_acknowledged for indices.close() are not
        clearly documented by Elasticsearch.
        """
        close_response = self._index.close(using=self._elasticsearch)
        if not close_response.get("shards_acknowledged", True):
            deadline = time.time() + INDEX_CLOSE_TIMEOUT_S
            while not self._index.is_closed(using=self._elasticsearch):
                if time.time() > deadline:
                    raise TimeoutError(
                        f"Index {self._index_name!r} did not close within timeout"
                    )
                time.sleep(INDEX_CLOSE_POLL_INTERVAL_S)

    def _open_index_blocking(self) -> None:
        """Open the index and wait until it is healthy."""
        self._index.open(using=self._elasticsearch)
        self._elasticsearch.cluster.health(
            index=self._index_name,
            wait_for_status="green",
            timeout=INDEX_OPERATION_TIMEOUT,
        )

    def reinit(self) -> str:
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

    def get_mapping(self) -> dict[str, Any]:
        return self._index.get_mapping()[self._index_name]["mappings"]

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
            index=self._index_name
        )[self._index_name]["settings"]

        # overwrite default for backup index
        index_settings = {
            **index_settings,
            **{
                "index": {
                    "number_of_replicas": 0,
                }
            },
        }

        if backup_index_name is None:
            backup_index_name = f"{self._index_name}-backup-{time.time()}"

        with self.make_index_readonly():
            # Copy all data to temp-index
            self._elasticsearch.indices.clone(
                index=self._index_name,
                target=backup_index_name,
                settings=index_settings,
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
