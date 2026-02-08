from __future__ import annotations

import enum
import hashlib
import logging
import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import PurePath
from typing import Annotated, Any, Callable, Generator, cast
from urllib.error import URLError
from uuid import UUID

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
from elasticsearch.dsl.response import Response
from libretranslatepy import LibreTranslateAPI
from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

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


class Secret(BaseModel):
    line_number: int
    secret: str


class _EsSecret(InnerDoc):
    line_number = Long()
    secret = Text(term_vector="with_positions_offsets")


class LibretranslateTranslatedLanguage(BaseModel):
    confidence: float
    language: str
    text: str


class _EsLibretranslateTranslatedLanguage(InnerDoc):
    confidence = Float()
    language = Keyword()
    text = Text(term_vector="with_positions_offsets")


LibreTranslateTranslations = list[LibretranslateTranslatedLanguage]


class LibretranslateSupportedLanguages(BaseModel):
    code: str
    name: str


try:
    LIBRETRANSLATE_SUPPORTED_LANGUAGES = [
        LibretranslateSupportedLanguages.model_validate(lang)
        # Since this is run at import-time, we can not use the dependency module here
        # to fetch a LibreTranslateAPI instance.
        for lang in LibreTranslateAPI(str(settings.translate_host)).languages()
        if settings.translate_target in lang["targets"]
    ]
except (URLError, JSONDecodeError):
    # Raised when libretranslate isn't available: for example while running unit-tests
    logger.warning("LibreTranslate service unavailable: using fallback language list")
    LIBRETRANSLATE_SUPPORTED_LANGUAGES = [
        LibretranslateSupportedLanguages(
            code=settings.translate_target, name="FallbackLanguage"
        ),
    ]


class _EsLibreTranslateTranslations(InnerDoc):
    """A wrapper for all available libretranslate languages."""

    for lang in LIBRETRANSLATE_SUPPORTED_LANGUAGES:
        locals()[lang.code] = Object(_EsLibretranslateTranslatedLanguage)


class ImapInfo(BaseModel):
    uid: int
    folder: PurePath


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


class RenderedFile(BaseModel):
    image_file_id: ObjectIdStr | None = None
    office_pdf_file_id: ObjectIdStr | None = None
    browser_pdf_file_id: ObjectIdStr | None = None


class _EsRenderedFile(InnerDoc):
    image_file_id = Keyword()
    office_pdf_file_id = Keyword()
    browser_pdf_file_id = Keyword()


FILE_SHORT_NAME_CONTENT_SUFFIX = ".content.txt"

TAG_LEN_MIN = 1
TAG_LEN_MAX = 25
Tag = Annotated[str, StringConstraints(min_length=TAG_LEN_MIN, max_length=TAG_LEN_MAX)]


class Attachment(BaseModel):
    id: UUID
    name: str


class _EsAttachment(InnerDoc):
    id = Keyword()
    name = Keyword()


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
    thumbnail_total_frames: int | None = None
    rendered_file: RenderedFile = RenderedFile()
    exclude_from_archives: bool = False
    tags: list[Tag] = []
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
    attachments: list[Attachment] = []
    summary: str | None = None
    embeddings: list[Embedding] = []
    trufflehog_secrets: list[Secret] | None = None
    ripsecrets_secrets: list[Secret] | None = None
    imap: ImapInfo | None = None

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, tags: list[Tag]) -> list[Tag]:
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
    thumbnail_total_frames = Long()
    rendered_file = Object(_EsRenderedFile)
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
    attachments = Object(_EsAttachment, multi=True)
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
    trufflehog_secrets = Object(_EsSecret, multi=True)
    ripsecrets_secrets = Object(_EsSecret, multi=True)
    imap = Object(_EsImapInfo)

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

    def get_stat_generic(self, query: QueryParameters, stat: Stat) -> StatisticsGeneric:
        class StatItem(BaseModel):
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
                transforms={"name": lambda s: str(bool(int(s))).lower()},
            ),
        }

        search = self._get_search_by_query(query=query)
        search = search[0:0]  # do not fetch hits
        search.aggs.metric(
            "total_no_of_files", "value_count", field="size"
        )  # required for % calculations
        search.aggs.metric(*search_dict[stat].args, **search_dict[stat].kwargs)
        result = self._execute_search_with_query(search=search, query=query)

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
                name=str(bucket["key"]), hits_count=int(bucket["doc_count"])
            )

            # apply special transforms like the name adjustment for IS_SPAM
            for stat_key, transformer in search_dict[stat].transforms.items():
                setattr(
                    stat_entry, stat_key, transformer(getattr(stat_entry, stat_key))
                )

            stats.data.append(stat_entry)
        return stats

    def get_stat_summary(self, query: QueryParameters) -> StatisticsSummary:
        search = self._get_search_by_query(query=query)
        search = search[0:0]  # do not fetch hits
        search.aggs.metric("avg_file_size", "avg", field="size")
        search.aggs.metric("max_file_size", "max", field="size")
        search.aggs.metric("min_file_size", "min", field="size")
        search.aggs.metric("total_no_of_files", "value_count", field="size")
        result = self._execute_search_with_query(search=search, query=query)

        return StatisticsSummary(
            avg_file_size=int(
                round(self.get_aggr(result, ["avg_file_size", "value"], default=0))
            ),
            max_file_size=self.get_aggr(result, ["max_file_size", "value"], default=0),
            min_file_size=self.get_aggr(result, ["min_file_size", "value"], default=0),
            total_no_of_files=self.get_aggr(
                result, ["total_no_of_files", "value"], default=0
            ),
        )

    def get_all_tags(self) -> list[str]:
        """Get all tags in the database."""
        search = self._document_type.search(using=self._elasticsearch)
        tags_aggregation: Agg[_EsFile] = A(
            "terms",
            field="tags",
            order={"_key": "asc"},  # alphebetic order
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
        embedding_vectors: list[list[float]],
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
                query_vector=q,
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
        self, query: QueryParameters, tree_node_directory_path: str
    ) -> list[TreePathsNode]:
        """Generate the tree path structure for all matching files."""

        escaped_directory = re.sub(
            ES_RESERVED_PATTERN, r"\\\1", tree_node_directory_path
        )
        pattern_directory = escaped_directory + "/.+"
        pattern_contents = escaped_directory + "/[^/]+/.+"

        search = self._get_search_by_query(query=query)

        dir_aggregation: Agg[_EsFile] = A(
            "terms",
            size=TREE_PATH_BUCKET_SIZE,
            field="full_path.tree",
            order={"_key": "asc"},  # alphebetic order by path name
            include=pattern_directory,
            exclude=pattern_contents,
        )
        search.aggs.bucket("directory", dir_aggregation)
        search = search[0:0]  # do not fetch hits
        result = self._execute_search_with_query(search=search, query=query)

        nodes = []
        for path in result.aggregations.directory.buckets:
            dirpath = PurePath(str(path.key))
            nodes.append(
                TreePathsNode(full_path=dirpath, file_count=cast(int, path.doc_count))
            )

        return nodes
