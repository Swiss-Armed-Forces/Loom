from abc import ABC

from common.celery_app import BaseTask, TaskGroupName


class PeriodicTask(BaseTask, ABC):
    _task_group_name = TaskGroupName.PERIODIC
