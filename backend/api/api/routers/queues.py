import logging

from common.dependencies import get_queues_service
from common.services.queues_service import QueuesService
from fastapi import APIRouter, Depends

from api.models.queues_model import QueuesStats

router = APIRouter()

default_queues_service = Depends(get_queues_service)

logger = logging.getLogger(__name__)


@router.get("")
def get_all_queues(
    queues_service: QueuesService = default_queues_service,
) -> dict[str, int]:
    return queues_service.get_all_queue_message_counts()


@router.get("/stats")
def get_overall_queue_stats(
    queues_service: QueuesService = default_queues_service,
) -> QueuesStats:
    return QueuesStats(
        messages_in_queues=queues_service.get_message_count(),
        paused_queues=queues_service.get_paused_queues(),
    )


@router.get("/paused")
def list_paused_queues(
    queues_service: QueuesService = default_queues_service,
) -> list[str]:
    return queues_service.get_paused_queues()


@router.get("/{queue_name}/paused")
def is_queue_paused(
    queue_name: str,
    queues_service: QueuesService = default_queues_service,
) -> bool:
    return queues_service.is_queue_paused(queue_name)


@router.get("/{queue_name}/message_count")
def get_message_count(
    queue_name: str | None = None,
    queues_service: QueuesService = default_queues_service,
) -> int:
    return queues_service.get_message_count(queue_name=queue_name)
