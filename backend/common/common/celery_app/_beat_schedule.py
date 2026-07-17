from datetime import datetime, timedelta, timezone

from celery.schedules import BaseSchedule, crontab, schedstate


class _NeverSchedule(BaseSchedule):
    """A schedule that never fires automatically.

    Allows a task to exist in the beat schedule (and be triggerable via the API) without
    ever running on its own schedule.

    ``is_due()`` unconditionally returns ``(False, 86400)`` — no date arithmetic that
    could accidentally yield a zero remainder and trigger the task.

    ``now()`` returns real UTC time, which matters because Celery's ``_when()`` computes
    each entry's heap position as ``timegm(schedule.now()) + next_run``. A schedule
    whose ``now()`` returns a fake past date (e.g. 1970) ends up with a heap key of
    ~3600, placing it permanently at H[0] — the top of the min-heap — so beat keeps re-
    examining it every tick. With a real timestamp, the heap key is ``now_unix +
    86400``, safely at the bottom of the heap.
    """

    def is_due(self, last_run_at: datetime) -> schedstate:
        return schedstate(False, 24 * 3600)

    def remaining_estimate(self, last_run_at: datetime) -> timedelta:
        return timedelta(hours=24)

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


SCHEDULE_NEVER = _NeverSchedule()


def get_beat_schedule() -> dict:
    """Return the Celery Beat schedule configuration.

    This function is separate from init_celery_app() so it can be called at module level
    by other components (e.g., beat router) without requiring a fully initialized Celery
    app.
    """
    return {
        # Magic trick: use prime numbers for all */X tasks -> then we will have less conflicts
        "compute-complete-estimate": {
            "task": (
                "worker.periodic.compute_complete_estimate_task.compute_complete_estimate_task"
            ),
            "schedule": crontab(minute="*/1"),
        },
        "throttle-and-flush-lazybytes": {
            "task": (
                "worker.periodic.throttle_and_flush_lazybytes_task.throttle_and_flush_lazybytes_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="*/2"),
        },
        "shrink-cache": {
            "task": "worker.periodic.shrink_periodically_task.shrink_periodically_task",
            "schedule": crontab(minute="*/3"),
        },
        "flush-file-storage-service": {
            "task": (
                "worker.periodic.flush_file_storage_service_task.flush_file_storage_service_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="*/37"),
        },
        "reindex-lost-files-on-idle": {
            "task": (
                "worker.periodic.reindex_lost_files_on_idle_task.reindex_lost_files_on_idle_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="11", hour="22-05"),
        },
        "hide-old-uploaded-files": {
            "task": "worker.periodic.hide_periodically_task.hide_periodically_task",
            "schedule": crontab(minute="0", hour="0"),
        },
        "flush-root-task-info-on-idle": {
            "task": (
                "worker.periodic.flush_root_task_info_on_idle_task.flush_root_task_info_on_idle_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="0", hour="3"),
        },
        "unsubscribe-old-imap-folders": {
            "task": (
                "worker.periodic.unsubscribe_old_imap_folders_periodically_task.unsubscribe_old_imap_folders_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": crontab(minute="30", hour="0"),
        },
        # Uses SCHEDULE_NEVER so it never fires automatically, but can still be
        # triggered manually via the API when a full IMAP flag re-sync is needed.
        "sync-imap-flags": {
            "task": (
                "worker.periodic.sync_imap_flags_periodically_task.sync_imap_flags_periodically_task"  # noqa: E501 pylint: disable=line-too-long
            ),
            "schedule": SCHEDULE_NEVER,
        },
        # SeaweedFS Maintenance Tasks - frequent "on-idle" variants (check_idle=True)
        "seaweedfs-fix-replication-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="0-23/6"),
            "args": ("volume.fix.replication", ["-apply"]),
        },
        "seaweedfs-balance-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="1-23/6"),
            "args": ("volume.balance", ["-apply"]),
        },
        "seaweedfs-scrub-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="2-23/6"),
            "args": ("volume.scrub",),
        },
        "seaweedfs-s3-clean-uploads-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="3-23/6"),
            "args": ("s3.clean.uploads",),
        },
        "seaweedfs-vacuum-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="4-23/6"),
            "args": ("volume.vacuum", ["-garbageThreshold=0.01"]),
        },
        "seaweedfs-fsck-on-idle": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="43", hour="5-23/6"),
            "args": (
                "volume.fsck",
                [
                    "-findMissingChunksInFiler=true",
                    "-reallyDeleteFromVolume=true",
                    "-reallyDeleteFilerEntries=true",
                ],
            ),
        },
        # SeaweedFS Maintenance Tasks - weekly forced runs at night (check_idle=False)
        "seaweedfs-fix-replication": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="0", day_of_week="6"),
            "args": ("volume.fix.replication", ["-apply"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-balance": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="2", day_of_week="6"),
            "args": ("volume.balance", ["-apply"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-scrub": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="0", day_of_week="0"),
            "args": ("volume.scrub",),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-s3-clean-uploads": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="2", day_of_week="0"),
            "args": ("s3.clean.uploads",),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-vacuum": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="4", day_of_week="0,6"),
            "args": ("volume.vacuum", ["-garbageThreshold=0.01"]),
            "kwargs": {"check_idle": False},
        },
        "seaweedfs-fsck": {
            "task": (
                "worker.periodic.seaweedfs_maintenance_task.seaweedfs_maintenance_task"
            ),
            "schedule": crontab(minute="0", hour="6", day_of_week="0,6"),
            "args": (
                "volume.fsck",
                [
                    "-findMissingChunksInFiler=true",
                    "-reallyDeleteFromVolume=true",
                    "-reallyDeleteFilerEntries=true",
                ],
            ),
            "kwargs": {"check_idle": False},
        },
    }
