"""Repository that handles file persistance operation."""

from __future__ import annotations

import enum
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError
from pathlib import PurePath
from typing import Any, Callable, Generator, cast
from urllib.error import URLError
from uuid import UUID

from elasticsearch_dsl import (  # type: ignore[import-untyped]
    A,
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
from elasticsearch_dsl.response import Response  # type: ignore[import-untyped]
from libretranslatepy import LibreTranslateAPI  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, computed_field, field_validator

from common.file.file_statistics import (
    StatisticsEntry,
    StatisticsGeneric,
    StatisticsSummary,
)
from common.models.es_repository import (
    BaseEsRepository,
    PaginationParameters,
    SortingParameters,
)
from common.services.query_builder import QueryParameters
from common.settings import settings
from common.task_object.task_object import RepositoryTaskObject, _EsTaskDocument
from common.utils.object_id_str import ObjectIdStr
from common.utils.unique_list import unique_list

logger = logging.getLogger(__name__)

PATH_SEPARATOR = "/"
PATH_ROOT = "//"
TREE_PATH_MAX_ELEMENT_COUNT = 100
TREE_PATH_BUCKET_SIZE = TREE_PATH_MAX_ELEMENT_COUNT + 1
ES_RESERVED_PATTERN = re.compile(r"([\".?+*|{}\][\\()])")
KNN_CANDIDATES_FACTOR = 5  # how many more candidates to select for KNN per shared


class FileNotFoundException(Exception):
    pass


class Embedding(BaseModel):
    vector: list[float]
    text: str


class KnnSearchEmbedding(BaseModel):
    file_id: UUID
    file_score: float
    text_score: float
    text: str


class _EsEmbedding(InnerDoc):
    vector = DenseVector(dims=settings.llm_embedding_dimensions, similarity="cosine")
    text = Text(term_vector="with_positions_offsets")


class LibretranslateTranslatedLanguage(BaseModel):
    confidence: float
    language: str
    text: str


class _EsLibretranslateTranslatedLanguage(InnerDoc):
    confidence = Float()
    language = Keyword()
    text = Text(term_vector="with_positions_offsets")


LibreTranslateTranslations = list[LibretranslateTranslatedLanguage]


class _EsLibreTranslateTranslations(InnerDoc):
    """A wrapper for all available libretranslate languages."""

    try:
        LIBRETRANSLATE_SUPPORTED_LANGUAGES = [
            lang["code"]
            # Since this is run at import-time, we can not use the dependency module here
            # to fetch a LibreTranslateAPI instance.
            for lang in LibreTranslateAPI(str(settings.libretranslate_host)).languages()
        ]
    except (URLError, JSONDecodeError):
        # Raised when libretranslate isn't available, for example while running unit-tests
        LIBRETRANSLATE_SUPPORTED_LANGUAGES = [settings.translate_target]

    for lang in LIBRETRANSLATE_SUPPORTED_LANGUAGES:
        locals()[lang] = Object(_EsLibretranslateTranslatedLanguage)


FILE_SHORT_NAME_CONTENT_SUFFIX = ".content.txt"

TAG_LEN_MIN = 1
TAG_LEN_MAX = 25


class File(RepositoryTaskObject):
    storage_id: ObjectIdStr
    content: str | None = None
    content_truncated: bool = False
    full_name: PurePath

    @computed_field  # type: ignore[misc]
    @property
    def deduplication_fingerprint(self) -> str:
        file_data_hash = hashlib.sha256()
        file_data_hash.update(str(self.full_name).encode())
        file_data_hash.update(self.sha256.encode())
        return file_data_hash.hexdigest()

    @computed_field  # type: ignore[misc]
    @property
    def full_path(self) -> PurePath:
        if isinstance(self.full_name, str):
            return PurePath(f"//{self.source}/{self.full_name}")
        return PurePath(f"//{self.source}") / self.full_name

    @computed_field  # type: ignore[misc]
    @property
    def short_name(self) -> str:
        return self.full_name.name

    @computed_field  # type: ignore[misc]
    @property
    def short_name_content(self) -> str:
        return f"{self.short_name}{FILE_SHORT_NAME_CONTENT_SUFFIX}"

    @computed_field  # type: ignore[misc]
    @property
    def extension(self) -> str:
        return self.full_name.suffix

    source: str
    sha256: str
    uploaded_datetime: datetime = Field(default_factory=datetime.now)
    size: int
    thumbnail_file_id: ObjectIdStr | None = None
    preview_file_id: ObjectIdStr | None = None
    exclude_from_archives: bool = False
    tags: list[str] = []
    magic_file_type: str | None = None
    tika_language: str | None = None
    libretranslate_language: str | None = None
    libretranslate_translations: LibreTranslateTranslations = Field(
        default_factory=LibreTranslateTranslations
    )
    is_spam: bool | None = None
    tika_file_type: str | None = None
    archives: list[str] = []
    tika_meta: dict[str, Any] = {}
    has_attachments: bool | None = None
    summary: str | None = None
    embeddings: list[Embedding] = []

    @field_validator("tags")
    @classmethod
    def check_tag_len(cls, tags: list[str]) -> list[str]:
        for tag in tags:
            tag_len = len(tag)
            if tag_len < TAG_LEN_MIN or tag_len > TAG_LEN_MAX:
                raise ValueError(
                    f"len('{tag}') must be {TAG_LEN_MIN} < {len(tag)} < {TAG_LEN_MAX}"
                )
        return tags

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, tags: list[str]) -> list[str]:
        return unique_list(tags)

    @field_validator("archives")
    @classmethod
    def unique_archives(cls, archives: list[str]) -> list[str]:
        return unique_list(archives)

    def to_es_dict(self) -> dict:
        es_dict = super().to_es_dict()
        # expand translations to object
        libretranslate_translations = es_dict["libretranslate_translations"]
        es_dict["libretranslate_translations"] = {}
        for translation in libretranslate_translations:
            es_dict["libretranslate_translations"][
                translation["language"]
            ] = translation

        return es_dict


