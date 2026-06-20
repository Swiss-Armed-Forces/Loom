from common.celery_app import TaskGroupName
from common.dependencies import get_celery_inspect_service
from common.services.celery_inspect_service import CeleryInspectService
from fastapi import APIRouter, Depends

router = APIRouter()

default_celery_inspect_service = Depends(get_celery_inspect_service)


@router.get("/task-groups")
def get_task_groups(
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> dict[str, list[str]]:
    return {
        group.value: celery_inspect_service.get_task_names_in_group(group)
        for group in TaskGroupName
    }


@router.get("/throttled")
def get_throttled(
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> bool:
    return celery_inspect_service.is_throttled()


@router.put("/throttled", status_code=204)
def set_throttled(
    throttled: bool,
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> None:
    celery_inspect_service.set_throttled(throttled)


@router.get("/task-groups/{group_name}/paused")
def get_taskgroup_paused(
    group_name: TaskGroupName,
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> bool:
    return celery_inspect_service.is_taskgroup_paused(group_name)


@router.put("/task-groups/{group_name}/paused", status_code=204)
def set_taskgroup_paused(
    group_name: TaskGroupName,
    paused: bool,
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> None:
    celery_inspect_service.set_taskgroup_paused(group_name, paused)


@router.get("/tasks/{task_name}/paused")
def get_task_paused(
    task_name: str,
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> bool:
    return celery_inspect_service.is_task_paused(task_name)


@router.put("/tasks/{task_name}/paused", status_code=204)
def set_task_paused(
    task_name: str,
    paused: bool,
    celery_inspect_service: CeleryInspectService = default_celery_inspect_service,
) -> None:
    celery_inspect_service.set_task_paused(task_name, paused)
