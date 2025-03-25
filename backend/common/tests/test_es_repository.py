import logging
from typing import Generator
from unittest.mock import MagicMock, call

import pytest
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Integer, Search, Text
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
    Embedding,
    File,
    FileRepository,
    LibretranslateTranslatedLanguage,
    _EsEmbedding,
    _EsFile,
    _EsLibretranslateTranslatedLanguage,
    _EsLibreTranslateTranslations,
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
        # Note: we use on purpose not spec=type[...] here, mostly because
        # that does not work work mocking @classmethods.
        # I am not quite sure why.. Ahhh ducktyping..
        self.object_type: _TestEsRepositoryObject | MagicMock = (
            _TestEsRepositoryObject
            if not mock_types
            else MagicMock(spec=_TestEsRepositoryObject)
        )
        self.document_type: _TestEsDocument | MagicMock = (
            _TestEsDocument if not mock_types else MagicMock(spec=_TestEsDocument)
        )
        self.elasticsearch_mock = MagicMock(spec=Elasticsearch)

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
                storage_id=TestValueDefaults.test_objec_id_str,
                content=TestValueDefaults.test_str,
                content_truncated=TestValueDefaults.test_bool,
                full_name=TestValueDefaults.test_pure_path,
                source=TestValueDefaults.test_str,
                sha256=TestValueDefaults.test_str,
                uploaded_datetime=TestValueDefaults.test_datetime,
                size=TestValueDefaults.test_long,
                thumbnail_file_id=TestValueDefaults.test_objec_id_str,
                preview_file_id=TestValueDefaults.test_objec_id_str,
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
                has_attachments=TestValueDefaults.test_bool,
                summary=TestValueDefaults.test_str,
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
                root_task_id=str(TestValueDefaults.test_uuid),
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsFile
                storage_id=str(TestValueDefaults.test_objec_id_str),
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
                thumbnail_file_id=str(TestValueDefaults.test_objec_id_str),
                preview_file_id=str(TestValueDefaults.test_objec_id_str),
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
                has_attachments=TestValueDefaults.test_bool,
                summary=TestValueDefaults.test_str,
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
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list,
                ),
                plain_file=StoredArchive(
                    storage_id=TestValueDefaults.test_objec_id_str,
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=StoredArchive(
                    storage_id=TestValueDefaults.test_objec_id_str,
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
                root_task_id=str(TestValueDefaults.test_uuid),
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsArchive
                query=_EsQueryParameters(
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list,
                ),
                plain_file=_EsStoredArchive(
                    storage_id=str(TestValueDefaults.test_objec_id_str),
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=_EsStoredArchive(
                    storage_id=str(TestValueDefaults.test_objec_id_str),
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
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list_no_duplicates,
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
                root_task_id=str(TestValueDefaults.test_uuid),
                state=TestValueDefaults.test_str,
                tasks_succeeded=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_retried=list(map(str, TestValueDefaults.test_uuid_list)),
                tasks_failed=list(map(str, TestValueDefaults.test_uuid_list)),
                # _EsAiContext
                query=_EsQueryParameters(
                    search_string=TestValueDefaults.test_str,
                    languages=TestValueDefaults.test_str_list_no_duplicates,
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
        obj.id_,
        using=es_repository.elasticsearch_mock,
    )


def test_es_repository_get_all():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    es_repository.get_generator_by_query = MagicMock(
        spec=es_repository.get_generator_by_query
    )

    es_repository.get_all()

    es_repository.get_generator_by_query.assert_called_once_with(
        query=QueryParameters(search_string="*")
    )


def test_es_repository_get_by_query():
    # Disable unnecessary-dunder-call because of __getitem__() in mock addressing
    # pylint: disable=unnecessary-dunder-call
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    es_repository.get_generator_by_query = MagicMock()

    query = QueryParameters(search_string="just a random query")
    pagination = PaginationParameters(size=10)

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
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_execute_mock = (
        search_mock
        # happens in: __get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .extra()
        .index()
        .extra()
        .sort()
        .execute
    )

    list(
        es_repository.get_generator_by_query(
            QueryParameters(search_string="just a random query")
        )
    )
    search_execute_mock.assert_called_once()


def test_es_repository_get_generator_by_query_fetches_more_pages():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_mock = (
        search_mock
        # happens in: __get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .extra()
        .sort()
    )
    search_execute_result_hit_mock = MagicMock()
    search_execute_result_hit_mock.sort = "sort value"

    search_mock.execute().hits.hits = [search_execute_result_hit_mock]
    search_mock.execute().hits.total.value = 2

    # 2nd loop pass will call .extra: return same mock object
    search_mock.extra.return_value = search_mock

    list(
        es_repository.get_generator_by_query(
            QueryParameters(search_string="just a random query")
        )
    )
    search_mock.execute.assert_has_calls([call(), call()])


def test_es_repository_get_id_generator_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_execute_mock = (
        search_mock
        # happens in: __get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _paginate_search
        .extra()
        .index()
        .extra()
        .sort()
        .execute
    )

    list(
        es_repository.get_generator_by_query(
            QueryParameters(search_string="just a random query")
        )
    )
    search_execute_mock.assert_called_once()


def test_es_repository_count_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    search_count_mock = (
        search_mock
        # happens in: count_by_query
        .query().count
    )
    search_count_mock.return_value = 123
    count = es_repository.count_by_query(
        QueryParameters(search_string="just a random query")
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
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock

    search_mock.execute().hits.total.value = 1

    es_repository.get_by_id_with_query(
        obj.id_,
        QueryParameters(search_string="just a random query"),
        full_highlight_context=False,
    )

    search_mock.highlight_options().highlight().query().filter().execute.assert_called_once()


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
