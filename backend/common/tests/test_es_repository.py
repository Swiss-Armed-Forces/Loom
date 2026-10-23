# pylint: disable=too-many-lines
import logging
from pathlib import PurePosixPath
from types import SimpleNamespace
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.dsl import Integer, Search, Text
from pydantic import BaseModel, ConfigDict, ValidationError

from common.ai_context.ai_context_repository import (
    AiContext,
    AiContextRepository,
    AiQuestion,
    AiQuestionCitation,
    ModeId,
    ToolCallActivityEntry,
    _EsActivityEntry,
    _EsAiContext,
    _EsAiQuestion,
    _EsAiQuestionCitation,
)
from common.archive.archive_repository import (
    LOOM_ARCHIVE_VERSION,
    Archive,
    ArchiveRepository,
    StoredArchive,
    _EsArchive,
    _EsQueryParameters,
    _EsStoredArchive,
)
from common.dependencies import get_pubsub_service, get_query_builder
from common.file.file_repository import (
    Attachment,
    Embedding,
    File,
    FileRepository,
    ImapInfo,
    RenderedFile,
    Secret,
    TikaMeta,
    TranslatedLanguage,
    _EsAttachment,
    _EsEmbedding,
    _EsFile,
    _EsImapInfo,
    _EsLazyBytes,
    _EsRenderedFile,
    _EsSecret,
    _EsTikaMeta,
    _EsTranslatedLanguage,
)
from common.messages.pubsub_service import PubSubService
from common.models.base_repository import RepositoryObject
from common.models.cursor_pagination import (
    InvalidPaginationCursorError,
    SearchAfterCursor,
)
from common.models.es_repository import (
    _ID_SCAN_PAGE_SIZE,
    _SCORE_SAMPLE_SIZE,
    ES_REPOSITORY_TYPES,
    BaseEsRepository,
    EsRepositoryObject,
    LeadingSnippetHighlight,
    PagedSearchResult,
    PaginationParameters,
    PointInTimeExpiredError,
    QueryScoreStats,
    SortingParameters,
    _EsMeta,
    _EsRepositoryDocument,
)
from common.services.lazybytes_service import LazyBytes
from common.services.query_builder import QueryBuilder, QueryParameters
from common.settings import settings
from common.task_object.root_task_information_repository import (
    RootTaskInformation,
    RootTaskInformationRepository,
    _EsRootTaskInformation,
)
from common.task_object.task_object import (
    TaskRecord,
    TaskRun,
    _EsTaskRecord,
    _EsTaskRun,
)
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
                tasks=[
                    TaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # File
                storage_data=LazyBytes(service_id=str(TestValueDefaults.test_uuid)),
                content=TestValueDefaults.test_str,
                content_truncated=TestValueDefaults.test_bool,
                attachments_skipped=TestValueDefaults.test_bool,
                full_name=TestValueDefaults.test_file_pure_path,
                source=TestValueDefaults.test_str,
                parent_id=TestValueDefaults.test_uuid,
                sha256=TestValueDefaults.test_str,
                uploaded_datetime=TestValueDefaults.test_datetime,
                size=TestValueDefaults.test_long,
                reindex_count=TestValueDefaults.test_long,
                thumbnail_data=LazyBytes(service_id=str(TestValueDefaults.test_uuid)),
                thumbnail_total_frames=TestValueDefaults.test_int,
                rendered_file=RenderedFile(
                    image_data=LazyBytes(service_id=str(TestValueDefaults.test_uuid)),
                    office_pdf_data=LazyBytes(
                        service_id=str(TestValueDefaults.test_uuid)
                    ),
                    browser_pdf_data=LazyBytes(
                        service_id=str(TestValueDefaults.test_uuid)
                    ),
                ),
                tags=TestValueDefaults.test_str_list_no_duplicates,
                magic_file_type=TestValueDefaults.test_str,
                magic_mime_type_group=TestValueDefaults.test_mime_type_group,
                tika_language=TestValueDefaults.test_str,
                detected_language=TestValueDefaults.test_str,
                translations=[
                    TranslatedLanguage(
                        confidence=TestValueDefaults.test_float,
                        language=settings.translate_target,
                        text=TestValueDefaults.test_str,
                    )
                ],
                is_spam=TestValueDefaults.test_bool,
                tika_file_type=TestValueDefaults.test_str,
                tika_mime_type_group=TestValueDefaults.test_mime_type_group,
                archives=TestValueDefaults.test_str_list_no_duplicates,
                tika_meta=TikaMeta(
                    dc_title=TestValueDefaults.test_str,
                    dc_description=TestValueDefaults.test_str,
                    dc_subject=TestValueDefaults.test_str,
                    dc_creator=TestValueDefaults.test_str,
                    dcterms_created=TestValueDefaults.test_datetime,
                    dcterms_modified=TestValueDefaults.test_datetime,
                    pdf_producer=TestValueDefaults.test_str,
                    pdf_docinfo_producer=TestValueDefaults.test_str,
                    pdf_docinfo_creator=TestValueDefaults.test_str,
                    pdf_docinfo_creator_tool=TestValueDefaults.test_str,
                    pdf_docinfo_created=TestValueDefaults.test_datetime,
                    pdf_docinfo_modified=TestValueDefaults.test_datetime,
                    pdf_docinfo_keywords=TestValueDefaults.test_str,
                    pdf_docinfo_title=TestValueDefaults.test_str,
                    message_from=TestValueDefaults.test_str,
                    message_from_name=TestValueDefaults.test_str,
                    message_from_email=TestValueDefaults.test_str,
                    message_to=TestValueDefaults.test_str,
                    message_to_name=TestValueDefaults.test_str,
                    message_to_email=TestValueDefaults.test_str,
                    message_cc=TestValueDefaults.test_str,
                    message_bcc=TestValueDefaults.test_str,
                    meta_last_author=TestValueDefaults.test_str,
                    content_type=TestValueDefaults.test_str,
                ),
                tika_handled_by=TestValueDefaults.test_str,
                attachments=[
                    Attachment(
                        id=TestValueDefaults.test_uuid,
                        name=TestValueDefaults.test_str,
                    ),
                ],
                recursion_depth=TestValueDefaults.test_long,
                summary=TestValueDefaults.test_str,
                image_description=TestValueDefaults.test_str,
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
                    folder=TestValueDefaults.test_imappure_path,
                ),
                flagged=TestValueDefaults.test_bool,
                seen=TestValueDefaults.test_bool,
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
                id=str(TestValueDefaults.test_uuid),
                deduplication_fingerprint=(
                    # computed in File
                    "b05da1c3eafe7b3545b322421b097efec85e7f55e9f01b8f1a1c7eff6d47fc47"
                ),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                failed_task_names=[TestValueDefaults.test_str],
                retried_task_names=[TestValueDefaults.test_str],
                successful_task_names=[TestValueDefaults.test_str],
                tasks=[
                    _EsTaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # _EsFile
                storage_data=_EsLazyBytes(
                    service_id=str(TestValueDefaults.test_uuid), embedded_data=None
                ),
                content=TestValueDefaults.test_str,
                content_truncated=TestValueDefaults.test_bool,
                attachments_skipped=TestValueDefaults.test_bool,
                full_name=str(TestValueDefaults.test_file_pure_path),
                full_path=(
                    f"//{TestValueDefaults.test_str}/"
                    f"{str(TestValueDefaults.test_file_pure_path).lstrip('/')}"
                ),
                parent_path=(
                    f"//{TestValueDefaults.test_str}/"
                    f"{str(TestValueDefaults.test_file_pure_path.parent).lstrip('/')}"
                ),
                short_name=TestValueDefaults.test_file_pure_path.name,
                extension=TestValueDefaults.test_file_pure_path.suffix,
                # Derived from the same path the two fields above are, so the
                # expectation follows the fixture rather than a fixed number.
                path_depth=len(
                    PurePosixPath(
                        f"//{TestValueDefaults.test_str}/"
                        f"{str(TestValueDefaults.test_file_pure_path).lstrip('/')}"
                    ).parts
                )
                - 1,
                source=TestValueDefaults.test_str,
                parent_id=str(TestValueDefaults.test_uuid),
                sha256=TestValueDefaults.test_str,
                uploaded_datetime=TestValueDefaults.test_datetime.isoformat(),
                size=TestValueDefaults.test_long,
                reindex_count=TestValueDefaults.test_long,
                thumbnail_data=_EsLazyBytes(
                    service_id=str(TestValueDefaults.test_uuid),
                    embedded_data=None,
                ),
                thumbnail_total_frames=TestValueDefaults.test_int,
                rendered_file=_EsRenderedFile(
                    image_data=_EsLazyBytes(
                        service_id=str(TestValueDefaults.test_uuid),
                        embedded_data=None,
                    ),
                    office_pdf_data=_EsLazyBytes(
                        service_id=str(TestValueDefaults.test_uuid),
                        embedded_data=None,
                    ),
                    browser_pdf_data=_EsLazyBytes(
                        service_id=str(TestValueDefaults.test_uuid),
                        embedded_data=None,
                    ),
                ),
                tags=TestValueDefaults.test_str_list_no_duplicates,
                magic_file_type=TestValueDefaults.test_str,
                magic_mime_type_group=TestValueDefaults.test_mime_type_group,
                tika_language=TestValueDefaults.test_str,
                detected_language=TestValueDefaults.test_str,
                translations=[
                    _EsTranslatedLanguage(
                        confidence=TestValueDefaults.test_float,
                        language=settings.translate_target,
                        text=TestValueDefaults.test_str,
                    )
                ],
                is_spam=TestValueDefaults.test_bool,
                tika_file_type=TestValueDefaults.test_str,
                tika_mime_type_group=TestValueDefaults.test_mime_type_group,
                archives=TestValueDefaults.test_str_list_no_duplicates,
                tika_meta=_EsTikaMeta(
                    dc_title=TestValueDefaults.test_str,
                    dc_description=TestValueDefaults.test_str,
                    dc_subject=TestValueDefaults.test_str,
                    dc_creator=TestValueDefaults.test_str,
                    dcterms_created=TestValueDefaults.test_datetime.isoformat(),
                    dcterms_modified=TestValueDefaults.test_datetime.isoformat(),
                    pdf_producer=TestValueDefaults.test_str,
                    pdf_docinfo_producer=TestValueDefaults.test_str,
                    pdf_docinfo_creator=TestValueDefaults.test_str,
                    pdf_docinfo_creator_tool=TestValueDefaults.test_str,
                    pdf_docinfo_created=TestValueDefaults.test_datetime.isoformat(),
                    pdf_docinfo_modified=TestValueDefaults.test_datetime.isoformat(),
                    pdf_docinfo_keywords=TestValueDefaults.test_str,
                    pdf_docinfo_title=TestValueDefaults.test_str,
                    message_from=TestValueDefaults.test_str,
                    message_from_name=TestValueDefaults.test_str,
                    message_from_email=TestValueDefaults.test_str,
                    message_to=TestValueDefaults.test_str,
                    message_to_name=TestValueDefaults.test_str,
                    message_to_email=TestValueDefaults.test_str,
                    message_cc=TestValueDefaults.test_str,
                    message_bcc=TestValueDefaults.test_str,
                    meta_last_author=TestValueDefaults.test_str,
                    content_type=TestValueDefaults.test_str,
                ),
                tika_handled_by=TestValueDefaults.test_str,
                attachments=[
                    _EsAttachment(
                        id=str(TestValueDefaults.test_uuid),
                        name=TestValueDefaults.test_str,
                    ),
                ],
                recursion_depth=TestValueDefaults.test_long,
                summary=TestValueDefaults.test_str,
                image_description=TestValueDefaults.test_str,
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
                    folder=str(TestValueDefaults.test_imappure_path),
                    folder_utf7=str(
                        TestValueDefaults.test_imappure_path
                    ),  # no unicode chars so it matches folder
                ),
                flagged=TestValueDefaults.test_bool,
                seen=TestValueDefaults.test_bool,
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
                tasks=[
                    TaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # Archive
                query=QueryParameters(
                    query_id=str(TestValueDefaults.test_uuid),
                    search_string=TestValueDefaults.test_str,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                plain_file=StoredArchive(
                    storage_data=LazyBytes(service_id=str(TestValueDefaults.test_uuid)),
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=StoredArchive(
                    storage_data=LazyBytes(service_id=str(TestValueDefaults.test_uuid)),
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                created_at=TestValueDefaults.test_datetime,
                note=TestValueDefaults.test_str,
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
                id=str(TestValueDefaults.test_uuid),
                deduplication_fingerprint=str(TestValueDefaults.test_uuid),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                failed_task_names=[TestValueDefaults.test_str],
                retried_task_names=[TestValueDefaults.test_str],
                successful_task_names=[TestValueDefaults.test_str],
                tasks=[
                    _EsTaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # _EsArchive
                version=LOOM_ARCHIVE_VERSION,
                query=_EsQueryParameters(
                    query_id=str(TestValueDefaults.test_uuid),
                    search_string=TestValueDefaults.test_str,
                    keep_alive=TestValueDefaults.test_keep_alive,
                ),
                plain_file=_EsStoredArchive(
                    storage_data=_EsLazyBytes(
                        service_id=str(TestValueDefaults.test_uuid),
                        embedded_data=None,
                    ),
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                encrypted_file=_EsStoredArchive(
                    storage_data=_EsLazyBytes(
                        service_id=str(TestValueDefaults.test_uuid),
                        embedded_data=None,
                    ),
                    sha256=TestValueDefaults.test_str,
                    size=TestValueDefaults.test_long,
                ),
                created_at=TestValueDefaults.test_datetime.isoformat(),
                name=(
                    "loom_archive_"
                    f"{TestValueDefaults.test_datetime.strftime('%Y-%m-%d_%H_%M_%S.%f')}"
                    ".zip"
                ),
                name_encrypted=(
                    "loom_archive_"
                    f"{TestValueDefaults.test_datetime.strftime('%Y-%m-%d_%H_%M_%S.%f')}"
                    ".loom"
                ),
                note=TestValueDefaults.test_str,
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
                tasks=[
                    TaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            TaskRun(
                                task_id=TestValueDefaults.test_uuid,
                                started_at=TestValueDefaults.test_datetime,
                                finished_at=TestValueDefaults.test_datetime,
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # AiContext
                chat_message_history_id=TestValueDefaults.test_uuid,
                created_at=TestValueDefaults.test_datetime,
                questions=[
                    AiQuestion(
                        question=TestValueDefaults.test_str,
                        answer=TestValueDefaults.test_str,
                        citations=[
                            AiQuestionCitation(
                                file_id=TestValueDefaults.test_uuid,
                                text=TestValueDefaults.test_str,
                            )
                        ],
                        activity=[
                            ToolCallActivityEntry(
                                tool_name=TestValueDefaults.test_str,
                                input={"key": TestValueDefaults.test_str},
                                output=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                active_mode=ModeId.RESEARCH,
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
                id=str(TestValueDefaults.test_uuid),
                deduplication_fingerprint=str(TestValueDefaults.test_uuid),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsTaskDocument
                state=TestValueDefaults.test_str,
                failed_task_names=[TestValueDefaults.test_str],
                retried_task_names=[TestValueDefaults.test_str],
                successful_task_names=[TestValueDefaults.test_str],
                tasks=[
                    _EsTaskRecord(
                        task_name=TestValueDefaults.test_str,
                        avg_duration=TestValueDefaults.test_float,
                        run_count=TestValueDefaults.test_int,
                        succeeded=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        retried=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                        failed=[
                            _EsTaskRun(
                                task_id=str(TestValueDefaults.test_uuid),
                                started_at=TestValueDefaults.test_datetime.isoformat(),
                                finished_at=TestValueDefaults.test_datetime.isoformat(),
                                duration=TestValueDefaults.test_float,
                                exception=TestValueDefaults.test_str,
                                arguments=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                # _EsAiContext
                chat_message_history_id=str(TestValueDefaults.test_uuid),
                created_at=TestValueDefaults.test_datetime.isoformat(),
                questions=[
                    _EsAiQuestion(
                        question=TestValueDefaults.test_str,
                        answer=TestValueDefaults.test_str,
                        citations=[
                            _EsAiQuestionCitation(
                                file_id=str(TestValueDefaults.test_uuid),
                                text=TestValueDefaults.test_str,
                            )
                        ],
                        activity=[
                            _EsActivityEntry(
                                type="tool_call",
                                tool_name=TestValueDefaults.test_str,
                                input={"key": TestValueDefaults.test_str},
                                output=TestValueDefaults.test_str,
                            )
                        ],
                    )
                ],
                active_mode=ModeId.RESEARCH,
            ),
        )
    ],
    RootTaskInformationRepository: [
        _TestInstances(
            object=RootTaskInformation(
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
                # RootTaskInformation
                root_task_id=TestValueDefaults.test_uuid,
                object_id=TestValueDefaults.test_uuid,
            ),
            document=_EsRootTaskInformation(
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
                id=str(TestValueDefaults.test_uuid),
                deduplication_fingerprint=str(TestValueDefaults.test_uuid),
                sort_unique=str(TestValueDefaults.test_uuid),
                hidden=TestValueDefaults.test_bool,
                # _EsRootTaskInformation
                root_task_id=str(TestValueDefaults.test_uuid),
                object_id=str(TestValueDefaults.test_uuid),
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
    a = test_instance.document.to_dict(skip_empty=False)
    b = document.to_dict()
    assert a == b

    actual = vars(test_instance.document)
    expected = vars(document)

    for key in actual.keys() | expected.keys():
        if actual.get(key) != expected.get(key):
            print("[ITEM]", key, repr(actual.get(key)), repr(expected.get(key)))

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
        .extra()  # scan_page_size
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


def test_search_after_cursor_round_trips():
    """The cursor travels as itself: a JSON body in, a model out, nothing to decode."""
    cursor = SearchAfterCursor(
        src="execute_query", last_sort=[1.5, "x"], pit="pit-1", query_digest="d"
    )

    decoded = SearchAfterCursor.model_validate_json(cursor.model_dump_json())
    decoded.validate_for(expected_src="execute_query", expected_digest="d")

    assert decoded.last_sort == [1.5, "x"]
    assert decoded.pit == "pit-1"


def test_search_after_cursor_rejects_another_producers_cursor():
    """Producers sort on different tuples, so a foreign cursor would otherwise be
    applied to an unrelated sort and return a plausible but wrong page."""
    cursor = SearchAfterCursor(src="flat_files", last_sort=[1.5, "x"])

    with pytest.raises(InvalidPaginationCursorError):
        cursor.validate_for(expected_src="execute_query")


def test_search_after_cursor_rejects_a_cursor_from_a_different_query():
    cursor = SearchAfterCursor(
        src="execute_query", last_sort=[1.5, "x"], query_digest="for-query-a"
    )

    with pytest.raises(InvalidPaginationCursorError):
        cursor.validate_for(
            expected_src="execute_query",
            expected_digest="for-query-b",
        )


def test_search_after_cursor_requires_a_digest_when_one_is_expected():
    cursor = SearchAfterCursor(src="execute_query", last_sort=[1.5, "x"])

    with pytest.raises(InvalidPaginationCursorError):
        cursor.validate_for(expected_src="execute_query", expected_digest="d")


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty-object"),
        pytest.param({"last_sort": [1.0, "x"]}, id="no-src"),
        pytest.param({"src": "nope", "last_sort": [1.0, "x"]}, id="unknown-src"),
        pytest.param({"src": "execute_query", "last_sort": []}, id="empty-sort"),
        pytest.param(
            {"src": "execute_query", "last_sort": [1.0, {"a": 1}]},
            id="non-scalar-sort-value",
        ),
        pytest.param(
            # isinstance(True, int) is True, so a bool would otherwise pass the
            # scalar check and be rejected by ES with an opaque error.
            {"src": "execute_query", "last_sort": [1.0, True]},
            id="boolean-sort-value",
        ),
    ],
)
def test_search_after_cursor_rejects_a_malformed_cursor(payload: dict):
    """Shape is validated on the model so a bad cursor never reaches ES, which would
    answer with an opaque 400 that callers have to string-match.

    Validating here rather than in a decoder is what makes it hold for every way in —
    the REST body, the agent's handle store and the Celery round-trip alike.
    """
    with pytest.raises(ValidationError):
        SearchAfterCursor.model_validate(payload)


def test_search_after_cursor_accepts_a_missing_sort_value():
    """ES returns null in the sort array for a document that has no value for the sort
    field, and takes it back in search_after — rejecting it would wedge paging at that
    document for good."""
    cursor = SearchAfterCursor(src="execute_query", last_sort=[1.0, None])

    assert cursor.last_sort == [1.0, None]


def test_search_after_cursor_digest_depends_on_every_part():
    assert SearchAfterCursor.digest("a", "b") == SearchAfterCursor.digest("a", "b")
    assert SearchAfterCursor.digest("a", "b") != SearchAfterCursor.digest("a", "c")
    # Parts are separated, so a shifted boundary is still a different digest.
    assert SearchAfterCursor.digest("ab", "c") != SearchAfterCursor.digest("a", "bc")


def _setup_page_search(
    es_repository: _TestEsRepository,
) -> MagicMock:
    """Wire the mock Search chain used by get_page_by_query up to .sort()."""
    es_repository.object_type.model_validate.return_value = _TestEsRepositoryObject(
        test_int=1, test_str="a", test_str_list=[]
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    return (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: _apply_page_params
        .sort()
    )


def _setup_page_hits(
    execute_mock: MagicMock, *, sorts: list[list[Any]], total: int
) -> None:
    """Wire the response with one hit per entry in ``sorts``.

    ``sorts`` is what ES returns for the over-fetched ``page_size + 1`` request, so pass
    one more entry than the page size to simulate a further page.
    """
    hits = []
    for sort in sorts:
        hit = MagicMock()
        hit.meta.sort = sort
        hits.append(hit)

    response_hits = MagicMock()
    response_hits.__iter__.return_value = iter(hits)
    response_hits.total = SimpleNamespace(
        value=total,
        relation="eq" if total <= 10_000 else "gte",
    )
    execute_mock.return_value.hits = response_hits


def test_es_repository_get_page_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    # happens in: _apply_page_params (page size), _execute_search_with_query
    execute_mock = sort_mock.extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[[2.0, "a"], [1.5, "sort-key"]], total=25)

    result = es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
    )

    execute_mock.assert_called_once()
    # The total is the ES hit count, not the size of the returned page.
    assert result.total_hits == 25
    assert len(result.objs) == 2
    assert result.next_sort_id == [1.5, "sort-key"]


def test_es_repository_get_page_by_query_reports_a_further_page():
    """The lookahead hit is reported as has_more but never returned."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    execute_mock = sort_mock.extra().index().extra().execute
    _setup_page_hits(
        execute_mock,
        sorts=[[3.0, "a"], [2.0, "b"], [1.0, "lookahead"]],
        total=25,
    )

    result = es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
    )

    assert result.has_more is True
    assert len(result.objs) == 2
    # The cursor resumes after the last *returned* hit, not the lookahead.
    assert result.next_sort_id == [2.0, "b"]


def test_es_repository_get_page_by_query_exhausted_on_an_exact_page_multiple():
    """A last page that exactly fills the page size must still end pagination."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    execute_mock = sort_mock.extra().index().extra().execute
    # page_size + 1 were requested but only page_size exist.
    _setup_page_hits(execute_mock, sorts=[[3.0, "a"], [2.0, "b"]], total=4)

    result = es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
    )

    assert result.has_more is False
    assert len(result.objs) == 2


def test_es_repository_get_page_by_query_over_fetches_one_hit():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    execute_mock = sort_mock.extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[], total=0)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
    )

    # +1 so that has_more can be answered without a second query.
    sort_mock.extra.assert_any_call(size=3)


def test_es_repository_get_page_by_query_limits_the_fetched_source():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    es_repository.object_type.model_validate.return_value = _TestEsRepositoryObject(
        test_int=1, test_str="a", test_str_list=[]
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    source_mock = search_mock.highlight_options().highlight().query().source
    execute_mock = source_mock().sort().extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[], total=0)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
        source_includes=["test_str"],
    )

    source_mock.assert_any_call(includes=["test_str"])


def test_es_repository_get_page_by_query_empty_page_has_no_next_sort_id():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    execute_mock = sort_mock.extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[], total=25)

    result = es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
    )

    # An exhausted result set must be distinguishable from "start at page one".
    assert result.objs == []
    assert result.next_sort_id is None
    assert result.has_more is False


def test_es_repository_get_page_by_query_applies_search_after_only_with_a_sort_id():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    # The cursor adds one more .extra() to the chain, before the page size.
    execute_mock = sort_mock.extra().extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[[1.5, "next"]], total=25)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2, sort_id=[1.0, "previous"]),
    )

    execute_mock.assert_called_once()
    sort_mock.extra.assert_any_call(search_after=[1.0, "previous"])


@pytest.mark.parametrize("page_size", [0, -1])
def test_es_repository_get_page_by_query_clamps_a_page_size_below_one(page_size: int):
    """page_size is unbounded on PaginationParameters, and a page of no hits would
    report a further page — the lookahead hit — with no cursor to reach it with."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    sort_mock = _setup_page_search(es_repository)
    execute_mock = sort_mock.extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[[1.0, "a"], [0.5, "lookahead"]], total=25)

    result = es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=page_size),
    )

    sort_mock.extra.assert_any_call(size=2)
    assert len(result.objs) == 1
    assert result.has_more is True
    assert result.next_sort_id == [1.0, "a"]


def _stub_sort_field_mapping(
    es_repository: _TestEsRepository, field: str, field_type: str
) -> None:
    """Answer the mapping lookup of _get_sort_by_field with a field of that type."""
    index_mock = es_repository.document_type._index  # pylint: disable=protected-access
    index_mock.get_field_mapping.return_value = {
        es_repository.index_name: {
            "mappings": {
                field: {
                    "full_name": field,
                    "mapping": {field.split(".")[-1]: {"type": field_type}},
                }
            }
        }
    }


@pytest.mark.parametrize(
    "sort_direction, expected_missing",
    [
        # 0001-01-01T00:00:00Z
        ("desc", -62135596800000),
        # 9999-12-31T23:59:59.999Z
        ("asc", 253402300799999),
    ],
)
def test_es_repository_bounds_a_date_sort_so_its_cursor_can_be_sent_back(
    sort_direction: str, expected_missing: int
):
    """A document with no value for a date sort field is sorted with Long.MIN_VALUE
    descending, which is the cursor the page then hands to the client — and which ES
    refuses to parse back as a date, so paging stops at the first such document.

    An explicit bound keeps those documents last and survives search_after.
    """
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    _stub_sort_field_mapping(es_repository, "created", "date")
    sort_mock = _setup_page_search(es_repository)
    _setup_page_hits(sort_mock.extra().index().extra().execute, sorts=[], total=0)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
        sort_params=SortingParameters(
            sort_by_field="created",
            sort_direction=sort_direction,  # type: ignore[arg-type]
        ),
    )

    search_mock = es_repository.document_type.search.return_value
    search_mock.highlight_options().highlight().query().sort.assert_called_with(
        {"created": {"order": sort_direction, "missing": expected_missing}},
        "sort_unique",
    )


def test_es_repository_leaves_a_keyword_sort_without_a_missing_bound():
    """Only dates need one: ES reports a missing keyword as null and takes null back in
    search_after, so bounding it would invent a value the index does not hold."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    _stub_sort_field_mapping(es_repository, "source", "keyword")
    sort_mock = _setup_page_search(es_repository)
    _setup_page_hits(sort_mock.extra().index().extra().execute, sorts=[], total=0)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
        sort_params=SortingParameters(sort_by_field="source", sort_direction="desc"),
    )

    search_mock = es_repository.document_type.search.return_value
    search_mock.highlight_options().highlight().query().sort.assert_called_with(
        {"source": {"order": "desc"}},
        "sort_unique",
    )


def test_es_repository_get_page_by_query_requests_a_fallback_snippet():
    """Highlighting a field with no_match_size returns its leading characters when the
    query matched nothing in it, which saves fetching the whole field via _source."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    es_repository.object_type.model_validate.return_value = _TestEsRepositoryObject(
        test_int=1, test_str="a", test_str_list=[]
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    highlight_mock = search_mock.highlight_options().highlight().query().highlight
    execute_mock = highlight_mock().sort().extra().index().extra().execute
    _setup_page_hits(execute_mock, sorts=[], total=0)

    es_repository.get_page_by_query(
        query=QueryParameters(query_id="0123456789", search_string="a query"),
        pagination_params=PaginationParameters(page_size=2),
        leading_snippet_highlight=LeadingSnippetHighlight(
            field="test_str", max_chars=2000
        ),
    )

    highlight_mock.assert_any_call("test_str", no_match_size=2000)


def test_paged_search_result_rejects_a_further_page_without_a_cursor():
    """Callers page until has_more is False, so the combination has to be impossible to
    construct rather than checked at every call site."""
    with pytest.raises(ValidationError):
        PagedSearchResult[_TestEsRepositoryObject](
            objs=[],
            total_hits=25,
            count_relation="eq",
            has_more=True,
            next_sort_id=None,
        )


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

    # after .extra(size=...) set in _paginate_search before the loop
    search_pre_execute_mock = search_pre_execute_mock.extra()

    # 1st page (no search_after yet)
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

    # 2nd page (after search_after set from page 1)
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


def test_es_repository_get_generator_by_query_raises_on_an_expired_pit():
    """A scan whose snapshot lapses mid-run stops, rather than finishing against a
    different one.

    Opening a fresh point-in-time and replaying the search_after tuple would resume from
    sort values that mean nothing in the new snapshot, so the rest of the scan would
    silently skip or repeat documents. Raising lets the task retry and start the sweep
    over, which is the only way to cover every document exactly once.
    """
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )

    initial_query_id = "initial query id"

    open_point_in_time = MagicMock()
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

    # after .extra(size=...) set in _paginate_search before the loop
    search_pre_execute_mock = search_pre_execute_mock.extra()

    # 1st page works (no search_after yet)
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

    # 2nd page: the point-in-time has gone
    search_pre_execute_mock = search_pre_execute_mock.extra()
    search_page2_execute_mock = search_pre_execute_mock.index().extra().execute
    search_page2_execute_mock.side_effect = NotFoundError(
        "search phase execution exception", MagicMock(), None
    )

    generator = es_repository.get_generator_by_query(
        QueryParameters(query_id=initial_query_id, search_string="just a random query")
    )

    with pytest.raises(PointInTimeExpiredError):
        list(generator)

    search_execute_mock.assert_called_once()
    search_page2_execute_mock.assert_called_once()
    # No silent recovery: a replacement snapshot is the caller's decision, because
    # only the caller knows the scan has to restart rather than continue.
    es_repository.elasticsearch_mock.open_point_in_time.assert_not_called()


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
        .extra()  # scan_page_size
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


def test_es_repository_full_scan_opens_pit_when_query_id_is_none():
    """When query_id is None and no pagination_params, _paginate_search must open a PIT
    automatically so that all pages see a consistent snapshot of the index."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    auto_pit_id = "auto-opened-pit-id"
    es_repository.elasticsearch_mock.open_point_in_time = MagicMock(
        return_value={"id": auto_pit_id}
    )

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
        .extra()  # scan_page_size
        # happens in: _execute_search_with_query (PIT path)
        .index()
        .extra()
    )

    list(
        es_repository.get_generator_by_query(
            QueryParameters(query_id=None, search_string="just a random query")
        )
    )

    # A PIT must have been opened automatically
    es_repository.elasticsearch_mock.open_point_in_time.assert_called_once()
    # And the query must have been executed via the PIT path, not the no-PIT shortcut
    search_pre_execute_mock.execute.assert_called_once()


def test_es_repository_get_id_generator_by_query_uses_large_scan_page_size():
    """get_id_generator_by_query must use _ID_SCAN_PAGE_SIZE, not DEFAULT_PAGE_SIZE, so
    that full-scan archive tasks make far fewer round trips to Elasticsearch."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock

    # Follow the actual call chain inside get_id_generator_by_query:
    # _get_search_by_query → .source() → _paginate_search: .sort()
    sort_mock = search_mock.highlight_options().highlight().query().source().sort()

    list(
        es_repository.get_id_generator_by_query(
            QueryParameters(query_id="0123456789", search_string="just a random query")
        )
    )

    # The first .extra() call in _paginate_search must set size=_ID_SCAN_PAGE_SIZE
    sort_mock.extra.assert_called_once_with(size=_ID_SCAN_PAGE_SIZE)


@pytest.mark.parametrize(
    "document_dict, expected_sort_value",
    [
        pytest.param(
            {"tika_meta": {"dcterms_created": "2016-06-01T16:35:07+00:00"}},
            "2016-06-01T16:35:07+00:00",
            id="field-present",
        ),
        pytest.param({"tika_meta": {}}, "", id="leaf-missing"),
        pytest.param({}, "", id="whole-branch-missing"),
        pytest.param({"tika_meta": "not-an-object"}, "", id="path-not-traversable"),
    ],
)
def test_es_repository_reports_no_sort_value_for_a_document_without_one(
    document_dict: dict, expected_sort_value: str
):
    """The descent stops as soon as the path runs out, and what it reached by then is
    not the value: handing it on puts the half-walked document in the field the client
    displays as the sort value."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    execute_mock = (
        search_mock.highlight_options()
        .highlight()
        .query()
        .source()
        .sort()
        .extra()
        .index()
        .extra()
        .execute
    )
    hit = MagicMock()
    hit.to_es_dict.return_value = dict(document_dict)
    hit.meta.sort = [1.0, "a"]
    execute_mock.return_value.hits = [hit]

    result = list(
        es_repository.get_id_generator_by_query(
            query=QueryParameters(query_id="0123456789", search_string="a query"),
            pagination_params=PaginationParameters(page_size=1),
            sort_params=SortingParameters(
                sort_by_field="tika_meta.dcterms_created", sort_direction="desc"
            ),
        )
    )

    assert [entry.sort_value for entry in result] == [expected_sort_value]


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


def test_es_repository_count_by_query_no_pit():
    """When query_id is None, count_by_query executes directly without a PIT."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
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
        # happens in: _execute_search_with_query (no-PIT path: direct execute)
        .execute
    )
    hits_mock = MagicMock()
    hits_mock.hits.total.value = 42  # pylint: disable=no-member
    search_pre_count_mock.return_value = hits_mock
    count = es_repository.count_by_query(
        QueryParameters(query_id=None, search_string="just a random query")
    )
    assert count == 42
    # .index() and the PIT .extra() must NOT be called in the no-PIT path
    search_mock.highlight_options().highlight().query().__getitem__(
        slice(0, 0, None)
    ).extra().index.assert_not_called()


def test_es_repository_count_and_score_stats_by_query():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    # pylint: disable=unnecessary-dunder-call
    search_pre_execute_mock = (
        search_mock
        # happens in: _get_search_by_query
        .highlight_options()
        .highlight()
        .query()
        # happens in: count_and_score_stats_by_query
        .__getitem__(slice(0, _SCORE_SAMPLE_SIZE, None))
        .extra()
        # happens in: _execute_search_with_query
        .index()
        .extra()
        .execute
    )

    hit1 = MagicMock()
    hit1.meta.score = 4.0
    hit2 = MagicMock()
    hit2.meta.score = 2.0
    result_mock = MagicMock()
    result_mock.hits.total.value = 50  # pylint: disable=no-member
    result_mock.hits.max_score = 4.0
    result_mock.hits.__iter__ = lambda _self: iter([hit1, hit2])
    search_pre_execute_mock.return_value = result_mock

    stats = es_repository.count_and_score_stats_by_query(
        QueryParameters(query_id="0123456789", search_string="test query")
    )
    assert isinstance(stats, QueryScoreStats)
    assert stats.total == 50
    assert stats.max_score == 4.0
    assert stats.avg_score == 3.0


def test_es_repository_count_and_score_stats_by_query_no_hits():
    """When no hits are returned, max_score and avg_score should be None."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    # pylint: disable=unnecessary-dunder-call
    search_pre_execute_mock = (
        search_mock.highlight_options()
        .highlight()
        .query()
        .__getitem__(slice(0, _SCORE_SAMPLE_SIZE, None))
        .extra()
        .index()
        .extra()
        .execute
    )

    result_mock = MagicMock()
    result_mock.hits.total.value = 0  # pylint: disable=no-member
    result_mock.hits.max_score = None
    result_mock.hits.__iter__ = lambda _self: iter([])
    search_pre_execute_mock.return_value = result_mock

    stats = es_repository.count_and_score_stats_by_query(
        QueryParameters(query_id="0123456789", search_string="nothing")
    )
    assert stats.total == 0
    assert stats.max_score is None
    assert stats.avg_score is None


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
def test_es_repository_get_by_id_with_query_no_pit(obj: _TestEsRepositoryObject):
    """When query_id is None, get_by_id_with_query executes directly without a PIT."""
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
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
        # happens in: _execute_search_with_query (no-PIT path: direct execute)
        .execute
    )

    es_repository.get_by_id_with_query(
        obj.id_,
        QueryParameters(query_id=None, search_string="just a random query"),
        full_highlight_context=False,
    )

    search_pre_execute_mock.assert_called_once()
    # .index() must NOT be called in the no-PIT path
    search_mock.highlight_options().highlight().query().filter().index.assert_not_called()


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
    document_mock.meta = MagicMock()
    document_mock.meta.seq_no = 1
    document_mock.meta.primary_term = 1

    es_repository.document_type.return_value = document_mock

    # Configure object_type.model_validate to return an object with valid es_meta
    # (this is called by _document_to_object internally)
    returned_obj = obj.model_copy(deep=True)
    returned_obj.es_meta.seq_no = 1
    returned_obj.es_meta.primary_term = 1
    es_repository.object_type.model_validate.return_value = returned_obj

    es_repository.save(obj)

    document_mock.save.assert_called_once_with(
        using=es_repository.elasticsearch_mock,
        refresh="wait_for",
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
    # Configure meta attributes that update() accesses after the update
    document_mock.meta = MagicMock()
    document_mock.meta.seq_no = 1
    document_mock.meta.primary_term = 1
    es_repository.document_type.return_value = document_mock

    # Capture original values before update (update modifies obj.es_meta)
    original_seq_no = obj.es_meta.seq_no
    original_primary_term = obj.es_meta.primary_term

    # Configure object_type.model_validate to return an object with valid es_meta
    # (this is called by _document_to_object internally)
    returned_obj = obj.model_copy(deep=True)
    returned_obj.es_meta.seq_no = 2
    returned_obj.es_meta.primary_term = 1
    es_repository.object_type.model_validate.return_value = returned_obj

    es_repository.update(obj)

    # update() now uses to_es_dict() which applies mode="json" serialization
    # (UUIDs become strings)
    document_mock.update.assert_called_once_with(
        id=str(obj.id_),
        deduplication_fingerprint=obj.deduplication_fingerprint,
        sort_unique=str(obj.sort_unique),
        hidden=obj.hidden,
        test_int=obj.test_int,
        test_str=obj.test_str,
        test_str_list=obj.test_str_list,
        using=es_repository.elasticsearch_mock,
        refresh="wait_for",
        if_seq_no=original_seq_no,
        if_primary_term=original_primary_term,
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
    # Configure meta attributes that update() accesses after the update
    document_mock.meta = MagicMock()
    document_mock.meta.seq_no = 1
    document_mock.meta.primary_term = 1
    es_repository.document_type.return_value = document_mock

    # Capture original values before update (update modifies obj.es_meta)
    original_seq_no = obj.es_meta.seq_no
    original_primary_term = obj.es_meta.primary_term

    # Configure object_type.model_validate to return an object with valid es_meta
    # (this is called by _document_to_object internally)
    returned_obj = obj.model_copy(deep=True)
    returned_obj.es_meta.seq_no = 2
    returned_obj.es_meta.primary_term = 1
    es_repository.object_type.model_validate.return_value = returned_obj

    es_repository.update(obj, include={"test_int", "test_str"})

    document_mock.update.assert_called_once_with(
        test_int=obj.test_int,
        test_str=obj.test_str,
        using=es_repository.elasticsearch_mock,
        refresh="wait_for",
        if_seq_no=original_seq_no,
        if_primary_term=original_primary_term,
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
    # Configure meta attributes that update() accesses after the update
    document_mock.meta = MagicMock()
    document_mock.meta.seq_no = 1
    document_mock.meta.primary_term = 1
    es_repository.document_type.return_value = document_mock

    # Capture original values before update (update modifies obj.es_meta)
    original_seq_no = obj.es_meta.seq_no
    original_primary_term = obj.es_meta.primary_term

    # Configure object_type.model_validate to return an object with valid es_meta
    # (this is called by _document_to_object internally)
    returned_obj = obj.model_copy(deep=True)
    returned_obj.es_meta.seq_no = 2
    returned_obj.es_meta.primary_term = 1
    es_repository.object_type.model_validate.return_value = returned_obj

    es_repository.update(obj, exclude={"test_int", "test_str"})

    # update() now uses to_es_dict() which applies mode="json" serialization
    # (UUIDs become strings)
    document_mock.update.assert_called_once_with(
        id=str(obj.id_),
        deduplication_fingerprint=obj.deduplication_fingerprint,
        sort_unique=str(obj.sort_unique),
        hidden=obj.hidden,
        test_str_list=obj.test_str_list,
        using=es_repository.elasticsearch_mock,
        refresh="wait_for",
        if_seq_no=original_seq_no,
        if_primary_term=original_primary_term,
    )


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_delete_by_id(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    es_repository.document_type.return_value = document_mock

    result = es_repository.delete_by_id(obj.id_)

    assert result is True
    document_mock.delete.assert_called_once_with(
        using=es_repository.elasticsearch_mock,
        refresh="wait_for",
    )


@pytest.mark.parametrize(
    "obj",
    get_test_repository_object_instances(),
)
def test_es_repository_delete_by_id_not_found(obj: _TestEsRepositoryObject):
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    document_mock = MagicMock(spec=_TestEsDocument)
    document_mock.delete.side_effect = NotFoundError(
        "document not found", MagicMock(), None
    )
    es_repository.document_type.return_value = document_mock

    result = es_repository.delete_by_id(obj.id_)

    assert result is False


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


class _TestRootTaskInformationRepository(RootTaskInformationRepository):
    """Test subclass with mocked document_type and elasticsearch."""

    def __init__(
        self,
        query_builder: QueryBuilder,
        pubsub_service: PubSubService,
    ):
        super().__init__(query_builder, pubsub_service)
        self.document_type_mock: MagicMock = MagicMock(spec=_EsRootTaskInformation)
        self.elasticsearch_mock: Elasticsearch = MagicMock(spec=Elasticsearch)

    @property
    def _document_type(self) -> type[_EsRootTaskInformation]:
        return self.document_type_mock  # type: ignore[return-value]

    @property
    def _elasticsearch(self) -> Elasticsearch:
        return self.elasticsearch_mock


def test_root_task_information_repository_get_by_root_task_id():
    """Test RootTaskInformationRepository.get_by_root_task_id method."""
    es_repository = _TestRootTaskInformationRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
    )

    # setup document that will be returned
    document = _EsRootTaskInformation(
        {
            "_id": TestValueDefaults.test_uuid,
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
        root_task_id=str(TestValueDefaults.test_uuid),
        object_id=str(TestValueDefaults.test_uuid),
    )

    # setup search mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type_mock.search.return_value = search_mock

    # setup hits - response[0] should return the document
    hits_mock = MagicMock()
    hits_mock.__len__.return_value = 1
    hits_mock.__getitem__.return_value = document
    search_mock.query.return_value.execute.return_value = hits_mock

    result = es_repository.get_by_root_task_id(TestValueDefaults.test_uuid)

    search_mock.query.assert_called_once_with(
        "match", root_task_id=str(TestValueDefaults.test_uuid)
    )
    assert result.root_task_id == TestValueDefaults.test_uuid
    assert result.object_id == TestValueDefaults.test_uuid


def test_root_task_information_repository_get_by_root_task_id_not_found():
    """Test RootTaskInformationRepository.get_by_root_task_id raises when not found."""
    es_repository = _TestRootTaskInformationRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
    )

    # setup search mock
    search_mock = MagicMock(spec=Search)
    es_repository.document_type_mock.search.return_value = search_mock

    # setup empty hits
    hits_mock = MagicMock()
    hits_mock.__len__.return_value = 0
    search_mock.query.return_value.execute.return_value = hits_mock

    with pytest.raises(ValueError, match="Root task info with id .* not found"):
        es_repository.get_by_root_task_id(TestValueDefaults.test_uuid)


def test_es_repository_count():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    es_repository.document_type.search.return_value = search_mock
    # pylint: disable=unnecessary-dunder-call
    search_pre_execute_mock = search_mock.__getitem__(slice(0, 0, None)).extra().execute
    hits_mock = MagicMock()
    hits_mock.hits.total.value = 42  # pylint: disable=no-member
    search_pre_execute_mock.return_value = hits_mock

    count = es_repository.count()

    assert count == 42


def test_es_repository_flush():
    es_repository = _TestEsRepository(
        query_builder=get_query_builder(),
        pubsub_service=get_pubsub_service(),
        mock_types=True,
    )
    search_mock = MagicMock(spec=Search)
    query_mock = MagicMock(spec=Search)
    search_mock.query.return_value = query_mock
    es_repository.document_type.search.return_value = search_mock

    es_repository.flush()

    search_mock.query.assert_called_once_with("match_all")
    query_mock.params.assert_called_once_with(refresh=True)
    query_mock.params.return_value.delete.assert_called_once()
