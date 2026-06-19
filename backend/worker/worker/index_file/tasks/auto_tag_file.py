import logging
from collections import defaultdict

from celery import chain
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_repository,
    get_lazybytes_service,
)
from common.file.file_repository import Embedding, File, Tag
from common.services.lazybytes_service import TempTypedLazyBytes
from common.services.query_builder import QueryParameters
from pydantic import BaseModel

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.settings import settings
from worker.utils.clustering import kde_filter_highest_cluster
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

MAX_FILES_KNN_SEARCH = 10

AUTO_TAG_PREFIX = "🤖 "


class FileTagInfo(BaseModel):
    tags: list[Tag]
    score: float


class FileInfo(BaseModel):
    short_name: str
    tags: list[Tag]

    @staticmethod
    def from_file(file: File) -> "FileInfo":
        return FileInfo(short_name=file.short_name, tags=file.tags)


class TagScore(BaseModel):
    tag: str
    score: float


def signature(file: File) -> Signature:
    if settings.skip_auto_tag_file_while_indexing:
        return noop.s()

    file_info = FileInfo.from_file(file)

    return chain(
        fetch_files_embeddings.s(file),
        calculate_tag_score.s(file_info),
        filter_scored_tags.s(),
        persist_add_auto_tag.s(file.id_),
    )


@app.task(base=FileIndexingTask)
def noop(*_, **__):
    pass


@app.task(base=FileIndexingTask)
def fetch_files_embeddings(
    embeddings_bytes_lazy: list[TempTypedLazyBytes[Embedding]], file: File
) -> list[FileTagInfo]:
    similar_files: list[FileTagInfo] = []

    query = QueryParameters(
        query_id=get_file_repository().open_point_in_time(),
        search_string=f'tags:* !id:"{file.id_}"',
    )

    for embedding_bytes_lazy in embeddings_bytes_lazy:
        embedding = get_lazybytes_service().load_object(embedding_bytes_lazy)

        # We receive the embeddings from creation, therefore the dense vector is present.
        if embedding.vector is None:
            logger.warning(
                "Embedding is missing dense vector - this should not happen. File: %s",
                file.short_name,
            )
            continue

        for knn_embedding in get_file_repository().get_embedding_generator_by_knn(
            query=query,
            embedding_vectors=[embedding.vector],
            k=MAX_FILES_KNN_SEARCH,
        ):
            found_file = get_file_repository().get_by_id(knn_embedding.file_id)
            similarity = knn_embedding.text_score

            if found_file:
                logger.debug(
                    "File %s has similarity score %.4f (compared to file %s)",
                    found_file.short_name,
                    similarity,
                    file.short_name,
                )

            if found_file and similarity > settings.auto_tag_file_similarity_threshold:
                similar_files.append(
                    FileTagInfo(score=similarity, tags=found_file.tags)
                )

    return similar_files


@app.task(base=FileIndexingTask)
def calculate_tag_score(
    similar_files: list[FileTagInfo],
    file_info: FileInfo,
) -> list[TagScore]:
    all_tags: list[TagScore] = [
        TagScore(tag=tag, score=similar_file.score)
        for similar_file in similar_files
        for tag in similar_file.tags
    ]

    scores_by_tag: dict[str, list[float]] = defaultdict(list)
    for tag_score in all_tags:
        if tag_score.tag.startswith(AUTO_TAG_PREFIX):
            continue
        scores_by_tag[tag_score.tag].append(tag_score.score)

    tags_avg_score: list[TagScore] = []
    for tag, scores in scores_by_tag.items():
        avg_score = sum(scores) / len(scores)
        tags_avg_score.append(TagScore(tag=tag, score=avg_score))

    # Remove tags already assigned to the current file
    valid_tags: list[TagScore] = [
        t for t in tags_avg_score if t.tag not in file_info.tags
    ]

    for valid_tag in valid_tags:
        logger.info(
            "Candidate tag %s with score %.4f for file %s",
            valid_tag.tag,
            valid_tag.score,
            file_info.short_name,
        )

    return valid_tags


@app.task(base=FileIndexingTask)
def filter_scored_tags(scored_tags: list[TagScore]) -> list[TagScore]:
    if len(scored_tags) < 1:
        logger.info("No similar files with tags found")
        return scored_tags

    filtered_tags = kde_filter_highest_cluster(scored_tags, lambda ts: ts.score)

    logger.info(
        "Filtered tags for file. before: %d after: %d",
        len(scored_tags),
        len(filtered_tags),
    )

    return filtered_tags


@persisting_task(app, IndexingPersister)
def persist_add_auto_tag(persister: IndexingPersister, tags: list[TagScore]):
    for tag in tags:
        persister.add_tag(AUTO_TAG_PREFIX + tag.tag)
