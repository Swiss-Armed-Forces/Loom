import logging

from celery import chord
from common.dependencies import (
    get_celery_app,
    get_celery_inspect_service,
)
from common.services.celery_inspect_service import (
    CeleryInspectService,
    TaskGroupName,
)
from common.utils.task_lock import task_lock

from worker.periodic.infra.periodic_task import PeriodicTask
from worker.periodic.tasks import flush_root_task_information

logger = logging.getLogger(__name__)

app = get_celery_app()

_FLUSH_ROOT_TASK_INFO_LOCK_TTL_SECONDS = 60 * 15  # 15 minutes
_WAIT_FOR_IDLE_TIMEOUT_SECONDS = 60 * 10  # 10 minutes (well under lock TTL)
_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS = 10.0

_PAUSED_GROUPS = (TaskGroupName.DISPATCH,)


def _wait_for_pipeline_idle(
    inspect: CeleryInspectService, exclude_tasks: list[str]
) -> bool:
    """Wait until the full pipeline is idle, excluding the given tasks."""
    all_tasks = inspect.get_task_names_in_group(TaskGroupName.ALL)
    return inspect.wait_for_idle(
        timeout=_WAIT_FOR_IDLE_TIMEOUT_SECONDS,
        poll_interval=_WAIT_FOR_IDLE_POLL_INTERVAL_SECONDS,
        include_tasks=all_tasks,
        exclude_tasks=exclude_tasks,
    )


@app.task(base=PeriodicTask)
def flush_complete(*_, **__):
    """Chord callback: resume source task groups after flush."""
    inspect = get_celery_inspect_service()
    for group in _PAUSED_GROUPS:
        inspect.set_taskgroup_paused(group, False)
    logger.info("Root task information flush complete")


@app.task(bind=True, base=PeriodicTask)
@task_lock(ttl_seconds=_FLUSH_ROOT_TASK_INFO_LOCK_TTL_SECONDS, blocking=False)
def flush_root_task_info_on_idle_task(self: PeriodicTask):
    """Flush stale root task information when the whole pipeline is quiescent.

    Root task information tracks which files are actively being processed. Flushing it
    while any processing or lazybytes-holding task is still running would silently drop
    in-progress tracking data.

    Two-phase approach:
    - Phase 1: wait for the full pipeline to be idle without pausing anything, to
      avoid disrupting the system unless it is actually quiet.
    - Phase 2: pause DISPATCH, wait for full idle again to close the race window,
      then replace with a chord that flushes root task info and resumes the paused
      groups via flush_complete.
    """
    inspect = get_celery_inspect_service()

    if not _wait_for_pipeline_idle(inspect, exclude_tasks=[self.name]):
        logger.info("Celery not idle: timed out waiting for full idle, skipping flush")
        return None

    for group in _PAUSED_GROUPS:
        inspect.set_taskgroup_paused(group, True)

    if not _wait_for_pipeline_idle(inspect, exclude_tasks=[self.name]):
        logger.info("Celery not idle after pausing sources: timed out, skipping flush")
        for group in _PAUSED_GROUPS:
            inspect.set_taskgroup_paused(group, False)
        return None

    logger.info("System idle: flushing root task information")
    return self.replace(
        chord(
            [flush_root_task_information.signature()],
            flush_complete.s(),
        )
    )
