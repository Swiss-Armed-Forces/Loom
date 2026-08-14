"""Custom Celery beat scheduler that writes a heartbeat file on each dispatched task."""

import datetime
import logging

from celery.beat import PersistentScheduler
from common.dependencies import get_celery_inspect_service

from worker.settings import settings

logger = logging.getLogger(__name__)


class HeartbeatScheduler(PersistentScheduler):
    max_interval = 60  # seconds; caps sleep between ticks so heartbeat stays fresh

    def apply_entry(self, entry, producer=None):  # type: ignore[override]
        if get_celery_inspect_service().is_beat_paused():
            # Beat is paused: advance the schedule entry so it doesn't fire
            # multiple times on resume, but do not send the task to the broker.
            self.reserve(entry)  # type: ignore[attr-defined]
            return
        super().apply_entry(entry, producer=producer)  # type: ignore[misc]

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        result = super().apply_async(
            entry,
            producer=producer,
            advance=advance,
            **kwargs,
        )
        # failing to write heartbeat file is not considered a failed dispatched task
        try:
            with open(settings.heartbeat_file_name, "w", encoding="utf-8") as f:
                f.write(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())
        except OSError:
            logger.exception("failed to write heartbeat file")
        return result