class _EsFile(_EsTaskDocument):
    storage_id = Keyword()
    content = Text(
        term_vector="with_positions_offsets",
        fields={
            "ngram": Text(
                term_vector="with_positions_offsets", analyzer="ngram_analyzer"
            ),
        },
    )
    content_truncated = Boolean()
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
    sha256 = Keyword()
    uploaded_datetime = Date()
    size = Long()
    thumbnail_file_id = Keyword()
    preview_file_id = Keyword()
    exclude_from_archives = Boolean()
    tags = Keyword(multi=True)
    magic_file_type = Keyword()
    tika_language = Keyword()
    libretranslate_language = Keyword()
    libretranslate_translations = Object(_EsLibreTranslateTranslations)
    is_spam = Boolean()
    tika_file_type = Keyword()
    archives = Keyword(multi=True)
    tika_meta = Object()
    has_attachments = Boolean()
    summary = Text(
        term_vector="with_positions_offsets",
        fields={
            "ngram": Text(
                term_vector="with_positions_offsets", analyzer="ngram_analyzer"
            ),
        },
    )
    embeddings = Nested(_EsEmbedding)

    def to_es_dict(self) -> dict:
        es_dict = super().to_es_dict()
        # merge all translations into a list
        libretranslate_translations = es_dict.get("libretranslate_translations", {})
        es_dict["libretranslate_translations"] = list(
            libretranslate_translations.values()
        )

        return es_dict

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
        """The index."""

        name = "file"
        settings = {
            # we disable data replication, since we run a single node cluster
            # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/high-availability-cluster-small-clusters.html # noqa: E501, B950 # pylint: disable=line-too-long
            "number_of_replicas": 0,
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
    """Node of tree of paths."""

    full_path: PurePath
    file_count: int


class Stat(enum.Enum):
    # SUMMARY = "summary"  # this is separate of the Stat enum -> too unconventional
    TAGS = "tags"  # though not entirely generic, it's partially so.
    SOURCES = "sources"
    STATES = "states"
    EXTENSIONS = "extensions"
    FILE_TYPE_TIKA = "file_type_tika"
    FILE_TYPE_MAGIC = "file_type_magic"
    LANGUAGE_TIKA = "language_tika"
    LANGUAGE_LIBRETRANSLATE = "language_libretranslate"
    IS_SPAM = "is_spam"


class FileRepository(BaseEsRepository[_EsFile, File]):
    @property
    def _object_type(self) -> type[File]:
        return File

    @property
    def _document_type(self) -> type[_EsFile]:
        return _EsFile

    @staticmethod
    def get_aggr(result: Response, key_nest: list[str], default: Any = 0) -> Any:
        """Accesses nested aggregate data from a response object."""
        res = result.aggregations
        for key in key_nest:
            if key not in res:
                return default
            res = res[key]
        # there's no case right now where we want null/None instead of default values right now.
        # this also prevents dataclass validation errors for int since None != 0
        return res if res is not None else default

    def _prep_search(self, query: QueryParameters) -> Search:
        search = self._document_type.search(using=self._elasticsearch)
        query_string = self._query_builder.build(query)
        search = search.query(
            "query_string",
            query=query_string,
            default_field="*",
            default_operator="AND",
        )
        return search[0:0]

    def get_stat_generic(self, query: QueryParameters, stat: Stat) -> StatisticsGeneric:
        @dataclass
        class StatItem:
            args: list[str]
            kwargs: dict[str, Any]
            transforms: dict[str, Callable[[str], str]]

        search_dict = {
            Stat.TAGS: StatItem(
                args=["all_tags", "terms"],
                kwargs={"field": "tags", "size": 100},
                transforms={},
            ),
            Stat.SOURCES: StatItem(
                args=["all_sources", "terms"],
                kwargs={"field": "source", "size": 100},
                transforms={},
            ),
            Stat.STATES: StatItem(
                args=["all_states", "terms"],
                kwargs={"field": "state", "size": 100},
                transforms={},
            ),
            Stat.EXTENSIONS: StatItem(
                args=["all_extensions", "terms"],
                kwargs={"field": "extension", "size": 100},
                transforms={},
            ),
            Stat.FILE_TYPE_TIKA: StatItem(
                args=["all_file_type_tika", "terms"],
                kwargs={"field": "tika_file_type", "size": 100},
                transforms={},
            ),
            Stat.FILE_TYPE_MAGIC: StatItem(
                args=["all_file_type_magic", "terms"],
                kwargs={"field": "magic_file_type", "size": 100},
                transforms={},
            ),
            Stat.LANGUAGE_TIKA: StatItem(
                args=["all_language_tika", "terms"],
                kwargs={"field": "tika_language", "size": 100},
                transforms={},
            ),
            Stat.LANGUAGE_LIBRETRANSLATE: StatItem(
                args=["all_language_libretranslate", "terms"],
                kwargs={"field": "libretranslate_language", "size": 100},
                transforms={},
            ),
            Stat.IS_SPAM: StatItem(
                args=["all_is_spam", "terms"],
                kwargs={"field": "is_spam", "size": 100},
                transforms={"name": lambda s: str(bool(s)).lower()},
            ),
        }

        search = self._prep_search(query)
        search.aggs.metric(
            "total_no_of_files", "value_count", field="size"
        )  # required for % calculations
        search.aggs.metric(*search_dict[stat].args, **search_dict[stat].kwargs)
        result = search.execute()
        total_no_of_files = self.get_aggr(
            result, ["total_no_of_files", "value"], default=0
        )
        stats = StatisticsGeneric(
            stat=stat.value,
            data=[],
            total_no_of_files=total_no_of_files,
            key=search_dict[stat].kwargs["field"],
        )
        nest_key = search_dict[stat].args[0]
        for bucket in self.get_aggr(result, [nest_key, "buckets"], []):
            stat_entry = StatisticsEntry(
                name=bucket["key"], hits_count=bucket["doc_count"]
            )

            # apply special transforms like the name adjustment for IS_SPAM
            for stat_key, transformer in search_dict[stat].transforms.items():
                setattr(
                    stat_entry, stat_key, transformer(getattr(stat_entry, stat_key))
                )

            stats.data.append(stat_entry)
        return stats

    def get_stat_summary(self, query: QueryParameters) -> StatisticsSummary:
        search = self._prep_search(query)
        search.aggs.metric("avg_file_size", "avg", field="size")
        search.aggs.metric("max_file_size", "max", field="size")
        search.aggs.metric("min_file_size", "min", field="size")
        search.aggs.metric("total_no_of_files", "value_count", field="size")
        result = search.execute()
        return StatisticsSummary(
            avg_file_size=self.get_aggr(result, ["avg_file_size", "value"], default=0),
            max_file_size=self.get_aggr(result, ["max_file_size", "value"], default=0),
            min_file_size=self.get_aggr(result, ["min_file_size", "value"], default=0),
            total_no_of_files=self.get_aggr(
                result, ["total_no_of_files", "value"], default=0
            ),
        )

    def get_all_tags(self) -> list[str]:
        """Get all tags that are in the database."""
        search = self._document_type.search(using=self._elasticsearch)
        tags_aggregation = A(
            "terms",
            field="tags",
            order={"_key": "asc"},  # alphebetic order
        )
        search.aggs.bucket("all_tags", tags_aggregation)
        search = search[0:0]  # do not fetch hits
        search_result = search.execute()  # pylint: disable=no-member
        all_tags: list[str] = []
        for tag in search_result.aggregations.all_tags.buckets:
            all_tags.append(tag.key)
        return all_tags

    # pylint: disable=too-many-arguments
    def get_embedding_generator_by_knn(
        self,
        query: QueryParameters,
        embedding_vectors: list[list[float]],
        k: int,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[KnnSearchEmbedding, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search: Search = self._document_type.search(using=self._elasticsearch)

        query_q = Q(
            "query_string",
            query=self._query_builder.build(query),
            default_field="*",
            default_operator="AND",
        )

        for q in embedding_vectors:
            search = search.knn(
                field="embeddings.vector",
                k=k,
                num_candidates=k * KNN_CANDIDATES_FACTOR,
                query_vector=q,
                filter=query_q,
                inner_hits={"_source": True, "fields": ["embeddings.text"], "size": k},
            )

        def page_handler(result: Response):
            for es_file, hit in zip(result.hits, result.hits.hits):
                es_embedding: _EsEmbedding
                for es_embedding in hit.inner_hits.embeddings:
                    yield KnnSearchEmbedding(
                        file_id=es_file.meta.id,
                        file_score=es_file.meta.score,
                        text_score=es_embedding.meta.score,
                        text=es_embedding.text,
                    )

        yield from self._paginate_search(
            search, sort_params, pagination_params, page_handler
        )

    def get_full_paths_by_query(
        self, query: QueryParameters, tree_node_directory_path: str
    ) -> list[TreePathsNode]:
        """Generate the tree path structure for all matching files."""

        escaped_directory = re.sub(
            ES_RESERVED_PATTERN, r"\\\1", tree_node_directory_path
        )
        pattern_directory = escaped_directory + "/.+"
        pattern_contents = escaped_directory + "/[^/]+/.+"

        search: Search = self._document_type.search(using=self._elasticsearch)

        query_string = self._query_builder.build(query)
        search = search.query(
            "query_string", query=query_string, default_operator="AND"
        )

        dir_aggregation = A(
            "terms",
            size=TREE_PATH_BUCKET_SIZE,
            field="full_path.tree",
            order={"_key": "asc"},  # alphebetic order by path name
            include=pattern_directory,
            exclude=pattern_contents,
        )
        search.aggs.bucket("directory", dir_aggregation)
        search = search[0:0]  # do not fetch hits
        search_result = search.execute()

        nodes = []
        for path in search_result.aggregations.directory.buckets:
            dirpath = PurePath(str(path.key))
            nodes.append(
                TreePathsNode(full_path=dirpath, file_count=cast(int, path.doc_count))
            )

        return nodes

    # pylint:disable=duplicate-code
    def get_generator_by_tag(
        self,
        tag: str,
        pagination_params: PaginationParameters | None = None,
        sort_params: SortingParameters | None = None,
    ) -> Generator[File, None, None]:
        if sort_params is None:
            sort_params = SortingParameters()

        search = self._document_type.search(
            using=self._elasticsearch,
            index=self._index_name,
        )
        search = search.query("match", tags=tag)

        def page_handler(result: Response):
            for hit in result.hits:
                yield self._document_to_object(hit)

        yield from self._paginate_search(
            search, sort_params, pagination_params, page_handler
        )
