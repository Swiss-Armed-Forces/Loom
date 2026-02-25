import logging

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from common.utils.object_id_str import ObjectIdStr
from pydantic import BaseModel
from wand.exceptions import MissingDelegateError, WandException
from wand.image import Image

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.tasks.render import (
    RenderFile,
    render_browser_to_pdf_task,
    render_office_to_pdf_task,
)
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


class ThumbnailFile(BaseModel):
    cache_key: str
    render_file: RenderFile

    @staticmethod
    def from_file(file: File) -> "ThumbnailFile":
        return ThumbnailFile(
            cache_key=file.sha256, render_file=RenderFile.from_file(file)
        )


def signature(file: File, file_content: LazyBytes) -> Signature:
    thumbnail_file = ThumbnailFile.from_file(file)
    return group(
        chain(
            thumbnail_image_png_task.s(file_content, thumbnail_file),
            group(
                persist_thumbnail_total_frames.s(file),
                chain(
                    upload_thumbnail_task.s(file.short_name),
                    group(
                        persist_thumbnail_task.s(file),
                        chain(
                            group(
                                thumbnail_fallback_render_office_to_pdf_task.s(
                                    file_content, thumbnail_file
                                ),
                                thumbnail_fallback_render_browser_to_pdf_task.s(
                                    file_content, thumbnail_file
                                ),
                            ),
                            thumbnail_fallback_pick.s(),
                            thumbnail_fallback_image_png_task.s(thumbnail_file),
                            group(
                                persist_thumbnail_total_frames.s(file),
                                chain(
                                    upload_thumbnail_task.s(file.short_name),
                                    persist_thumbnail_task.s(file),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def signature_pass_file_content(
    file: File,
    thumbnail_file: ThumbnailFile,
) -> Signature:
    return chain(
        thumbnail_image_png_task.s(thumbnail_file),
        group(
            persist_thumbnail_total_frames.s(file),
            chain(
                upload_thumbnail_task.s(file.short_name),
                persist_thumbnail_task.s(file),
            ),
        ),
    )


class Thumbnail(BaseModel):
    thumbnail: LazyBytes
    total_frames: int = 0


def _thumbnail_image_png_task(file_content: LazyBytes | None) -> Thumbnail | None:
    if file_content is None:
        return None

    total_frames = 0
    try:
        with (
            get_lazybytes_service().load_file(file_content) as fd,
            Image(file=fd) as image,
        ):
            total_frames = len(image.sequence)

            if len(image.sequence) > 1:
                # Keep only the frames we'll render
                del image.sequence[settings.thumbnail_max_frames_montage :]

                image.montage()
            image.transform(
                resize=f"{settings.thumbnail_width}x{settings.thumbnail_height}>"
            )
            image.unsharp_mask()
            blob = image.make_blob(format="png")
    except (MissingDelegateError, WandException):
        logger.warning(
            "Unable to render thumbnail with Wand",
            exc_info=True,
        )
        return None

    if not isinstance(blob, bytes):
        return None

    blob_lazy = get_lazybytes_service().from_bytes(blob)
    return Thumbnail(
        thumbnail=blob_lazy,
        total_frames=total_frames,
    )


# This task is different from fallback_thumbnail_image_png_task because of caching
@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, thumbnail_file: thumbnail_file.cache_key)
def thumbnail_image_png_task(
    file_content: LazyBytes | None, _: ThumbnailFile
) -> Thumbnail | None:
    return _thumbnail_image_png_task(file_content)


@app.task(base=FileIndexingTask)
def upload_thumbnail_task(
    thumbnail: Thumbnail | None, file_short_name: str
) -> ObjectIdStr | None:
    if thumbnail is None:
        return None
    with get_lazybytes_service().load_file(thumbnail.thumbnail) as fd:
        file_id = get_file_storage_service().upload_from_stream(
            f"{file_short_name}.thumbnail.png",
            fd,
        )
    return ObjectIdStr(file_id)


@persisting_task(app, IndexingPersister)
def persist_thumbnail_total_frames(
    persister: IndexingPersister,
    thumbnail: Thumbnail | None,
):
    if thumbnail is None:
        return
    persister.set_thumbnail_total_frames(thumbnail.total_frames)


@app.task(base=FileIndexingTask)
def thumbnail_fallback_render_office_to_pdf_task(
    thumbnail_file_id: ObjectIdStr | None,
    file_content: LazyBytes | None,
    thumbnail_file: ThumbnailFile,
) -> LazyBytes | None:
    if thumbnail_file_id is not None:
        return None
    return render_office_to_pdf_task(file_content, thumbnail_file.render_file)


@app.task(base=FileIndexingTask)
def thumbnail_fallback_render_browser_to_pdf_task(
    thumbnail_file_id: ObjectIdStr | None,
    file_content: LazyBytes | None,
    thumbnail_file: ThumbnailFile,
) -> LazyBytes | None:
    if thumbnail_file_id is not None:
        return None
    return render_browser_to_pdf_task(file_content, thumbnail_file.render_file)


@app.task(base=FileIndexingTask)
def thumbnail_fallback_pick(fallbacks: list[LazyBytes | None]) -> LazyBytes | None:
    for fallback in fallbacks:
        if fallback is not None:
            return fallback
    return None


# This task is different from thumbnail_image_png_task because of caching
@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, thumbnail_file: thumbnail_file.cache_key)
def thumbnail_fallback_image_png_task(
    file_content: LazyBytes | None, _: ThumbnailFile
) -> Thumbnail | None:
    return _thumbnail_image_png_task(file_content)


@persisting_task(app, IndexingPersister)
def persist_thumbnail_task(
    persister: IndexingPersister, thumbnail_file_id: ObjectIdStr | None
):
    if thumbnail_file_id is None:
        return
    persister.set_thumbnail_file_id(thumbnail_file_id)
