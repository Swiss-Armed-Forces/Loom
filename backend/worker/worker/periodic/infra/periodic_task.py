from abc import ABC

from celery import Task  # type: ignore[import-untyped]


class PeriodicTask(ABC, Task):
    pass
