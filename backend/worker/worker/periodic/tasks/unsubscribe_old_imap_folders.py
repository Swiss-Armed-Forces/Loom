import logging
from datetime import datetime, timedelta, timezone

from celery.canvas import Signature
from common.dependencies import get_celery_app, get_imap_service

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.settings import settings

logger = logging.getLogger(__name__)

app = get_celery_app()


def signature() -> Signature:
    return unsubscribe_old_imap_folders_task.s()


@app.task(base=PeriodicTask)
def unsubscribe_old_imap_folders_task(
    days_before_unsubscribe: int | None = settings.imap_folder_days_before_unsubscribe,
):
    if days_before_unsubscribe is None:
        return
    logger.info("Checking subscribed IMAP folders for old emails")

    imap_service = get_imap_service()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_before_unsubscribe)

    subscribed_folders = imap_service.list_subscribed_folders()

    for folder in subscribed_folders:
        latest_date = imap_service.get_latest_email_date(folder)

        if latest_date is not None and latest_date > cutoff_date:
            # still relevant
            continue
        logger.info(
            "Unsubscribing from old folder: %s (latest: %s)", folder, latest_date
        )
        imap_service.unsubscribe_folder(folder)
