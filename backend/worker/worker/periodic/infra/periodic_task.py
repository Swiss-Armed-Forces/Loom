from abc import ABC

from common.celery_app import BaseTask


class PeriodicTask(BaseTask, ABC):
    pass
