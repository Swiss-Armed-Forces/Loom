"""Custom Celery beat scheduler that writes a heartbeat file on each tick."""

import datetime

from celery.beat import PersistentScheduler

HEARTBEAT_FILE = "/tmp/beat_heartbeat"


class HeartbeatScheduler(PersistentScheduler):
    max_interval = 60  # seconds; caps sleep between ticks so heartbeat stays fresh

    def tick(self, *args, **kwargs):  # type: ignore[override]
        result = super().tick(*args, **kwargs)
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            f.write(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())
        return result
