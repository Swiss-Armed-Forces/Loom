import asyncio
import gc
import logging
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from threading import Thread
from time import monotonic
from typing import (
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
)
from uuid import UUID

from common.models.base_repository import (
    BaseRepository,
    RepositoryObject,
    RepositoryObjectT,
)
from common.utils.cgroup_memory_limit import is_memory_pressure

from worker.settings import settings

logger = logging.getLogger(__name__)

PERSISTER_EVICTION_GC_RUN = 10

# ParamSpec for mutation function parameters (after obj)
P = ParamSpec("P")

# TypeVar for the repository object type in mutation decorator
MutationObjT = TypeVar("MutationObjT", bound=RepositoryObject)


def mutation(
    fn: Callable[Concatenate[MutationObjT, P], None],
) -> Callable[Concatenate["PersisterBase[MutationObjT]", P], None]:
    """Decorator that converts a mutation function into a persister method.

    Transforms a function of the form:
        def set_state(obj: File, state: str):
            obj.state = state

    Into a method that automatically submits the mutation to the actor queue:
        persister.set_state("done")

    Type transformation:
        Input:  (obj: File, state: str) -> None
        Output: (self: PersisterBase[File], state: str) -> None

    The decorated function:
    - Takes the object as its first parameter (after self is removed)
    - All other parameters are passed from the method call
    - Gets wrapped into a closure that captures arguments at call time
    - Is submitted to the worker queue for the object

    Safety guarantees:
    - Arguments are captured at call time (no late binding issues)
    - Mutation is applied only by the owning worker
    - Replay-safe: closures can be re-applied on conflict recovery
    """

    @wraps(fn)
    def wrapper(
        self: "PersisterBase[MutationObjT]", *args: P.args, **kwargs: P.kwargs
    ) -> None:
        def apply(obj: MutationObjT) -> None:
            fn(obj, *args, **kwargs)

        self.submit(_ObjectMutation(object_id=self.object_id, mutation_fn=apply))

    return wrapper


class PersistingException(Exception):
    """Exception raised when persisting a file fails."""


class _ObjectState(Generic[RepositoryObjectT]):
    """State for a single tracked object (worker-internal)."""

    def __init__(
        self,
        obj: RepositoryObjectT,
        now: float,
    ) -> None:
        self._obj = obj
        self._last_update_ts = now
        self._first_update_ts: float | None = None
        self._replay_log: list[Callable[[RepositoryObjectT], None]] = []
        self._recovery_attempts = 0
        self._has_error = False

    @property
    def obj(self) -> RepositoryObjectT:
        """The cached repository object (read-only)."""
        return self._obj

    @property
    def last_update_ts(self) -> float:
        """Timestamp of last mutation or object replacement (read-only)."""
        return self._last_update_ts

    @property
    def first_update_ts(self) -> float | None:
        """Timestamp of first unsaved mutation, None if no pending mutations (read-
        only)."""
        return self._first_update_ts

    @property
    def recovery_attempts(self) -> int:
        """Count of recovery attempts (read-only)."""
        return self._recovery_attempts

    def increment_recovery_attempts(self) -> None:
        """Increment recovery attempt counter.

        Call BEFORE attempting recovery.
        """
        self._recovery_attempts += 1

    @property
    def has_pending_mutations(self) -> bool:
        """True if there are mutations waiting to be saved."""
        return bool(self._replay_log)

    @property
    def has_error(self) -> bool:
        """True if object had an error during last save attempt."""
        return self._has_error

    def mark_error(self) -> None:
        """Mark this object as having a save error."""
        self._has_error = True

    def apply_mutation(
        self,
        mutation_fn: Callable[[RepositoryObjectT], None],
        now: float,
    ) -> None:
        """Apply a mutation to the object and record it for replay."""
        mutation_fn(self._obj)
        self._replay_log.append(mutation_fn)
        self._last_update_ts = now
        if self._first_update_ts is None:
            self._first_update_ts = now

    def replace_obj(self, new_obj: RepositoryObjectT, now: float) -> None:
        """Replace the object and replay pending mutations.

        Updates timestamps to trigger a new save attempt (used for error recovery).
        Clears error flag. Note: caller must increment recovery_attempts before calling.
        """
        self._obj = new_obj
        for fn in self._replay_log:
            fn(self._obj)
        self._first_update_ts = now
        self._last_update_ts = now
        self._has_error = False

    def mark_saved(self) -> None:
        """Mark mutations as successfully saved.

        Clears replay log, resets recovery_attempts, and clears error flag.
        """
        self._replay_log.clear()
        self._first_update_ts = None
        self._recovery_attempts = 0
        self._has_error = False


