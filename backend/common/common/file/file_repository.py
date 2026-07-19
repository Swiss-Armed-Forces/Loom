# pylint: disable=too-many-lines
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Any, Callable, Generator, Sequence, cast
from uuid import UUID

import imapclient.imap_utf7
from elasticsearch.dsl import (
    A,
    Agg,
    Boolean,
    Date,
    DenseVector,
    Float,
    InnerDoc,
    Keyword,
    Long,
    MetaField,
    Nested,
    Object,
    Q,
    Search,
    Text,
)
from elasticsearch.dsl.query import Query
from elasticsearch.dsl.response import Response
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)
from pydantic_core import core_schema

from common.file.file_statistics import (
    BooleanTermsStat,
    DateHistogramStat,
    GroupedHistogramStatistics,
    GroupedStatisticsEntry,
    HistogramStat,
    NumberHistogramStat,
    StatisticsEntry,
    TermsStat,
    TermsStatistics,
    discover_stats,
)
from common.messages.pubsub_service import PubSubService
from common.models.es_repository import (
    BaseEsRepository,
    PaginationParameters,
    SortingParameters,
)
from common.services.lazybytes_service import FileStorageLazyBytes
from common.services.query_builder import (
    QueryBuilder,
    QueryParameters,
)
from common.settings import settings
from common.task_object.task_object import RepositoryTaskObject, _EsTaskDocument
from common.utils.unique_list import unique_list

logger = logging.getLogger(__name__)

PATH_SEPARATOR = "/"
PATH_ROOT = "//"
TREE_PATH_MAX_ELEMENT_COUNT = 10
ES_RESERVED_PATTERN = re.compile(r"([\".?+*|{}\][\\()])")
KNN_CANDIDATES_FACTOR = 5  # how many more candidates to select for KNN per shared


class FileRepositoryException(Exception):
    pass


class FileNotFoundException(FileRepositoryException):
    pass


class FileWithoutStorageDataException(FileRepositoryException):
    pass


class Embedding(BaseModel):
    # ES 9.2+ excludes dense_vector fields from _source by default
    # (exclude_vectors feature). The elasticsearch-dsl library sets
    # exclude_vectors=False for top-level searches, but this does
    # not propagate to nested InnerDoc DenseVector fields, so vector
    # may be absent on read. Vectors are only needed in the write
    # path and KNN queries (passed directly),never for display.
    # see:
    # https://www.elastic.co/search-labs/blog/elasticsearch-exclude-vectors-from-source
    vector: list[float] | None = None
    text: str


class KnnSearchEmbedding(BaseModel):
    file_id: UUID
    file_score: float
    text_score: float
    text: str


class _EsEmbedding(InnerDoc):
    vector = DenseVector(dims=settings.llm.embedding.dimensions, similarity="cosine")
    text = Text(term_vector="with_positions_offsets")


class Secret(BaseModel):
    line_number: int
    secret: str


class _EsSecret(InnerDoc):
    line_number = Long()
    secret = Text(term_vector="with_positions_offsets")


class TranslatedLanguage(BaseModel):
    confidence: float
    language: Annotated[str, TermsStat()]
    text: str


class _EsTranslatedLanguage(InnerDoc):
    confidence = Float()
    language = Keyword()
    text = Text(term_vector="with_positions_offsets")


