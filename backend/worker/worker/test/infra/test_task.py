from abc import ABC

from common.celery_app import BaseTask


class TestTask(BaseTask, ABC):
    pass
