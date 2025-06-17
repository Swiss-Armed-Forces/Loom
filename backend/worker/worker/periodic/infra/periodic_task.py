from abc import ABC

from celery import Task


class PeriodicTask(ABC, Task):
    pass
