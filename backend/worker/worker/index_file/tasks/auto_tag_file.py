import itertools
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

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
AUTO_TAG_KNN_BATCH_SIZE = 32
NUM_KNN_QUERY_WORKERS = 4
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
    embeddings_bytes_lazy: list[TempTypedLazyBytes[Embedding]],
    file: File,
) -> list[FileTagInfo]:
    """Batch all embeddings and perform parallel kNN requests to find similar files
    exceeding the configured threshold."""
    if not embeddings_bytes_lazy:
        return []

    batches = [
        embeddings_bytes_lazy[i : i + AUTO_TAG_KNN_BATCH_SIZE]
        for i in range(0, len(embeddings_bytes_lazy), AUTO_TAG_KNN_BATCH_SIZE)
    ]

    logger.info(
        "Split %d embeddings into %d batches for %d workers for auto-tag KNN search (file: %s)",
        len(embeddings_bytes_lazy),
        len(batches),
        NUM_KNN_QUERY_WORKERS,
        file.short_name,
    )

    # NOTE: We don't use `self.replace()` here as that would create a nested replace within
    # `create_embedding_task`, which in turn causes issues with other celery tasks.
    with ThreadPoolExecutor(max_workers=NUM_KNN_QUERY_WORKERS) as pool:
        batched_results = list(
            pool.map(
                lambda batch: fetch_embeddings_batch(batch, file), batches, timeout=None
            )
        )

    results = list(itertools.chain.from_iterable(batched_results))
    logger.debug(
        "Got %d kNN results from %d batches",
        len(results),
        len(batches),
    )
    return results


def fetch_embeddings_batch(
    batch: list[TempTypedLazyBytes[Embedding]],
    file: File,
) -> list[FileTagInfo]:
    """Search for a batch of embeddings via a single KNN query."""
    embeddings_batch: list[list[float]] = []
    for embedding_bytes_lazy in batch:
        embedding = get_lazybytes_service().load_object(embedding_bytes_lazy)

        if embedding.vector is None:
            logger.warning(
                "Embedding is missing dense embedding vector - this should not happen."
                " File: %s",
                file.short_name,
            )
            continue

        embeddings_batch.append(embedding.vector)

    if not embeddings_batch:
        return []

    query = QueryParameters(
        search_string=f'tags:* !id:"{file.id_}"',
    )

    logger.debug(
        "Searching for similar files by KNN for batch of %d embeddings (file: %s)",
        len(embeddings_batch),
        file.short_name,
    )

    similar_files: list[FileTagInfo] = []
    for knn_embedding in get_file_repository().get_embedding_generator_by_knn(
        query=query,
        embedding_vectors=embeddings_batch,
        k=MAX_FILES_KNN_SEARCH,
    ):
        logger.debug("Processing candidate similarity match for %s", file.short_name)

        similarity = knn_embedding.text_score
        if similarity > settings.auto_tag_file_similarity_threshold:
            similar_file = get_file_repository().get_by_id(knn_embedding.file_id)
            if similar_file:
                logger.debug(
                    "Found similar file %s to file %s (similarity score: %.4f)",
                    similar_file.short_name,
                    file.short_name,
                    similarity,
                )
                similar_files.append(
                    FileTagInfo(score=similarity, tags=similar_file.tags)
                )
            else:
                logger.warning(
                    "Failed to fetch similar file with id '%s'",
                    knn_embedding.file_id,
                )
        else:
            logger.debug(
                "File with id %s not similar enough to file named %s (similarity score: %.4f)",
                knn_embedding.file_id,
                file.short_name,
                similarity,
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