@dataclass
class _ObjectMutation(Generic[RepositoryObjectT]):
    object_id: UUID
    mutation_fn: Callable[[RepositoryObjectT], None]


class GlobalPersisterWorker(Generic[RepositoryObjectT]):
    """Manages a single global worker that batches and persists mutations.

    Thread-safe submission via stdlib queue.Queue. Worker loop runs in a dedicated event
    loop thread.
    """

    # No lock needed: Celery prefork pool uses separate processes, each single-threaded
    _instance_counter: ClassVar[int] = 0

    def __init__(self, repository: BaseRepository[RepositoryObjectT]):
        self._repository = repository

        # Create unique instance ID
        GlobalPersisterWorker._instance_counter += 1
        instance_id = GlobalPersisterWorker._instance_counter

        # Create instance-specific logger
        repo_name = type(repository).__name__
        self._logger = logging.getLogger(f"{__name__}.{repo_name}.{instance_id}")

        self._mutation_queue: queue.Queue[_ObjectMutation] = queue.Queue()
        self._loop = asyncio.new_event_loop()

        def run():
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._loop_thread = Thread(target=run, daemon=True)
        self._loop_thread.start()
        self._worker_result = asyncio.run_coroutine_threadsafe(
            self._worker_loop(), self._loop
        )

    def submit(self, object_mutation: _ObjectMutation[RepositoryObjectT]) -> None:
        """Submit a mutation.

        Thread-safe.
        """
        self._mutation_queue.put(object_mutation)

    async def _worker_loop(self) -> None:
        """Single global worker.

        Never terminates.
        """
        objects: dict[UUID, _ObjectState[RepositoryObjectT]] = {}
        object_mutations: list[_ObjectMutation[RepositoryObjectT]] = []
        now = monotonic()

        while True:
            try:
                # Debounce
                before_sleep = monotonic()
                sleep_time = max(
                    0, settings.persister_debounce_window - (before_sleep - now)
                )
                await asyncio.sleep(sleep_time)

                # Update now
                now = monotonic()

                # Drain mutations from queue
                while True:
                    try:
                        object_mutations.append(self._mutation_queue.get_nowait())
                    except queue.Empty:
                        break

                # Apply mutations (may defer some if under memory pressure)
                # Pop mutations as we process them so they're removed from the list.
                # If an exception occurs, already-processed mutations won't be retried.
                deferred_mutations = 0
                len_object_mutations = len(object_mutations)
                while object_mutations:
                    object_mutation = object_mutations.pop(0)
                    applied_mutation = await self._apply_mutation(
                        now, objects, object_mutation
                    )
                    if not applied_mutation:
                        self._mutation_queue.put(object_mutation)
                        deferred_mutations += 1
                self._logger.info(
                    "Applied %d mutations, deferred: %d, cached objects: %d",
                    len_object_mutations - deferred_mutations,
                    deferred_mutations,
                    len(objects),
                )

                # Flush
                await self._flush_all_ready(now, objects)

                # Handle errors
                await self._handle_errors(now, objects)

                # Forget
                await self._forget_stale(now, objects)

            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.exception("Error in global worker loop, continuing...")

    async def _apply_mutation(
        self,
        now: float,
        objects: dict[UUID, _ObjectState[RepositoryObjectT]],
        object_mutation: _ObjectMutation,
    ) -> bool:
        """Apply mutation to object, lazy-loading if needed.

        If memory pressure and object not cached, adds mutation to deferred_mutations
        instead of loading.

        Always loads if cache is empty to prevent deadlocks.
        """
        state = objects.get(object_mutation.object_id)

        if state is None:
            # Check memory pressure, but always allow load if cache is empty
            if len(objects) > 0 and is_memory_pressure():
                return False

            # Load object
            obj = await asyncio.to_thread(
                self._repository.get_by_id, object_mutation.object_id
            )
            if obj is None:
                self._logger.warning("Object %s not found", object_mutation.object_id)
                return True

            state = _ObjectState(obj=obj, now=now)
            objects[object_mutation.object_id] = state

        # Apply mutation to cached object
        state.apply_mutation(object_mutation.mutation_fn, now)
        return True

    async def _flush_all_ready(
        self, now: float, objects: dict[UUID, _ObjectState[RepositoryObjectT]]
    ) -> None:
        """Flush objects ready for persistence using bulk_save."""
        objects_to_save: list[RepositoryObjectT] = []

        for state in objects.values():
            if state.first_update_ts is None:
                # No unflushed updates
                continue
            debounce_deadline = (
                state.last_update_ts + settings.persister_debounce_window
            )
            max_deadline = state.first_update_ts + settings.persister_max_delay
            if now >= debounce_deadline or now >= max_deadline:
                objects_to_save.append(state.obj)

        if not objects_to_save:
            return

        results = await asyncio.to_thread(
            lambda: list(self._repository.bulk_save(objects_to_save))
        )

        for op_result in results:
            obj_id = op_result.object_id
            state = objects[obj_id]

            if op_result.success:
                self._logger.debug("Saved object %s", obj_id)
                state.mark_saved()
            else:
                self._logger.warning("Failed to save %s: %s", obj_id, op_result.error)
                state.mark_error()

    async def _handle_errors(
        self,
        now: float,
        objects: dict[UUID, _ObjectState[RepositoryObjectT]],
    ) -> None:
        """Handle all objects marked with errors by reloading and retrying.

        Each object is handled independently - exceptions don't affect other objects.
        Counter is incremented BEFORE recovery attempt to prevent infinite loops.
        """
        # Collect IDs first to avoid modifying dict during iteration
        error_ids = [obj_id for obj_id, state in objects.items() if state.has_error]

        for obj_id in error_ids:
            state = objects[obj_id]

            # Increment BEFORE recovery attempt (prevents infinite loop on exception)
            state.increment_recovery_attempts()

            # Check max retries (after increment)
            if state.recovery_attempts > settings.persister_save_max_retries:
                self._logger.error("Max recovery retries exceeded for %s", obj_id)
                objects.pop(obj_id)
                continue

            # Reload from repository
            reloaded_obj = await asyncio.to_thread(self._repository.get_by_id, obj_id)

            if reloaded_obj is None:
                objects.pop(obj_id)
                self._logger.warning(
                    "Object %s disappeared during error recovery", obj_id
                )
                continue

            # Replace object and replay mutations (clears error flag)
            state.replace_obj(reloaded_obj, now)

            self._logger.info(
                "Recovery for %s (attempt %d/%d)",
                obj_id,
                state.recovery_attempts,
                settings.persister_save_max_retries,
            )

    async def _forget_stale(
        self, now: float, objects: dict[UUID, _ObjectState[RepositoryObjectT]]
    ) -> None:
        """Remove stale objects to free memory."""
        cutoff_time = now - (
            settings.persister_max_delay
            * settings.persister_max_delay_forget_multiplier
        )

        stale_ids = []
        for obj_id, state in objects.items():
            if state.last_update_ts < cutoff_time and not state.has_pending_mutations:
                stale_ids.append(obj_id)

        for obj_id in stale_ids:
            objects.pop(obj_id)
            self._logger.debug("Forgot stale object %s", obj_id)

        # LRU eviction if under memory pressure (after flush cleared replay logs)
        if is_memory_pressure():
            # Sort by last_update_ts (oldest first), evict those without pending mutations
            evictable = [
                (obj_id, state)
                for obj_id, state in objects.items()
                if not state.has_pending_mutations
            ]
            evictable.sort(key=lambda x: x[1].last_update_ts)

            evicted_count = 0
            for obj_id, _ in evictable:
                # Run GC periodically to actually free memory and check pressure
                if evicted_count % PERSISTER_EVICTION_GC_RUN == 0:
                    gc.collect()
                if not is_memory_pressure():
                    break
                objects.pop(obj_id)
                evicted_count += 1
                self._logger.debug("Evicted object %s (LRU)", obj_id)


class PersisterBase(ABC, Generic[RepositoryObjectT]):
    """Base class for persisters.

    Delegates to GlobalPersisterWorker.
    """

    # Each subclass gets its own worker instance
    # No lock needed: Celery prefork pool uses separate processes, each single-threaded
    _worker: ClassVar[GlobalPersisterWorker[Any] | None] = None

    @classmethod
    @abstractmethod
    def get_repository(cls) -> BaseRepository[RepositoryObjectT]:
        pass

    @classmethod
    def _get_worker(cls) -> GlobalPersisterWorker[RepositoryObjectT]:
        """Get or create the worker for this persister class."""
        if cls._worker is None:
            cls._worker = GlobalPersisterWorker(cls.get_repository())
        return cls._worker

    @classmethod
    def submit(cls, object_mutation: _ObjectMutation[RepositoryObjectT]) -> None:
        """Submit a mutation to the global worker."""
        cls._get_worker().submit(object_mutation)

    def __init__(self, object_id: UUID):
        self._object_id = object_id

    @property
    def object_id(self) -> UUID:
        """The ID of the object being persisted."""
        return self._object_id
