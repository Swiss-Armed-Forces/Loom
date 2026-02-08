# pylint: disable=too-many-lines
import logging
from typing import Generator
from unittest.mock import MagicMock

import pytest
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.dsl import Integer, Search, Text
from pydantic import BaseModel, ConfigDict

from common.ai_context.ai_context_repository import (
    AiContext,
    AiContextRepository,
    _EsAiContext,
)
from common.archive.archive_repository import (
    Archive,
    ArchiveRepository,
    StoredArchive,
    _EsArchive,
    _EsQueryParameters,
    _EsStoredArchive,
)
from common.dependencies import get_pubsub_service, get_query_builder
from common.file.file_repository import (
    FILE_SHORT_NAME_CONTENT_SUFFIX,
    Attachment,
    Embedding,
    File,
    FileRepository,
    ImapInfo,
    LibretranslateTranslatedLanguage,
    RenderedFile,
    Secret,
    _EsAttachment,
    _EsEmbedding,
    _EsFile,
    _EsImapInfo,
    _EsLibretranslateTranslatedLanguage,
    _EsLibreTranslateTranslations,
    _EsRenderedFile,
    _EsSecret,
)
from common.messages.pubsub_service import PubSubService
from common.models.base_repository import RepositoryObject
from common.models.es_repository import (
    ES_REPOSITORY_TYPES,
    UPDATE_RETRY_ON_CONFLICT_COUNT,
    BaseEsRepository,
    EsRepositoryObject,
    PaginationParameters,
    _EsMeta,
    _EsRepositoryDocument,
)
from common.services.query_builder import QueryBuilder, QueryParameters
from common.settings import settings
from mocks.test_value_defaults import TestValueDefaults

logger = logging.getLogger(__name__)


class _TestEsRepositoryObject(EsRepositoryObject):
    test_int: int
    test_str: str
    test_str_list: list[str]


class _TestEsDocument(_EsRepositoryDocument):
    test_int = Integer()
    test_str = Text()
    test_str_list = Text(multi=True)


class _TestEsRepository(BaseEsRepository[_TestEsDocument, _TestEsRepositoryObject]):
    def __init__(
        self,
        query_builder: QueryBuilder,
        pubsub_service: PubSubService,
        mock_types=False,
    ):
        super().__init__(query_builder, pubsub_service)
        # Note: we use on purpose not spec=type[...] here in MagicMocks,
        # mostly because it does not work mocking @classmethods.
        # I am not quite sure why..
        # Ahhh ducktyping..
        self.object_type: type[_TestEsRepositoryObject] | MagicMock = (
            _TestEsRepositoryObject
            if not mock_types
            else MagicMock(spec=_TestEsRepositoryObject)
        )
        self.document_type: type[_TestEsDocument] | MagicMock = (
            _TestEsDocument if not mock_types else MagicMock(spec=_TestEsDocument)
        )
        self.elasticsearch_mock: Elasticsearch = MagicMock(spec=Elasticsearch)

    @property
    def _object_type(self) -> type[_TestEsRepositoryObject]:
        return self.object_type

    @property
    def _document_type(self) -> type[_TestEsDocument]:
        return self.document_type

    @property
    def _elasticsearch(self) -> Elasticsearch:
        return self.elasticsearch_mock


