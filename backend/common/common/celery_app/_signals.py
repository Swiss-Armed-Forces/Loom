import logging
from typing import Any, Protocol

from celery import Celery, Task, signals

from common.celery_app._queues import get_terminal_queues
from common.utils.oom_score_adjust import adjust_oom_score

logger = logging.getLogger(__name__)


class _WorkerReadySender(Protocol):  # pylint: disable=too-few-public-methods
    # The celery-stubs package does not type the `app` attribute on
    # celery.worker.components.Consumer (the actual runtime sender of
    # worker_ready), nor does the kombu-stubs package type
    # ProducerPool.acquire. This Protocol captures the subset we actually
    # use so mypy/Pyright can follow the chain.
    # Remove once upstream stubs are complete.
    app: Celery


# Set oom scores for the pool worker
# such that the pool worker is more likely to be
# killed under memory pressure..
@signals.worker_process_init.connect
def set_oom_score_for_pool_worker(*_, **__):
    adjust_oom_score(1000)


@signals.worker_ready.connect
def declare_terminal_queues(sender: _WorkerReadySender, **__: Any) -> None:
    """Declare terminal queues that no worker consumes.

    Celery only declares queues a worker actively subscribes to. The abyss and
    unroutable queues are terminal destinations with no consumers, so they must be
    declared explicitly to ensure dead-letter and alternate-exchange routing works
    correctly on fresh deployments.
    """
    with sender.app.pool.acquire(block=True) as conn:  # type: ignore[attr-defined]
        for queue in get_terminal_queues():
            queue(conn.default_channel).declare()  # type: ignore[operator]


@signals.task_prerun.connect
def log_task_start(
    _: Task | None = None,
    task_id: str | None = None,
    task: Task | None = None,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    **__: Any,
) -> None:
    logger.info(
        "Starting task %s[%s] with args=%s, kwargs=%s",
        task.name if task is not None else None,
        task_id,
        args,
        kwargs,
    )
