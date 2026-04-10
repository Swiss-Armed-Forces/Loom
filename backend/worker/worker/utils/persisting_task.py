from typing import Any, Callable, Concatenate, ParamSpec, Type

from celery import Celery
from celery.result import AsyncResult
from common.celery_app import BaseTask
from common.models.base_repository import BaseRepository
from common.settings import settings
from common.task_object.task_object import (
    RepositoryTaskObjectT,
    SecondaryRepositoryTaskObjectT,
)
from common.utils.sharding import compute_shard, get_persister_shard_queue_name

from worker.utils.persister_base import PersisterBase
from worker.utils.processing_task import ProcessingTask

P = ParamSpec("P")


def _default_persisting_cache(*_, **__):
    def decorator(func: Callable):
        return func

    return decorator


def persisting_task(
    celery_app: "Celery[BaseTask]",
    persister_type: Type[PersisterBase[RepositoryTaskObjectT]],
    get_task_object_repository: (
        Callable[[], BaseRepository[SecondaryRepositoryTaskObjectT]] | None
    ) = None,
    persisting_cache_decorator: Callable[
        [Callable], Callable
    ] = _default_persisting_cache,
):
    """Decorator to register a persisting task out of a callable.

    The callable must accept an IndexingPersister as first argument and the rest of the
    arguments are passed through to the task.

    :param get_task_object_repository: By default, the status of this task will be reported
        to the same repository as the persister_type is persisting. You can use this
        parameter if the persister_type is not persisting to the same repository as the
        task is reporting its state to.
    :param persisting_cache_decorator: Decorator is used before running the task allowing
        caching. The decorator needs to return a cache decorator and accept the persisting
        function which can be used to create the actually cache name.
        This can be used with `persisting_cache`.
    """

    def inner_decorator(persist_fcn: Callable[Concatenate[PersisterBase, P], None]):
        class PersistingTask(
            ProcessingTask[RepositoryTaskObjectT, SecondaryRepositoryTaskObjectT]
        ):
            """Base class for persisting tasks."""

            name = celery_app.gen_task_name(
                persist_fcn.__name__, persist_fcn.__module__
            )

            # pylint does not consider metaclass:
            # https://stackoverflow.com/questions/22186843/pylint-w0223-method-is-abstract-in-class-but-is-not-overridden
            # pylint: disable=abstract-method

            @property
            def _repository(
                self,
            ) -> (
                BaseRepository[RepositoryTaskObjectT]
                | BaseRepository[SecondaryRepositoryTaskObjectT]
            ):
                if get_task_object_repository is None:
                    return persister_type.get_repository()
                return get_task_object_repository()

            def apply_async(  # type: ignore[override]  # pylint: disable=arguments-differ
                self, args=None, kwargs=None, **options
            ) -> AsyncResult:
                """Route to persister shard queue based on entity ID."""
                # Last argument is always the entity object
                if args is None:
                    raise RuntimeError(
                        "Cannot call apply_async without args. "
                        "This should not happen."
                    )
                obj: RepositoryTaskObjectT = args[-1]
                shard = compute_shard(obj.id_, settings.num_persister_shards)
                options["queue"] = get_persister_shard_queue_name(shard)
                return super().apply_async(args, kwargs, **options)

            @persisting_cache_decorator(persist_fcn)
            def run(self, *args, **kwargs) -> Any:
                passed_args = args[:-1]
                obj: RepositoryTaskObjectT = args[-1]
                persister = persister_type(obj.id_)
                persist_fcn(persister, *passed_args, **kwargs)

                if len(passed_args) <= 0:
                    return None
                return passed_args[0]

        task_instance = PersistingTask()
        celery_app.register_task(
            task_instance,
        )
        return task_instance

    return inner_decorator