class ImapPurePath(PurePosixPath):
    """IMAP path - behaves like PurePosixPath but works with Pydantic."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __):

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.str_schema(),
                ]
            ),
            # spellchecker:off
            serialization=core_schema.plain_serializer_function_ser_schema(
                str,
                return_schema=core_schema.str_schema(),
            ),
            # spellchecker:on
        )


class ImapInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    uid: int
    folder: ImapPurePath

    @computed_field  # type: ignore[misc]
    @property
    def folder_utf7(self) -> str:
        data = imapclient.imap_utf7.encode(str(self.folder))
        return data.decode()


class _EsImapInfo(InnerDoc):
    uid = Long()
    folder = Text(
        fielddata=True,
        fields={
            "tree": Text(
                analyzer="path_analyzer",
                fielddata=True,
            ),
            "keyword": Keyword(),
        },
    )
    folder_utf7 = Keyword()


class _EsLazyBytes(InnerDoc):
    embedded_data = Keyword()
    service_id = Keyword()


class RenderedFile(BaseModel):
    image_data: FileStorageLazyBytes | None = None
    office_pdf_data: FileStorageLazyBytes | None = None
    browser_pdf_data: FileStorageLazyBytes | None = None


class _EsRenderedFile(InnerDoc):
    image_data = Object(_EsLazyBytes)
    office_pdf_data = Object(_EsLazyBytes)
    browser_pdf_data = Object(_EsLazyBytes)


TAG_LEN_MIN = 1
TAG_LEN_MAX = 25
Tag = Annotated[str, StringConstraints(min_length=TAG_LEN_MIN, max_length=TAG_LEN_MAX)]


class TikaMeta(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    dc_title: str | list[str] | None = Field(default=None, alias="dc:title")
    dc_description: str | list[str] | None = Field(default=None, alias="dc:description")
    dc_subject: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="dc:subject"
    )
    dc_creator: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="dc:creator"
    )
    dcterms_created: Annotated[
        datetime | list[datetime] | None, DateHistogramStat()
    ] = Field(default=None, alias="dcterms:created")
    dcterms_modified: Annotated[
        datetime | list[datetime] | None, DateHistogramStat()
    ] = Field(default=None, alias="dcterms:modified")

    pdf_producer: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="pdf:producer"
    )
    pdf_docinfo_producer: str | list[str] | None = Field(
        default=None, alias="pdf:docinfo:producer"
    )
    pdf_docinfo_creator: str | list[str] | None = Field(
        default=None, alias="pdf:docinfo:creator"
    )
    pdf_docinfo_creator_tool: Annotated[
        str | list[str] | None, TermsStat(keyword=True)
    ] = Field(default=None, alias="pdf:docinfo:creator_tool")
    pdf_docinfo_created: Annotated[
        datetime | list[datetime] | None, DateHistogramStat()
    ] = Field(default=None, alias="pdf:docinfo:created")
    pdf_docinfo_modified: Annotated[
        datetime | list[datetime] | None, DateHistogramStat()
    ] = Field(default=None, alias="pdf:docinfo:modified")
    pdf_docinfo_keywords: str | list[str] | None = Field(
        default=None, alias="pdf:docinfo:keywords"
    )
    pdf_docinfo_title: str | list[str] | None = Field(
        default=None, alias="pdf:docinfo:title"
    )

    message_from: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Message-From"
    )
    message_from_name: Annotated[str | list[str] | None, TermsStat(keyword=True)] = (
        Field(default=None, alias="Message:From-Name")
    )
    message_from_email: Annotated[str | list[str] | None, TermsStat(keyword=True)] = (
        Field(default=None, alias="Message:From-Email")
    )
    message_to: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Message-To"
    )
    message_to_name: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Message:To-Name"
    )
    message_to_email: Annotated[str | list[str] | None, TermsStat(keyword=True)] = (
        Field(default=None, alias="Message:To-Email")
    )
    message_cc: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Message-Cc"
    )
    message_bcc: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Message-Bcc"
    )

    meta_last_author: Annotated[str | list[str] | None, TermsStat(keyword=True)] = (
        Field(default=None, alias="meta:last-author")
    )
    content_type: Annotated[str | list[str] | None, TermsStat(keyword=True)] = Field(
        default=None, alias="Content-Type"
    )


class _EsTikaMeta(InnerDoc):
    dc_title = Text(multi=True, fields={"keyword": Keyword()})
    dc_description = Text(multi=True, fields={"keyword": Keyword()})
    dc_subject = Text(multi=True, fields={"keyword": Keyword()})
    dc_creator = Text(multi=True, fields={"keyword": Keyword()})
    dcterms_created = Date(multi=True)
    dcterms_modified = Date(multi=True)

    pdf_producer = Text(multi=True, fields={"keyword": Keyword()})
    pdf_docinfo_producer = Text(multi=True, fields={"keyword": Keyword()})
    pdf_docinfo_creator = Text(multi=True, fields={"keyword": Keyword()})
    pdf_docinfo_creator_tool = Text(multi=True, fields={"keyword": Keyword()})
    pdf_docinfo_created = Date(multi=True)
    pdf_docinfo_modified = Date(multi=True)
    pdf_docinfo_keywords = Text(multi=True, fields={"keyword": Keyword()})

    message_from = Text(multi=True, fields={"keyword": Keyword()})
    message_from_name = Text(multi=True, fields={"keyword": Keyword()})
    message_from_email = Text(multi=True, fields={"keyword": Keyword()})
    message_to = Text(multi=True, fields={"keyword": Keyword()})
    message_to_name = Text(multi=True, fields={"keyword": Keyword()})
    message_to_email = Text(multi=True, fields={"keyword": Keyword()})
    message_cc = Text(multi=True, fields={"keyword": Keyword()})
    message_bcc = Text(multi=True, fields={"keyword": Keyword()})

    meta_last_author = Text(multi=True, fields={"keyword": Keyword()})
    content_type = Text(multi=True, fields={"keyword": Keyword()})


class Attachment(BaseModel):
    id: UUID
    name: str


class _EsAttachment(InnerDoc):
    id = Keyword()
    name = Keyword()


class FilePurePath(PurePosixPath):
    """File path - behaves like PurePosixPath but works with Pydantic."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __):

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.str_schema(),
                ]
            ),
            # spellchecker:off
            serialization=core_schema.plain_serializer_function_ser_schema(
                str,
                return_schema=core_schema.str_schema(),
            ),
            # spellchecker:on
        )


class File(RepositoryTaskObject):
    state: Annotated[str, TermsStat()] = "started"

    storage_data: FileStorageLazyBytes | None = None

    content: str | None = None
    content_truncated: Annotated[bool, BooleanTermsStat()] = False
    attachments_skipped: Annotated[bool, BooleanTermsStat()] = False
    full_name: FilePurePath

    @computed_field  # type: ignore[misc]
    @property
    def deduplication_fingerprint(self) -> str:
        file_data_hash = hashlib.sha256()
        file_data_hash.update(str(self.full_name).encode())
        file_data_hash.update(self.sha256.encode())
        return file_data_hash.hexdigest()

    @computed_field  # type: ignore[misc]
    @property
    def full_path(self) -> FilePurePath:
        if isinstance(self.full_name, str):
            return FilePurePath(f"//{self.source}/{self.full_name}")
        full_name_str = str(self.full_name)
        # Filenames that already start with "//" are stored as the literal
        # full_path (e.g. "//api-upload/dir/file.txt" set by the tree tests).
        # Return them as-is so the source prefix is not doubled.
        if full_name_str.startswith("//"):
            return self.full_name
        # Strip any leading slash(es) to prevent pathlib's / operator from
        # treating full_name as an absolute path and silently dropping the
        # source prefix. "lstrip" covers both "/" and "//" that slipped through.
        return FilePurePath(f"//{self.source}/{full_name_str.lstrip('/')}")

    @computed_field  # type: ignore[misc]
    @property
    def short_name(self) -> str:
        return self.full_name.name

    @computed_field  # type: ignore[misc]
    @property
    def extension(self) -> Annotated[str, TermsStat()]:
        return self.full_name.suffix

    source: Annotated[str, TermsStat()]
    parent_id: UUID | None = None
    sha256: str
    uploaded_datetime: Annotated[datetime, DateHistogramStat()] = Field(
        default_factory=datetime.now
    )
    size: Annotated[int, NumberHistogramStat(label="File Size (bytes)")]
    reindex_count: Annotated[int, NumberHistogramStat(label="Reindex Count")] = 0
    thumbnail_data: FileStorageLazyBytes | None = None
    thumbnail_total_frames: Annotated[
        int | None, NumberHistogramStat(label="Frame Count")
    ] = None
    rendered_file: RenderedFile = RenderedFile()
    tags: Annotated[list[Tag], TermsStat()] = []
    magic_file_type: Annotated[str | None, TermsStat()] = None
    tika_language: Annotated[str | None, TermsStat()] = None
    detected_language: Annotated[str | None, TermsStat()] = None
    translations: list[TranslatedLanguage] = Field(default_factory=list)
    is_spam: Annotated[bool | None, BooleanTermsStat()] = None
    tika_file_type: Annotated[str | None, TermsStat()] = None
    archives: Annotated[list[str], TermsStat()] = []
    tika_meta: TikaMeta = Field(default_factory=TikaMeta)
    tika_handled_by: Annotated[str | None, TermsStat()] = None
    attachments: list[Attachment] = []
    recursion_depth: Annotated[int, NumberHistogramStat(label="Recursion Depth")] = 0
    summary: str | None = None
    image_description: str | None = None
    embeddings: list[Embedding] = []
    trufflehog_secrets: list[Secret] | None = None
    ripsecrets_secrets: list[Secret] | None = None
    imap: ImapInfo | None = None
    flagged: Annotated[bool, BooleanTermsStat()] = False
    seen: Annotated[bool, BooleanTermsStat()] = False

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, tags: list[Tag]) -> list[Tag]:
        return unique_list(tags)

    @field_validator("archives")
    @classmethod
    def unique_archives(cls, archives: list[str]) -> list[str]:
        return unique_list(archives)


