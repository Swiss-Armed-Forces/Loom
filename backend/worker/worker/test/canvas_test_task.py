import logging
from typing import Callable, List, Tuple

from celery import chain, chord
from celery.canvas import Signature, group
from common.dependencies import get_celery_app

from worker.test.infra.test_task import TestTask

logger = logging.getLogger(__name__)
app = get_celery_app()

GET_TIMEOUT = 30


class CanvasTestException(Exception):
    pass


# === Base tasks ===============================================================


@app.task(base=TestTask)
def noop(*_, **__):
    pass


@app.task(base=TestTask)
def raise_exception(ex: CanvasTestException, *_, **__):
    raise ex


@app.task(base=TestTask)
def raise_exception_with_input(_, ex: CanvasTestException, *__, **___):
    raise ex


@app.task(bind=True, base=TestTask)
def self_replace(self: TestTask, signature: Signature, *__, **___):
    return self.replace(signature)


# === Registry + decorator to auto-create tests ===============================

_CASES: List[Tuple[str, Callable[..., Signature]]] = (
    []
)  # (case_name, fn(ex)->Signature)
_CREATED: set[str] = set()  # guard against redefining


def canvas_case(name: str | None = None):
    """Register a signature factory; auto-define two tests for it."""

    def _wrap(fn: Callable[..., Signature]):
        case_name = name or fn.__name__.removeprefix("signature_")
        _CASES.append((case_name, fn))
        return fn

    return _wrap


def _define_subtask_test(case: str, sig_fn: Callable[..., Signature]) -> str:
    task_name = f"test_subtask_{case}"
    fully_qualified = f"{__name__}.{task_name}"

    # Idempotency: if we already exposed the task on the module, just return its name
    if task_name in globals():
        return fully_qualified

    def _impl(ex: CanvasTestException, *_, **__):
        sig_fn(ex).delay().get(disable_sync_subtasks=False, timeout=GET_TIMEOUT)

    _impl.__name__ = task_name
    _impl.__qualname__ = task_name
    _impl.__module__ = __name__

    task_obj = app.task(name=fully_qualified, base=TestTask)(_impl)
    globals()[task_name] = task_obj
    return fully_qualified


def _define_self_replace_test(case: str, sig_fn: Callable[..., Signature]) -> str:
    task_name = f"test_self_replace_{case}"
    fully_qualified = f"{__name__}.{task_name}"

    # Idempotency
    if task_name in globals():
        return fully_qualified

    def _impl(_: TestTask, ex: CanvasTestException, *__, **___):
        self_replace.s(sig_fn(ex)).delay().get(
            disable_sync_subtasks=False, timeout=GET_TIMEOUT
        )

    _impl.__name__ = task_name
    _impl.__qualname__ = task_name
    _impl.__module__ = __name__

    task_obj = app.task(name=fully_qualified, bind=True, base=TestTask)(_impl)
    globals()[task_name] = task_obj
    return fully_qualified


def _autodefine_tests() -> list[str]:
    created_task_names: list[str] = []
    for case, fn in _CASES:
        for builder in (_define_subtask_test, _define_self_replace_test):
            fq_name = builder(
                case, fn
            )  # idempotent; returns e.g. "worker.test.canvas_test_task.test_foo_subtask"
            logical_name = fq_name.rsplit(".", 1)[1]  # e.g. "test_foo_subtask"
            if logical_name not in _CREATED:
                _CREATED.add(logical_name)
                created_task_names.append(fq_name)
            else:
                # Avoid duplicates in the return list
                if fq_name not in created_task_names:
                    created_task_names.append(fq_name)
    return created_task_names


# === Concrete canvases (use tasks/canvas directly) ===========================


@canvas_case()
def signature_raise_exception(ex: CanvasTestException) -> Signature:
    return raise_exception.s(ex)


@canvas_case()
def signature_raise_exception_group1(ex: CanvasTestException) -> Signature:
    return group(noop.s(), raise_exception.s(ex))


@canvas_case()
def signature_raise_exception_group2(ex: CanvasTestException) -> Signature:
    return group(raise_exception.s(ex), noop.s())


@canvas_case()
def signature_raise_exception_chain1(ex: CanvasTestException) -> Signature:
    return chain(noop.s(), raise_exception_with_input.s(ex))


@canvas_case()
def signature_raise_exception_chain2(ex: CanvasTestException) -> Signature:
    return chain(raise_exception.s(ex), noop.s())


@canvas_case()
def signature_raise_exception_chord1(ex: CanvasTestException) -> Signature:
    return chord([raise_exception.s(ex), noop.s()], noop.s(ex))


@canvas_case()
def signature_raise_exception_chord2(ex: CanvasTestException) -> Signature:
    return chord([noop.s(), raise_exception.s(ex)], noop.s(ex))


@canvas_case()
def signature_raise_exception_chord3(ex: CanvasTestException) -> Signature:
    return chord([noop.s(), noop.s()], raise_exception_with_input.s(ex))


@canvas_case()
def signature_complex_canvas1(ex: CanvasTestException) -> Signature:
    return group(signature_raise_exception_chain1(ex), noop.s())


@canvas_case()
def signature_self_replace1(ex: CanvasTestException):
    return self_replace.s(raise_exception.s(ex))


# === Generate tests for every signature_* above ==============================

_autodefine_tests()
