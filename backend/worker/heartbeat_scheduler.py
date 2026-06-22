"""Custom Celery beat scheduler that writes a heartbeat file on each tick."""

import datetime

from celery.beat import PersistentScheduler
from common.dependencies import get_celery_inspect_service

HEARTBEAT_FILE = "/tmp/beat_heartbeat"


class HeartbeatScheduler(PersistentScheduler):
    max_interval = 60  # seconds; caps sleep between ticks so heartbeat stays fresh

    def apply_entry(self, entry, producer=None):  # type: ignore[override]
        if get_celery_inspect_service().is_beat_paused():
            # Beat is paused: advance the schedule entry so it doesn't fire
            # multiple times on resume, but do not send the task to the broker.
            self.reserve(entry)  # type: ignore[attr-defined]
            return
        super().apply_entry(entry, producer=producer)  # type: ignore[misc]

    def tick(self, *args, **kwargs):  # type: ignore[override]
        result = super().tick(*args, **kwargs)
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            f.write(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())
        return result
