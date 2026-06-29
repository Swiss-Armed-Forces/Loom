import logging
import uuid

from common.dependencies import get_celery_app, get_file_storage_service
from common.models.base_repository import REPOSITORY_INSTANCES
from common.services.lazybytes_service import FileStorageLazyBytes

from worker.periodic.infra.periodic_task import PeriodicTask

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(base=PeriodicTask)
def search_and_remove_file_storage_object(*_, service_id: str, **__):
    service_uuid = uuid.UUID(service_id)
    repos = list(REPOSITORY_INSTANCES.values())
    referenced = any(
        repo.is_file_storage_service_id_referenced(service_uuid) for repo in repos
    )
    if referenced:
        logger.debug("Service ID %s is still referenced, skipping", service_id)
        return
    logger.info("Removing orphaned file storage object %s", service_id)
    get_file_storage_service().delete(FileStorageLazyBytes(service_id=service_uuid))