class _TestInstances(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    object: RepositoryObject
    document: _EsRepositoryDocument


ES_REPOSITORY_TEST_INSTANCES: dict[type[BaseEsRepository], list[_TestInstances]] = {
    _TestEsRepository: [
        _TestInstances(
            object=_TestEsRepositoryObject(
                # Document
                # EsRepositoryObject
                es_meta=_EsMeta(
                    id=TestValueDefaults.test_uuid,
                    highlight=TestValueDefaults.test_empty_dict,
                    index=TestValueDefaults.test_str,
                    score=TestValueDefaults.test_float,
                    version=TestValueDefaults.test_int,
                    seq_no=TestValueDefaults.test_int,
                    primary_term=TestValueDefaults.test_int,
                ),
                sort_unique=TestValueDefaults.test_uuid,
                hidden=TestValueDefaults.test_bool,
                # _TestEsRepositoryObject
                test_int=TestValueDefaults.test_int,
                test_str=TestValueDefaults.test_str,
                test_str_list=TestValueDefaults.test_str_list,
            ),
            document=_TestEsDocument(
                {
                    # Document
                    "_id": TestValueDefaults.test_uuid,
                    # _EsRepositoryDocument
                    "_highlight": TestValueDefaults.test_empty_dict,
                    "_index": TestValueDefaults.test_str,
                    "_score": TestValueDefaults.test_float,
                    "_version": TestValueDefaults.test_int,
                    "_seq_no": TestValueDefaults.test_int,
                    "_primary_term": TestValueDefaults.test_int,
                },
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _TestEsDocument
                test_int=TestValueDefaults.test_int,
                test_str=TestValueDefaults.test_str,
                test_str_list=TestValueDefaults.test_str_list,
            ),
        )
    ],
    FileRepository: [
        _TestInstances(
            object=File(
                # RepositoryObject
                # EsRepositoryObject
                es_meta=_EsMeta(
                    id=TestValueDefaults.test_uuid,
                    highlight=TestValueDefaults.test_empty_dict,
                    index=TestValueDefaults.test_str,
                    score=TestValueDefaults.test_float,
                    version=TestValueDefaults.test_int,
                    seq_no=TestValueDefaults.test_int,
                    primary_term=TestValueDefaults.test_int,
                ),
                sort_unique=TestValueDefaults.test_uuid,
                hidden=TestValueDefaults.test_bool,
                # RepositoryTaskObject
                state=TestValueDefaults.test_str,
                tasks_succeeded=TestValueDefaults.test_uuid_list,
                tasks_retried=TestValueDefaults.test_uuid_list,
                tasks_failed=TestValueDefaults.test_uuid_list,
                # File
                storage_id=TestValueDefaults.test_object_id_str,
                content=TestValueDefaults.test_str,
                content_truncated=TestValueDefaults.test_bool,
                full_name=TestValueDefaults.test_pure_path,
                source=TestValueDefaults.test_str,
                sha256=TestValueDefaults.test_str,
                uploaded_datetime=TestValueDefaults.test_datetime,
                size=TestValueDefaults.test_long,
                thumbnail_file_id=TestValueDefaults.test_object_id_str,
                thumbnail_total_frames=TestValueDefaults.test_int,
                rendered_file=RenderedFile(
                    image_file_id=TestValueDefaults.test_object_id_str,
                    office_pdf_file_id=TestValueDefaults.test_object_id_str,
                    browser_pdf_file_id=TestValueDefaults.test_object_id_str,
                ),
                exclude_from_archives=TestValueDefaults.test_bool,
                tags=TestValueDefaults.test_str_list_no_duplicates,
                magic_file_type=TestValueDefaults.test_str,
                tika_language=TestValueDefaults.test_str,
                libretranslate_language=TestValueDefaults.test_str,
                libretranslate_translations=[
                    # Note: we have to use here a language defined
                    # in _EsLibreTranslateTranslations model. Which are fetched
                    # dynamically from libretranslate but as libretranslate is not
                    # available in unit testing, they are just set to:
                    #   [settings.translate_target]
                    LibretranslateTranslatedLanguage(
                        confidence=TestValueDefaults.test_float,
                        language=settings.translate_target,
                        text=TestValueDefaults.test_str,
                    )
                ],
                is_spam=TestValueDefaults.test_bool,
                tika_file_type=TestValueDefaults.test_str,
                archives=TestValueDefaults.test_str_list_no_duplicates,
                tika_meta=TestValueDefaults.test_str_str_dict,
                attachments=[
                    Attachment(
                        id=TestValueDefaults.test_uuid,
                        name=TestValueDefaults.test_str,
                    ),
                ],
                summary=TestValueDefaults.test_str,
                trufflehog_secrets=[
                    Secret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                    Secret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                ],
                ripsecrets_secrets=[
                    Secret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                    Secret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                ],
                embeddings=[
                    Embedding(
                        vector=TestValueDefaults.test_vector,
                        text=TestValueDefaults.test_str,
                    ),
                    Embedding(
                        vector=TestValueDefaults.test_vector,
                        text=TestValueDefaults.test_str,
                    ),
                ],
                imap=ImapInfo(
                    uid=TestValueDefaults.test_int,
                    folder=TestValueDefaults.test_pure_path,
                ),
            ),
            document=_EsFile(
                {
                    # Document
                    "_id": TestValueDefaults.test_uuid,
                    # _EsRepositoryDocument
                    "_highlight": TestValueDefaults.test_empty_dict,
                    "_index": TestValueDefaults.test_str,
                    "_score": TestValueDefaults.test_float,
                    "_version": TestValueDefaults.test_int,
                    "_seq_no": TestValueDefaults.test_int,
                    "_primary_term": TestValueDefaults.test_int,
                },
                deduplication_fingerprint=(
                    # computed in File
                    "b05da1c3eafe7b3545b322421b097efec85e7f55e9f01b8f1a1c7eff6d47fc47"
                ),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsFile
                storage_id=TestValueDefaults.test_object_id_str,
                content=TestValueDefaults.test_str,
                content_truncated=TestValueDefaults.test_bool,
                full_name=str(TestValueDefaults.test_pure_path),
                full_path=str(TestValueDefaults.test_pure_path),
                short_name=TestValueDefaults.test_pure_path.name,
                short_name_content=(
                    f"{TestValueDefaults.test_pure_path.name}"
                    f"{FILE_SHORT_NAME_CONTENT_SUFFIX}"
                ),
                extension=TestValueDefaults.test_pure_path.suffix,
                source=TestValueDefaults.test_str,
                sha256=TestValueDefaults.test_str,
                uploaded_datetime=TestValueDefaults.test_datetime.isoformat(),
                size=TestValueDefaults.test_long,
                thumbnail_file_id=TestValueDefaults.test_object_id_str,
                thumbnail_total_frames=TestValueDefaults.test_int,
                rendered_file=_EsRenderedFile(
                    image_file_id=TestValueDefaults.test_object_id_str,
                    office_pdf_file_id=TestValueDefaults.test_object_id_str,
                    browser_pdf_file_id=TestValueDefaults.test_object_id_str,
                ),
                exclude_from_archives=TestValueDefaults.test_bool,
                tags=TestValueDefaults.test_str_list_no_duplicates,
                magic_file_type=TestValueDefaults.test_str,
                tika_language=TestValueDefaults.test_str,
                libretranslate_language=TestValueDefaults.test_str,
                libretranslate_translations=_EsLibreTranslateTranslations(
                    **{
                        # Note: we have to use here a language defined
                        # in _EsLibreTranslateTranslations model. Which are fetched
                        # dynamically from libretranslate but as libretranslate is not
                        # available in unit testing, they are just set to:
                        #   [settings.translate_target]
                        settings.translate_target: _EsLibretranslateTranslatedLanguage(
                            confidence=TestValueDefaults.test_float,
                            language=settings.translate_target,
                            text=TestValueDefaults.test_str,
                        )
                    }
                ),
                is_spam=TestValueDefaults.test_bool,
                tika_file_type=TestValueDefaults.test_str,
                archives=TestValueDefaults.test_str_list_no_duplicates,
                tika_meta=TestValueDefaults.test_str_str_dict,
                attachments=[
                    _EsAttachment(
                        id=str(TestValueDefaults.test_uuid),
                        name=TestValueDefaults.test_str,
                    ),
                ],
                summary=TestValueDefaults.test_str,
                trufflehog_secrets=[
                    _EsSecret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                    _EsSecret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                ],
                ripsecrets_secrets=[
                    _EsSecret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                    _EsSecret(
                        line_number=TestValueDefaults.test_long,
                        secret=TestValueDefaults.test_str,
                    ),
                ],
                embeddings=[
                    _EsEmbedding(
                        vector=TestValueDefaults.test_vector,
                        text=TestValueDefaults.test_str,
                    ),
                    _EsEmbedding(
                        vector=TestValueDefaults.test_vector,
                        text=TestValueDefaults.test_str,
                    ),
                ],
                imap=_EsImapInfo(
                    uid=TestValueDefaults.test_int,
                    folder=str(TestValueDefaults.test_pure_path),
                ),
            ),
        )
    ],
    ArchiveRepository: [
        _TestInstances(
            object=Archive(
                # RepositoryObject
                # EsRepositoryObject
                es_meta=_EsMeta(
                    id=TestValueDefaults.test_uuid,
                    highlight=TestValueDefaults.test_empty_dict,
                    index=TestValueDefaults.test_str,
                    score=TestValueDefaults.test_float,
                    version=TestValueDefaults.test_int,
                    seq_no=TestValueDefaults.test_int,
                    primary_term=TestValueDefaults.test_int,
                ),
                sort_unique=TestValueDefaults.test_uuid,
                hidden=TestValueDefaults.test_bool,
                # RepositoryTaskObject
                state=TestValueDefaults.test_str,
                tasks_succeeded=TestValueDefaults.test_uuid_list,
                tasks_retried=TestValueDefaults.test_uuid_list,
                tasks_failed=TestValueDefaults.test_uuid_list,
                # Archive
                query=QueryParameters(
                    query_id=TestValueDefaults.test_object_id_str,
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                plain_file=StoredArchive(
                    storage_id=TestValueDefaults.test_object_id_str,
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=StoredArchive(
                    storage_id=TestValueDefaults.test_object_id_str,
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                created_at=TestValueDefaults.test_datetime,
            ),
            document=_EsArchive(
                {
                    # Document
                    "_id": TestValueDefaults.test_uuid,
                    # _EsRepositoryDocument
                    "_highlight": TestValueDefaults.test_empty_dict,
                    "_index": TestValueDefaults.test_str,
                    "_score": TestValueDefaults.test_float,
                    "_version": TestValueDefaults.test_int,
                    "_seq_no": TestValueDefaults.test_int,
                    "_primary_term": TestValueDefaults.test_int,
                },
                deduplication_fingerprint=str(TestValueDefaults.test_uuid),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsArchive
                query=_EsQueryParameters(
                    query_id=TestValueDefaults.test_object_id_str,
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                plain_file=_EsStoredArchive(
                    storage_id=TestValueDefaults.test_object_id_str,
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=_EsStoredArchive(
                    storage_id=TestValueDefaults.test_object_id_str,
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                created_at=TestValueDefaults.test_datetime.isoformat(),
                name=f"loom_archive_{TestValueDefaults.test_datetime}.zip",
                name_encrypted=f"loom_archive_{TestValueDefaults.test_datetime}.loom",
            ),
        )
    ],
    AiContextRepository: [
        _TestInstances(
            object=AiContext(
                # RepositoryObject
                # EsRepositoryObject
                es_meta=_EsMeta(
                    id=TestValueDefaults.test_uuid,
                    highlight=TestValueDefaults.test_empty_dict,
                    index=TestValueDefaults.test_str,
                    score=TestValueDefaults.test_float,
                    version=TestValueDefaults.test_int,
                    seq_no=TestValueDefaults.test_int,
                    primary_term=TestValueDefaults.test_int,
                ),
                sort_unique=TestValueDefaults.test_uuid,
                hidden=TestValueDefaults.test_bool,
                # RepositoryTaskObject
                state=TestValueDefaults.test_str,
                tasks_succeeded=TestValueDefaults.test_uuid_list,
                tasks_retried=TestValueDefaults.test_uuid_list,
                tasks_failed=TestValueDefaults.test_uuid_list,
                # AiContext
                query=QueryParameters(
                    query_id=TestValueDefaults.test_object_id_str,
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list_no_duplicates,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                chat_message_history_id=TestValueDefaults.test_uuid,
                created_at=TestValueDefaults.test_datetime,
            ),
            document=_EsAiContext(
                {
                    # Document
                    "_id": TestValueDefaults.test_uuid,
                    # _EsRepositoryDocument
                    "_highlight": TestValueDefaults.test_empty_dict,
                    "_index": TestValueDefaults.test_str,
                    "_score": TestValueDefaults.test_float,
                    "_version": TestValueDefaults.test_int,
                    "_seq_no": TestValueDefaults.test_int,
                    "_primary_term": TestValueDefaults.test_int,
                },
                deduplication_fingerprint=str(TestValueDefaults.test_uuid),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsAiContext
                query=_EsQueryParameters(
                    query_id=TestValueDefaults.test_object_id_str,
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list_no_duplicates,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                chat_message_history_id=str(TestValueDefaults.test_uuid),
                created_at=TestValueDefaults.test_datetime.isoformat(),
            ),
        )
    ],
}


def get_test_repository_object_instances() -> list[RepositoryObject]:
    def testcases() -> Generator[RepositoryObject, None, None]:
        for test_instance in ES_REPOSITORY_TEST_INSTANCES[_TestEsRepository]:
            yield test_instance.object

    return list(testcases())


def get_test_instances_for_all_known_repository_types() -> (
    list[tuple[type[BaseEsRepository], _TestInstances]]
):
    def testcases():
        for repository_type in ES_REPOSITORY_TYPES:
            for test_instance in ES_REPOSITORY_TEST_INSTANCES[repository_type]:
                yield (repository_type, test_instance)

    return list(testcases())


@pytest.mark.parametrize(
    "es_repository_type, test_instance",
    get_test_instances_for_all_known_repository_types(),
)
def test_es_repository_object_to_document(
    es_repository_type: type[BaseEsRepository], test_instance: _TestInstances
):
    es_repository = es_repository_type(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
    )
    document = es_repository._object_to_document(  # pylint: disable=protected-access
        test_instance.object
    )
    # do compare value dicts first: this is only here because
    # pytest can generate nice diffs on dicts.
    assert test_instance.document.to_dict() == document.to_dict()

    assert test_instance.document == document


@pytest.mark.parametrize(
    "es_repository_type, test_instance",
    get_test_instances_for_all_known_repository_types(),
)
def test_es_repository_document_to_object(
    es_repository_type: type[BaseEsRepository], test_instance: _TestInstances
):
    es_repository = es_repository_type(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
    )
    obj = es_repository._document_to_object(  # pylint: disable=protected-access
        test_instance.document
    )

    # do compare value dicts first: this is only here because
    # pytest can generate nice diffs on dicts.
    assert test_instance.object.model_dump() == obj.model_dump()

    assert test_instance.object == obj


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_get_by_id(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    es_repository.get_by_id(obj.id_)

    es_repository.document_type.get.assert_called_once_with(  # pylint: disable=no-member
        str(obj.id_),
        using=es_repository.elasticsearch_mock,
    )


def test_es_repository_get_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    es_repository.get_generator_by_query = MagicMock()

    query = QueryParameters(query_id="0123456789", search_string="just a random query")
    pagination = PaginationParameters(page_size=10)

    es_repository.get_by_query(
        query,
        pagination,
    )
    es_repository.get_generator_by_query.assert_called_once_with(
        query, pagination, None
    )


def test_es_repository_get_generator_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .sort()
        # happens in: _execute_search_with_query
        .index()
        .extra()
    )

    list(
        es_repository.get_generator_by_query(
            QueryParameters(query_id="0123456789", search_string="just a random query")
        )
    )
    search_pre_execute_mock.execute.assert_called_once()


def test_es_repository_get_generator_by_query_fetches_more_pages():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .sort()
    )

    # setup hits_hits
    hits_hits_mock = MagicMock()
    hits_hits_mock.sort = "sort value"

    # 1st page
    search_execute_mock = search_pre_execute_mock.index().extra().execute
    search_execute_mock.return_value.hits.__iter__.return_value = [
        _TestEsDocument(),
        _TestEsDocument(),
    ]
    search_execute_mock.return_value.hits.__len__.return_value = 2
    search_execute_mock.return_value.hits.hits = [
        hits_hits_mock,
        hits_hits_mock,
    ]

    # 2nd page
    search_pre_execute_mock = search_pre_execute_mock.extra()
    search_page2_execute_mock = search_pre_execute_mock.index().extra().execute
    search_page2_execute_mock.return_value.hits.__iter__.return_value = [
        _TestEsDocument()
    ]
    search_page2_execute_mock.return_value.hits.__len__.return_value = 1
    search_page2_execute_mock.return_value.hits.hits = [hits_hits_mock]

    # 3rd page (empty)
    search_pre_execute_mock = search_pre_execute_mock.extra()
    search_page3_execute_mock = search_pre_execute_mock.index().extra().execute
    search_page3_execute_mock.return_value.hits.__iter__.return_value = []
    search_page3_execute_mock.return_value.hits.hits = []

    results = list(
        es_repository.get_generator_by_query(
            QueryParameters(query_id="0123456789", search_string="just a random query")
        )
    )
    assert len(results) == 3
    search_execute_mock.assert_called_once()
    search_page2_execute_mock.assert_called_once()
    search_page3_execute_mock.assert_called_once()


def test_es_repository_get_generator_by_query_fetches_more_pages_with_expired_pit():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    initial_query_id = "initial query id"
    new_query_id = "new query id"

    open_point_in_time = MagicMock()
    open_point_in_time.return_value = {"id": new_query_id}
    es_repository.elasticsearch_mock.open_point_in_time = open_point_in_time

    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .sort()
    )

    # setup hits_hits
    hits_hits_mock = MagicMock()
    hits_hits_mock.sort = "sort value"

    # 1st page works
    search_execute_mock = search_pre_execute_mock.index().extra().execute
    search_execute_mock.return_value.hits.__iter__.return_value = [
        _TestEsDocument(),
        _TestEsDocument(),
    ]
    search_execute_mock.return_value.hits.__len__.return_value = 2
    search_execute_mock.return_value.hits.hits = [
        hits_hits_mock,
        hits_hits_mock,
    ]

    # 2nd page throws NotFoundError on first call, succeeds on retry
    search_pre_execute_mock = search_pre_execute_mock.extra()
    search_page2_execute_mock = search_pre_execute_mock.index().extra().execute

    # Configure to throw on first call, then return success on second call
    mock_success_response = MagicMock()
    mock_success_response.hits.__iter__.return_value = [_TestEsDocument()]
    mock_success_response.hits.__len__.return_value = 1
    mock_success_response.hits.hits = [hits_hits_mock]

    search_page2_execute_mock.side_effect = [
        NotFoundError(
            "search phase execution exception", MagicMock(), None
        ),  # First call throws
        mock_success_response,  # Second call succeeds
    ]

    # 3rd page (empty)
    search_pre_execute_mock = search_pre_execute_mock.extra()
    search_page3_execute_mock = search_pre_execute_mock.index().extra().execute
    search_page3_execute_mock.return_value.hits.__iter__.return_value = []
    search_page3_execute_mock.return_value.hits = []

    results = list(
        es_repository.get_generator_by_query(
            QueryParameters(
                query_id=initial_query_id, search_string="just a random query"
            )
        )
    )
    assert len(results) == 3
    search_execute_mock.assert_called_once()
    assert search_page2_execute_mock.call_count == 2
    search_page3_execute_mock.assert_called_once()
    es_repository.elasticsearch_mock.open_point_in_time.assert_called_once()


def test_es_repository_get_id_generator_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .sort()
        # happens in: _execute_search_with_query
        .index()
        .extra()
    )

    list(
        es_repository.get_generator_by_query(
            QueryParameters(query_id="0123456789", search_string="just a random query")
        )
    )
    search_pre_execute_mock.execute.assert_called_once()


def test_es_repository_count_by_query():

    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    # Because of __getitem__() in mock addressing:
    # pylint: disable=unnecessary-dunder-call
    search_pre_count_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: count_by_query
        .__getitem__(slice(0, 0, None))
        .extra()
        # happens in: _execute_search_with_query
        .index()
        .extra()
        .execute
    )
    hits_mock = MagicMock()
    # https://github.com/elastic/elasticsearch-dsl-py/issues/1897
    hits_mock.hits.total.value = 123  # pylint: disable=no-member
    search_pre_count_mock.return_value = hits_mock
    count = es_repository.count_by_query(
        QueryParameters(query_id="0123456789", search_string="just a random query")
    )
    assert count == 123


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_get_by_id_with_query(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    # setup search_mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: get_by_id_with_query
        .filter()
        # happens in: _execute_search_with_query
        .index()
        .extra()
    )

    es_repository.get_by_id_with_query(
        obj.id_,
        QueryParameters(query_id="0123456789", search_string="just a random query"),
        full_highlight_context=False,
    )

    search_pre_execute_mock.execute.assert_called_once()


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_save(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    es_repository.document_type.return_value = document_mock

    es_repository.save(obj)

    document_mock.save.assert_called_once_with(
        using=es_repository.elasticsearch_mock,
        refresh=True,
    )


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_update(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    es_repository.document_type.return_value = document_mock

    es_repository.update(obj)

    document_mock.update.assert_called_once_with(
        deduplication_fingerprint=obj.deduplication_fingerprint,
        sort_unique=obj.sort_unique,
        hidden=obj.hidden,
        test_int=obj.test_int,
        test_str=obj.test_str,
        test_str_list=obj.test_str_list,
        using=es_repository.elasticsearch_mock,
        refresh=True,
        retry_on_conflict=UPDATE_RETRY_ON_CONFLICT_COUNT,
    )


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_update_include(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    es_repository.document_type.return_value = document_mock

    es_repository.update(obj, include={"test_int", "test_str"})

    document_mock.update.assert_called_once_with(
        test_int=obj.test_int,
        test_str=obj.test_str,
        using=es_repository.elasticsearch_mock,
        refresh=True,
        retry_on_conflict=UPDATE_RETRY_ON_CONFLICT_COUNT,
    )


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_update_exclude(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    es_repository.document_type.return_value = document_mock

    es_repository.update(obj, exclude={"test_int", "test_str"})

    document_mock.update.assert_called_once_with(
        deduplication_fingerprint=obj.deduplication_fingerprint,
        sort_unique=obj.sort_unique,
        hidden=obj.hidden,
        test_str_list=obj.test_str_list,
        using=es_repository.elasticsearch_mock,
        refresh=True,
        retry_on_conflict=UPDATE_RETRY_ON_CONFLICT_COUNT,
    )


def test_es_repository_open_point_in_time():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    mock_point_in_time_id = "0123456789"
    open_point_in_time = MagicMock()
    open_point_in_time.return_value = {"id": mock_point_in_time_id}
    es_repository.elasticsearch_mock.open_point_in_time = open_point_in_time

    point_in_time_id = es_repository.open_point_in_time()

    es_repository.elasticsearch_mock.open_point_in_time.assert_called_once()
    assert point_in_time_id == mock_point_in_time_id
