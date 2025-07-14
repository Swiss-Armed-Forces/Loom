import logging
from io import BytesIO

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.utils.object_id_str import ObjectIdStr
from wand.exceptions import MissingDelegateError, WandException
from wand.image import Image

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature(file_content: LazyBytes, file: File) -> Signature:
    """Create the signature for the tasks that create a thumbnail."""
    return group(
        chain(
            create_resized_image.s(file, file_content, 300),
            persist_thumbnail_task.s(file),
        ),
        chain(
            create_resized_image.s(file, file_content, 1500),
            persist_preview_task.s(file),
        ),
    )


@app.task(base=FileIndexingTask)
def create_resized_image(
    file: File, file_content: LazyBytes, width: int
) -> ObjectIdStr | None:
    """Returns the filename of the create thumbnail."""
    with get_lazybytes_service().load_file(file_content) as loaded_file:
        try:
            with Image(file=loaded_file) as image:
                if len(image.sequence) > 1:
                    image = Image(image.sequence[0])
                if image.width > width:
                    image.transform(resize=f"{width}")
                blob = image.make_blob(format="png")
        except MissingDelegateError as ex:
            logger.info(
                "Type is not supported by Wand! %s: %s",
                type(ex),
                ex,
            )
            return None
        except WandException as ex:
            if file.magic_file_type is None or "image" in file.magic_file_type:
                logger.error(
                    "Unable to create thumbnail with Wand! %s: %s",
                    type(ex),
                    ex,
                )
            return None
    thumbnail_file_id = get_file_storage_service().upload_from_stream(
        # We leave the filename empty in the upload because this service is only concerned by
        # the data itself. Two writes to the same filename (in this case the empty string) does
        # not mean that data will be overwritten in GridFS.
        "",
        BytesIO(blob),
    )
    return ObjectIdStr(thumbnail_file_id)


@persisting_task(app, IndexingPersister)
def persist_thumbnail_task(
    persister: IndexingPersister, thumbnail_file_id: ObjectIdStr | None
):
    """Persists the thumbnail."""
    if thumbnail_file_id is not None:
        persister.set_thumbnail_file_id(thumbnail_file_id)


@persisting_task(app, IndexingPersister)
def persist_preview_task(
    persister: IndexingPersister, preview_file_id: ObjectIdStr | None
):
    """Persists the preview."""
    if preview_file_id is not None:
        persister.set_preview_file_id(preview_file_id)