class _EsFile(_EsTaskDocument):
    storage_data = Object(_EsLazyBytes)
    content = Text(
        term_vector="with_positions_offsets",
        fields={
            "ngram": Text(
                term_vector="with_positions_offsets", analyzer="ngram_analyzer"
            ),
        },
    )
    content_truncated = Boolean()
    attachments_skipped = Boolean()
    full_name = Text(fields={"keyword": Keyword()})
    full_path = Text(
        fielddata=True,
        fields={
            "tree": Text(
                analyzer="path_analyzer",
                fielddata=True,
            ),
            "keyword": Keyword(),
        },
    )
    short_name = Text(fields={"keyword": Keyword()})
    extension = Keyword()
    source = Keyword()
    parent_id = Keyword()
    sha256 = Keyword()
    uploaded_datetime = Date()
    size = Long()
    reindex_count = Long()
    thumbnail_data = Object(_EsLazyBytes)
    thumbnail_total_frames = Long()
    rendered_file = Object(_EsRenderedFile)
    tags = Keyword(multi=True)
    magic_file_type = Keyword()
    tika_language = Keyword()
    detected_language = Keyword()
    translations = Object(_EsTranslatedLanguage, multi=True)
    is_spam = Boolean()
    tika_file_type = Keyword()
    archives = Keyword(multi=True)
    tika_meta = Object(_EsTikaMeta)
    tika_handled_by = Keyword()
    attachments = Object(_EsAttachment, multi=True)
    recursion_depth = Long()
    summary = Text(
        term_vector="with_positions_offsets",
        fields={
            "ngram": Text(
                term_vector="with_positions_offsets", analyzer="ngram_analyzer"
            ),
        },
    )
    image_description = Text(
        term_vector="with_positions_offsets",
        fields={
            "ngram": Text(
                term_vector="with_positions_offsets", analyzer="ngram_analyzer"
            ),
        },
    )
    embeddings = Nested(_EsEmbedding)
    trufflehog_secrets = Object(_EsSecret, multi=True)
    ripsecrets_secrets = Object(_EsSecret, multi=True)
    imap = Object(_EsImapInfo)
    flagged = Boolean()
    seen = Boolean()

    class Meta:  # pylint: disable=too-few-public-methods
        dynamic_templates = MetaField(
            [
                {
                    "strings": {
                        "match_mapping_type": "string",
                        "mapping": {
                            "type": "text",
                            "term_vector": "with_positions_offsets",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    }
                }
            ]
        )

    class Index:  # pylint: disable=too-few-public-methods

        name = "file"
        settings = {
            "number_of_shards": settings.es_number_of_shards,
            "number_of_replicas": settings.es_number_of_replicas,
            # tika_meta produces a lot of sub fields:
            # hence, we have to increase the limit here
            # ref: https://www.elastic.co/guide/en/elasticsearch/reference/master/mapping-settings-limit.html  # noqa: E501, B950 # pylint: disable=line-too-long
            "index.mapping.total_fields.limit": 9999999,
            "index.max_ngram_diff": 3,
            "analysis": {
                "analyzer": {
                    "ngram_analyzer": {"tokenizer": "ngram"},
                    "path_analyzer": {"tokenizer": "path"},
                },
                "tokenizer": {
                    "ngram": {
                        "type": "ngram",
                        "min_gram": 6,
                        "max_gram": 6,
                        "token_chars": ["letter", "digit", "symbol", "punctuation"],
                    },
                    "path": {
                        "type": "path_hierarchy",
                    },
                },
            },
        }


class TreePathsNode(BaseModel):
    """A node in the file path tree.

    Attributes:
        full_path: Absolute path of the node (directory or file).
        file_count: Total number of descendant files under this path.
        file_id: Set only when the node is a leaf file (not a directory).
        unseen_count: Number of unseen descendant files, excluding the node
            itself when is_unseen is True.
        is_unseen: Whether the file at this node is unseen (leaf nodes only).
        flagged_count: Number of flagged descendant files, excluding the node
            itself when is_flagged is True.
        is_flagged: Whether the file at this node is flagged (leaf nodes only).
    """

    full_path: FilePurePath
    file_count: int
    file_id: str | None = None
    unseen_count: int = 0
    is_unseen: bool = False
    flagged_count: int = 0
    is_flagged: bool = False


class TreePathsResult(BaseModel):
    """Result of a paginated tree path query.

    Attributes:
        nodes: The tree path nodes for this page.
        next_page_cursor: Opaque cursor for fetching the next page, or None
            when all pages have been returned.
        root_stats: Aggregate counts for the virtual root node (total files,
            unseen and flagged across the whole query).  Only populated when
            the request targets the root path (``tree_node_directory_path="/"``).
    """

    nodes: list[TreePathsNode]
    next_page_cursor: str | None = None
    root_stats: TreePathsNode | None = None


TERMS_STAT_REGISTRY = discover_stats(File, TermsStat)
HISTOGRAM_STAT_REGISTRY = discover_stats(File, HistogramStat)

# Maximum number of distinct group values returned by the terms sub-aggregation
# inside grouped histogram queries (date and number variants).  Capped here so
# the three call sites stay in sync; raise this value to expose more groups.
GROUP_SUB_AGG_SIZE = 100

EMAIL_EXTENSIONS = [
    ".eml",
]
# see /etc/mime.types
EMAIL_MIMETYPES = ["message/rfc822"]


class FileRepository(BaseEsRepository[_EsFile, File]):
    def __init__(
        self,
        query_builder: QueryBuilder,
        pubsub_service: PubSubService,
        search_factory: (
            Callable[[QueryParameters, bool], Search[_EsFile]] | None
        ) = None,
    ):
        super().__init__(query_builder, pubsub_service)
        self._search_factory = search_factory

    def _get_search_by_query(
        self,
        query: QueryParameters,
        full_highlight_context: bool = False,
    ) -> Search[_EsFile]:
        if self._search_factory is not None:
            return self._search_factory(query, full_highlight_context)
        return super()._get_search_by_query(query, full_highlight_context)

    @property
    def _object_type(self) -> type[File]:
        return File

    @property
    def _document_type(self) -> type[_EsFile]:
        return _EsFile

    @staticmethod
    def _bucket_key(bucket: Any) -> str:
        """Return the display key for a date-histogram bucket."""
        return str(
            bucket["key_as_string"]
            if hasattr(bucket, "key_as_string")
            else bucket["key"]
        )

    @staticmethod
    def get_aggr(
        result: Response[_EsFile], key_nest: list[str], default: Any = 0
    ) -> Any:
        """Accesses nested aggregate data from a response object."""
        res: Any = result.aggregations
        for key in key_nest:
            if key not in res:
                return default
            res = res[key]
        # there's no case right now where we want null/None instead of default values right now.
        # this also prevents dataclass validation errors for int since None != 0
        return res if res is not None else default

    def get_stat_terms(
        self, query: QueryParameters, stat: str, size: int = 5
    ) -> TermsStatistics:
        if stat not in TERMS_STAT_REGISTRY:
            raise FileRepositoryException(f"Unknown terms stat: {stat!r}")

        defn = TERMS_STAT_REGISTRY[stat]
        agg_name = f"all_{stat.replace('.', '_')}"

        search = self._get_search_by_query(query=query)
        search = search[0:0]  # do not fetch hits
        search = search.extra(track_total_hits=True)
        missing = {} if isinstance(defn, BooleanTermsStat) else {"missing": "(none)"}
        search.aggs.metric(agg_name, "terms", field=stat, size=size, **missing)

        result = self._execute_search_with_query(search=search, query=query)

        stats = TermsStatistics(
            stat=stat,
            data=[],
            total_no_of_files=result.hits.total.value,  # type: ignore[attr-defined]
            key=stat,
        )
        for bucket in self.get_aggr(result, [agg_name, "buckets"], []):
            name = str(bucket["key"])
            if defn.transform is not None:
                name = defn.transform(name)
            stats.data.append(
                StatisticsEntry(name=name, hits_count=int(bucket["doc_count"]))
            )
        return stats

    def get_stat_histogram(self, query: QueryParameters, stat: str) -> TermsStatistics:
        stat_defn = HISTOGRAM_STAT_REGISTRY.get(stat)
        if stat_defn is None:
            raise FileRepositoryException(f"Unknown histogram stat: {stat!r}")
        if isinstance(stat_defn, DateHistogramStat):
            return self._get_stat_date_histogram(query, stat)
        return self._get_stat_number_histogram(query, stat)

    def _get_stat_date_histogram(
        self, query: QueryParameters, stat: str
    ) -> TermsStatistics:
        agg_name = f"all_{stat.replace('.', '_')}"

        search = self._get_search_by_query(query=query)
        search = search[0:0]  # do not fetch hits
        search.aggs.metric("total_no_of_files", "value_count", field=stat)
        search.aggs.metric(agg_name, "auto_date_histogram", field=stat, buckets=24)
        search.aggs.metric("min_val", "min", field=stat)
        search.aggs.metric("max_val", "max", field=stat)

        result = self._execute_search_with_query(search=search, query=query)

        min_val = self.get_aggr(result, ["min_val", "value"], default=None)
        max_val = self.get_aggr(result, ["max_val", "value"], default=None)

        stats = TermsStatistics(
            stat=stat,
            data=[],
            total_no_of_files=self.get_aggr(
                result, ["total_no_of_files", "value"], default=0
            ),
            key=stat,
            min_value=float(min_val) if min_val is not None else None,
            max_value=float(max_val) if max_val is not None else None,
        )
        for bucket in self.get_aggr(result, [agg_name, "buckets"], []):
            stats.data.append(
                StatisticsEntry(
                    name=self._bucket_key(bucket), hits_count=int(bucket["doc_count"])
                )
            )
        return stats

    def _extract_sub_groups(
        self, bucket: Any, sub_agg_name: str, terms_defn: TermsStat
    ) -> dict[str, int]:
        """Parse a histogram bucket's terms sub-aggregation into a group→count map."""
        groups: dict[str, int] = {}
        for sub_bucket in (
            bucket[sub_agg_name]["buckets"] if sub_agg_name in bucket else []
        ):
            group_name = str(sub_bucket["key"])
            if terms_defn.transform is not None:
                group_name = terms_defn.transform(group_name)
            groups[group_name] = int(sub_bucket["doc_count"])
        return groups

    def get_stat_histogram_grouped(
        self, query: QueryParameters, stat: str, group_by: str
    ) -> GroupedHistogramStatistics:
        stat_defn = HISTOGRAM_STAT_REGISTRY.get(stat)
        if stat_defn is None:
            raise FileRepositoryException(f"Unknown histogram stat: {stat!r}")
        if group_by not in TERMS_STAT_REGISTRY:
            raise FileRepositoryException(f"Unknown terms stat: {group_by!r}")
        if isinstance(stat_defn, DateHistogramStat):
            return self._get_stat_date_histogram_grouped(query, stat, group_by)
        return self._get_stat_number_histogram_grouped(query, stat, group_by)

    def _get_stat_date_histogram_grouped(
        self, query: QueryParameters, stat: str, group_by: str
    ) -> GroupedHistogramStatistics:
        terms_defn = TERMS_STAT_REGISTRY[group_by]

        agg_name = f"grouped_{stat.replace('.', '_')}"
        sub_agg_name = f"by_{group_by.replace('.', '_')}"

        search = self._get_search_by_query(query=query)
        search = search[0:0]
        search.aggs.metric("total_no_of_files", "value_count", field=stat)
        search.aggs.metric(agg_name, "auto_date_histogram", field=stat, buckets=24)
        missing = (
            {} if isinstance(terms_defn, BooleanTermsStat) else {"missing": "(none)"}
        )
        search.aggs[agg_name].metric(
            sub_agg_name,
            "terms",
            field=group_by,
            size=GROUP_SUB_AGG_SIZE,
            **missing,
        )
        search.aggs.metric("min_val", "min", field=stat)
        search.aggs.metric("max_val", "max", field=stat)

        result = self._execute_search_with_query(search=search, query=query)

        min_val = self.get_aggr(result, ["min_val", "value"], default=None)
        max_val = self.get_aggr(result, ["max_val", "value"], default=None)

        grouped = GroupedHistogramStatistics(
            stat=stat,
            group_by=group_by,
            key=stat,
            histogram_type="date",
            data=[],
            total_no_of_files=self.get_aggr(result, ["total_no_of_files", "value"], 0),
            min_value=float(min_val) if min_val is not None else None,
            max_value=float(max_val) if max_val is not None else None,
        )
        for bucket in self.get_aggr(result, [agg_name, "buckets"], []):
            grouped.data.append(
                GroupedStatisticsEntry(
                    name=self._bucket_key(bucket),
                    groups=self._extract_sub_groups(bucket, sub_agg_name, terms_defn),
                    hits_count=int(bucket["doc_count"]),
                )
            )
        return grouped

    def _get_stat_number_histogram(
        self, query: QueryParameters, stat: str
    ) -> TermsStatistics:
        agg_name = f"all_{stat.replace('.', '_')}"

        # First query: get min + max + count to compute interval
        search = self._get_search_by_query(query=query)
        search = search[0:0]
        search.aggs.metric("min_val", "min", field=stat)
        search.aggs.metric("max_val", "max", field=stat)
        search.aggs.metric("total_no_of_files", "value_count", field=stat)

        result = self._execute_search_with_query(search=search, query=query)
        min_val = self.get_aggr(result, ["min_val", "value"], default=None)
        max_val = self.get_aggr(result, ["max_val", "value"], default=None)
        total = int(self.get_aggr(result, ["total_no_of_files", "value"], default=0))

        if min_val is None or max_val is None:
            return TermsStatistics(
                stat=stat,
                data=[],
                total_no_of_files=total,
                key=stat,
                min_value=None,
                max_value=None,
            )

        if min_val == max_val:
            return TermsStatistics(
                stat=stat,
                data=[StatisticsEntry(name=str(min_val), hits_count=total)],
                total_no_of_files=total,
                key=stat,
                min_value=float(min_val),
                max_value=float(max_val),
            )

        interval = max(1, round((max_val - min_val) / 24))

        # Second query: histogram aggregation with computed interval
        search2 = self._get_search_by_query(query=query)
        search2 = search2[0:0]
        search2.aggs.metric(agg_name, "histogram", field=stat, interval=interval)

        result2 = self._execute_search_with_query(search=search2, query=query)

        stats = TermsStatistics(
            stat=stat,
            data=[],
            total_no_of_files=total,
            key=stat,
            min_value=float(min_val),
            max_value=float(max_val),
        )
        for bucket in self.get_aggr(result2, [agg_name, "buckets"], []):
            stats.data.append(
                StatisticsEntry(
                    name=str(bucket["key"]), hits_count=int(bucket["doc_count"])
                )
            )
        return stats

    def _get_stat_number_histogram_grouped(
        self, query: QueryParameters, stat: str, group_by: str
    ) -> GroupedHistogramStatistics:
        terms_defn = TERMS_STAT_REGISTRY[group_by]

        agg_name = f"grouped_{stat.replace('.', '_')}"

        # First query: get min + max + count to compute interval
        search = self._get_search_by_query(query=query)
        search = search[0:0]
        search.aggs.metric("min_val", "min", field=stat)
        search.aggs.metric("max_val", "max", field=stat)
        search.aggs.metric("total_no_of_files", "value_count", field=stat)

        result = self._execute_search_with_query(search=search, query=query)
        min_val = self.get_aggr(result, ["min_val", "value"], default=None)
        max_val = self.get_aggr(result, ["max_val", "value"], default=None)
        total = int(self.get_aggr(result, ["total_no_of_files", "value"], default=0))

        if min_val is None or max_val is None:
            return GroupedHistogramStatistics(
                stat=stat,
                group_by=group_by,
                key=stat,
                histogram_type="number",
                data=[],
                total_no_of_files=total,
                min_value=None,
                max_value=None,
            )

        if min_val == max_val:
            # All documents share the same value — single bucket.
            # Run a flat terms aggregation to get the group breakdown.
            search = self._get_search_by_query(query=query)
            search = search[0:0]
            missing = (
                {}
                if isinstance(terms_defn, BooleanTermsStat)
                else {"missing": "(none)"}
            )
            search.aggs.metric(
                "groups",
                "terms",
                field=group_by,
                size=GROUP_SUB_AGG_SIZE,
                **missing,
            )
            return GroupedHistogramStatistics(
                stat=stat,
                group_by=group_by,
                key=stat,
                histogram_type="number",
                data=[
                    GroupedStatisticsEntry(
                        name=str(min_val),
                        groups=self._extract_sub_groups(
                            {
                                "groups": {
                                    "buckets": self.get_aggr(
                                        self._execute_search_with_query(
                                            search=search, query=query
                                        ),
                                        ["groups", "buckets"],
                                        [],
                                    )
                                }
                            },
                            "groups",
                            terms_defn,
                        ),
                        hits_count=total,
                    )
                ],
                total_no_of_files=total,
                min_value=float(min_val),
                max_value=float(max_val),
            )

        # Second query: histogram + terms sub-aggregation
        search = self._get_search_by_query(query=query)
        search = search[0:0]
        search.aggs.metric(
            agg_name,
            "histogram",
            field=stat,
            interval=max(1, round((max_val - min_val) / 24)),
        )
        missing = (
            {} if isinstance(terms_defn, BooleanTermsStat) else {"missing": "(none)"}
        )
        search.aggs[agg_name].metric(
            f"by_{group_by.replace('.', '_')}",
            "terms",
            field=group_by,
            size=GROUP_SUB_AGG_SIZE,
            **missing,
        )

        result2 = self._execute_search_with_query(search=search, query=query)

        grouped = GroupedHistogramStatistics(
            stat=stat,
            group_by=group_by,
            key=stat,
            histogram_type="number",
            data=[],
            total_no_of_files=total,
            min_value=float(min_val),
            max_value=float(max_val),
        )
        for bucket in self.get_aggr(result2, [agg_name, "buckets"], []):
            grouped.data.append(
                GroupedStatisticsEntry(
                    name=str(bucket["key"]),
                    groups=self._extract_sub_groups(
                        bucket, f"by_{group_by.replace('.', '_')}", terms_defn
                    ),
                    hits_count=int(bucket["doc_count"]),
                )
            )
        return grouped

    def get_all_tags(self) -> list[str]:
        """Get all tags in the database."""
        search = self._document_type.search(using=self._elasticsearch)
        tags_aggregation: Agg[_EsFile] = A(
            "terms", field="tags", order={"_key": "asc"}, size=1_000
        )
        search.aggs.bucket("all_tags", tags_aggregation)
        search = search[0:0]  # do not fetch hits
        result = search.execute()  # pylint: disable=no-member

        all_tags: list[str] = []
        for tag in result.aggregations.all_tags.buckets:
            all_tags.append(cast(str, tag.key))
        return all_tags

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def get_embedding_generator_by_knn(
        self,
        query: QueryParameters,
        embedding_vectors: Sequence[Sequence[float]],
        k: int,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[KnnSearchEmbedding, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search: Search[_EsFile] = self._document_type.search(using=self._elasticsearch)

        search = search.extra(
            pit={"id": query.query_id, "keep_alive": query.keep_alive}
        )

        search = search.index()  # Remove index: pit requests run against no index

        filter_query = Q(
            "query_string",
            query=self._query_builder.build(query),
            default_operator="AND",
            # Be lenient because the index-level default fields are set dynamically
            # (index.query.default_field). Those fields can span multiple data types
            # (text, numeric, boolean, date), and query_string parsing would otherwise
            # fail when a term is incompatible with a field's type.
            lenient=True,
        )

        for q in embedding_vectors:
            search = search.knn(  # pylint: disable=no-member
                field="embeddings.vector",
                k=k,
                num_candidates=k * KNN_CANDIDATES_FACTOR,
                query_vector=list(q),
                filter=filter_query,
                inner_hits={"_source": True, "fields": ["embeddings.text"], "size": k},
            )

        def page_handler(result: Response[_EsFile]):
            for es_file in result.hits:
                es_embedding: _EsEmbedding
                for es_embedding in es_file.meta.inner_hits["embeddings"]:
                    yield KnnSearchEmbedding(
                        file_id=UUID(es_file.meta.id),
                        file_score=(
                            es_file.meta.score
                            if es_file.meta.score is not None
                            else 0.0
                        ),
                        text_score=(
                            es_embedding.meta.score
                            if es_embedding.meta.score is not None
                            else 0.0
                        ),
                        text=str(es_embedding.text),
                    )

        yield from self._paginate_search(
            search=search,
            query=query,
            sort_params=sort_params,
            pagination_params=pagination_params,
            per_page_callback=page_handler,
        )

    def get_full_paths_by_query(
        self,
        query: QueryParameters,
        tree_node_directory_path: str,
        after: str | None = None,
    ) -> TreePathsResult:
        """Return the direct children of ``tree_node_directory_path`` for tree browsing.

        Uses a single ``terms`` aggregation with an ``include`` regex so ES filters
        bucket keys natively at segment level.  The regex matches paths that are exactly
        one component deeper than ``tree_node_directory_path``, which are the direct
        children.  This avoids the previous composite pagination loop that had to fetch
        O(total_path_tokens / page_size) pages just to find direct children.

        Cursor pagination works via a ``range`` filter on ``full_path.tree``.  Because
        the field is multi-value, the filter admits a document when *any* token exceeds
        the cursor.  This means the cursor bucket itself may be returned by ES (its
        deeper-path tokens satisfy the range); it is excluded explicitly after the
        aggregation.
        """
        # Build a Java-compatible regex matching direct children only.
        # re.escape covers all Java regex metacharacters that appear in file paths.
        include_regex = re.escape(tree_node_directory_path) + "/[^/]+"

        dir_aggregation: Agg[_EsFile] = A(
            "terms",
            field="full_path.tree",
            include=include_regex,
            # +1 to detect whether more pages exist. When `after` is set the
            # range filter on the multi-value full_path.tree field re-admits
            # the cursor bucket (its leaf token cursor/doc exceeds the cursor),
            # which is then excluded post-aggregation. An extra +1 covers that
            # slot so the "is there a next page?" check still sees N+1 results.
            size=TREE_PATH_MAX_ELEMENT_COUNT + 1 + (1 if after is not None else 0),
            order={"_key": "asc"},  # alphabetical ensures stable cursor pagination
        )
        dir_aggregation.bucket(
            "first_hit",
            A(
                "top_hits",
                size=1,
                sort=[{"full_path.keyword": "asc"}],
                _source=["full_path", "seen", "flagged"],
            ),
        )
        dir_aggregation.bucket(
            "unseen",
            A("filter", filter=Q("term", seen=False)),
        )
        dir_aggregation.bucket(
            "flagged",
            A("filter", filter=Q("term", flagged=True)),
        )

        search = self._get_search_by_query(query=query)
        # Scope the aggregation to documents at or below the requested path.
        # The path_hierarchy tokenizer emits one token per path prefix, so a
        # term filter on full_path.tree restricts results to documents whose path
        # starts with tree_node_directory_path.  Root ("/") is skipped because the
        # "/" token is present on every document and the filter would be a no-op.
        if tree_node_directory_path != "/":
            search = search.filter(
                "term", **{"full_path.tree": tree_node_directory_path}
            )
        # Cursor pagination: skip documents whose full_path.tree tokens all precede
        # the cursor.  The range is satisfied when any token exceeds it, which
        # correctly includes documents contributing to unseen child buckets.
        if after is not None:
            search = search.filter("range", **{"full_path.tree": {"gt": after}})
        search.aggs.bucket("directory", dir_aggregation)
        # When querying the root, add global aggregations to compute the
        # virtual root node's totals directly in ES.  These run over all
        # documents that match the user's search query (no path filter is
        # applied at root level), giving exact counts without summing the
        # individual child buckets on the client.
        is_root = tree_node_directory_path == "/"
        if is_root:
            search.aggs.bucket("total_files", A("filter", filter=Q("match_all")))
            search.aggs.bucket(
                "total_unseen", A("filter", filter=Q("term", seen=False))
            )
            search.aggs.bucket(
                "total_flagged", A("filter", filter=Q("term", flagged=True))
            )
        search = search[0:0]  # do not fetch hits
        # Tree counts must always reflect the live index state, not the
        # query's point-in-time snapshot. Counts change when files are
        # flagged/seen outside of the PIT window, so we execute directly
        # against the index.
        result = search.using(self._elasticsearch).execute()

        # Exclude the cursor bucket in case it was re-admitted by the range filter.
        raw_buckets = [
            b for b in result.aggregations.directory.buckets if str(b.key) != after
        ]
        nodes = [
            self._build_tree_paths_node(
                key=str(b.key),
                doc_count=b.doc_count,
                first_hit_bucket=b.first_hit,
                unseen_bucket=b.unseen,
                flagged_bucket=b.flagged,
            )
            for b in raw_buckets[:TREE_PATH_MAX_ELEMENT_COUNT]
        ]
        next_cursor = (
            str(raw_buckets[TREE_PATH_MAX_ELEMENT_COUNT - 1].key)
            if len(raw_buckets) > TREE_PATH_MAX_ELEMENT_COUNT
            else None
        )
        root_stats: TreePathsNode | None = None
        if is_root:
            root_stats = TreePathsNode(
                full_path=FilePurePath("/"),
                file_count=cast(int, result.aggregations.total_files.doc_count),
                unseen_count=cast(int, result.aggregations.total_unseen.doc_count),
                flagged_count=cast(int, result.aggregations.total_flagged.doc_count),
            )
        return TreePathsResult(
            nodes=nodes, next_page_cursor=next_cursor, root_stats=root_stats
        )

    def get_flat_files_by_query(
        self,
        query: QueryParameters,
        after: str | None = None,
        filename: str | None = None,
    ) -> TreePathsResult:
        """Return a paginated flat list of all leaf files matching the query.

        Uses a ``terms`` aggregation on ``full_path.keyword`` so each bucket is exactly
        one file.  Used by the folder-view filter box to search files by name across the
        whole index.

        Cursor pagination works via a ``range`` filter on ``full_path.keyword``. Because
        the field is single-value, the filter is unambiguous — the cursor bucket is
        never readmitted (unlike the multi-value ``full_path.tree`` field used by the
        tree variant).

        If ``filename`` is provided, an additional wildcard filter is applied on
        ``full_path.keyword`` to restrict results to files whose path contains the given
        string.
        """
        dir_aggregation: Agg[_EsFile] = A(
            "terms",
            field="full_path.keyword",
            size=TREE_PATH_MAX_ELEMENT_COUNT
            + 1,  # +1 to detect whether more pages exist
            order={"_key": "asc"},
        )
        dir_aggregation.bucket(
            "first_hit",
            A(
                "top_hits",
                size=1,
                sort=[{"full_path.keyword": "asc"}],
                _source=["full_path", "seen", "flagged"],
            ),
        )
        dir_aggregation.bucket(
            "unseen",
            A("filter", filter=Q("term", seen=False)),
        )
        dir_aggregation.bucket(
            "flagged",
            A("filter", filter=Q("term", flagged=True)),
        )

        search = self._get_search_by_query(query=query)
        if after is not None:
            search = search.filter("range", **{"full_path.keyword": {"gt": after}})
        if filename:
            search = search.filter("wildcard", **{"full_path.keyword": f"*{filename}*"})
        search.aggs.bucket("directory", dir_aggregation)
        search = search[0:0]  # do not fetch hits
        result = search.using(self._elasticsearch).execute()

        raw_buckets = list(result.aggregations.directory.buckets)
        nodes = [
            self._build_tree_paths_node(
                key=str(b.key),
                doc_count=b.doc_count,
                first_hit_bucket=b.first_hit,
                unseen_bucket=b.unseen,
                flagged_bucket=b.flagged,
            )
            for b in raw_buckets[:TREE_PATH_MAX_ELEMENT_COUNT]
        ]
        next_cursor = (
            str(raw_buckets[TREE_PATH_MAX_ELEMENT_COUNT - 1].key)
            if len(raw_buckets) > TREE_PATH_MAX_ELEMENT_COUNT
            else None
        )
        return TreePathsResult(nodes=nodes, next_page_cursor=next_cursor)

    def get_spine_by_path(
        self,
        query: QueryParameters,
        full_path: str,
    ) -> TreePathsResult:
        """Return one TreePathsNode per path segment from the first non-root ancestor
        down to full_path (inclusive), in root-to-leaf order, plus root aggregations.

        Uses a single terms aggregation with an include filter so only the exact
        ancestor paths are returned — no pagination needed.  Global filter aggregations
        are added to compute the virtual root node's totals in the same ES request, so
        the caller never has to sum children client-side.
        """
        target = PurePosixPath(full_path)
        spine_paths = [
            str(p) for p in reversed(list(target.parents)) if str(p) not in ("/", "//")
        ] + [full_path]

        if not spine_paths:
            return TreePathsResult(nodes=[], root_stats=None)

        terms_agg: Agg[_EsFile] = A(
            "terms",
            field="full_path.tree",
            include=spine_paths,
            size=len(spine_paths),
        )
        terms_agg.bucket(
            "first_hit",
            A(
                "top_hits",
                size=1,
                sort=[{"full_path.keyword": "asc"}],
                _source=["full_path", "seen", "flagged"],
            ),
        )
        terms_agg.bucket("unseen", A("filter", filter=Q("term", seen=False)))
        terms_agg.bucket("flagged", A("filter", filter=Q("term", flagged=True)))

        search = self._get_search_by_query(query=query)
        search.aggs.bucket("spine", terms_agg)
        search.aggs.bucket("total_files", A("filter", filter=Q("match_all")))
        search.aggs.bucket("total_unseen", A("filter", filter=Q("term", seen=False)))
        search.aggs.bucket("total_flagged", A("filter", filter=Q("term", flagged=True)))
        search = search[0:0]
        result = search.using(self._elasticsearch).execute()

        nodes = [
            self._build_tree_paths_node(
                key=str(bucket.key),
                doc_count=bucket.doc_count,
                first_hit_bucket=bucket.first_hit,
                unseen_bucket=bucket.unseen,
                flagged_bucket=bucket.flagged,
            )
            for bucket in result.aggregations.spine.buckets
        ]
        nodes.sort(key=lambda n: str(n.full_path).count("/"))
        if not any(str(n.full_path) == full_path for n in nodes):
            return TreePathsResult(nodes=[], root_stats=None)
        root_stats = TreePathsNode(
            full_path=FilePurePath("/"),
            file_count=cast(int, result.aggregations.total_files.doc_count),
            unseen_count=cast(int, result.aggregations.total_unseen.doc_count),
            flagged_count=cast(int, result.aggregations.total_flagged.doc_count),
        )
        return TreePathsResult(nodes=nodes, root_stats=root_stats)

    @staticmethod
    def _build_tree_paths_node(
        key: str,
        doc_count: int,
        first_hit_bucket: Any,
        unseen_bucket: Any,
        flagged_bucket: Any,
    ) -> TreePathsNode:
        """Build a TreePathsNode from pre-extracted aggregation bucket fields."""
        dirpath = FilePurePath(key)
        file_id = None
        is_unseen = False
        is_flagged = False
        hits = first_hit_bucket.hits.hits
        if hits and str(hits[0]["_source"]["full_path"]) == key:
            file_id = hits[0]["_id"]
            try:
                is_unseen = not hits[0]["_source"]["seen"]
            except KeyError:
                pass
            try:
                is_flagged = bool(hits[0]["_source"]["flagged"])
            except KeyError:
                pass
        return TreePathsNode(
            full_path=dirpath,
            file_count=cast(int, doc_count) - (1 if file_id is not None else 0),
            file_id=file_id,
            unseen_count=cast(int, unseen_bucket.doc_count) - (1 if is_unseen else 0),
            is_unseen=is_unseen,
            flagged_count=cast(int, flagged_bucket.doc_count)
            - (1 if is_flagged else 0),
            is_flagged=is_flagged,
        )

    @staticmethod
    def _parse_tree_bucket(path: Any) -> TreePathsNode:
        """Build a TreePathsNode from a single composite aggregation bucket."""
        return FileRepository._build_tree_paths_node(
            key=str(path.key.path),
            doc_count=path.doc_count,
            first_hit_bucket=path.first_hit,
            unseen_bucket=path.unseen,
            flagged_bucket=path.flagged,
        )

    def _build_email_filter(self) -> Query:
        email_filters = []

        if EMAIL_MIMETYPES:
            email_filters.append(Q("terms", tika_file_type=EMAIL_MIMETYPES))

        if EMAIL_EXTENSIONS:
            email_filters.append(Q("terms", extension=EMAIL_EXTENSIONS))

        return Q("bool", should=email_filters, minimum_should_match=1)

    def get_emails(
        self,
        query: QueryParameters,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[File, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search: Search[_EsFile] = (
            self._document_type.search(using=self._elasticsearch)
            .extra(pit={"id": query.query_id, "keep_alive": query.keep_alive})
            .index()
        )

        filter_query = self._build_email_filter()

        if query.search_string:
            query_string = Q(
                "query_string",
                query=self._query_builder.build(query),
                default_operator="AND",
                lenient=True,
            )

            search = search.query(
                Q(
                    "bool",
                    must=[
                        filter_query,
                        query_string,
                    ],
                )
            )
        else:
            search = search.query(
                Q(
                    "bool",
                    must=[filter_query],
                )
            )

        def page_handler(result: Response[_EsFile]):
            for hit in result.hits:
                yield self._document_to_object(hit)

        yield from self._paginate_search(
            search=search,
            query=query,
            sort_params=sort_params,
            pagination_params=pagination_params,
            per_page_callback=page_handler,
        )

    def get_emails_from_imap_info(self, imap_info: ImapInfo) -> list[UUID]:

        search: Search[_EsFile] = self._document_type.search(using=self._elasticsearch)

        email_filter = self._build_email_filter()

        imap_filter = Q(
            "bool",
            must=[
                Q("term", imap__uid=imap_info.uid),
                Q("term", imap__folder__keyword=str(imap_info.folder)),
            ],
        )

        final_query = Q(
            "bool",
            must=[email_filter, imap_filter],
        )

        search = search.query(final_query).source(False)
        result = search.execute()

        return [UUID(hit.meta.id) for hit in result.hits]
