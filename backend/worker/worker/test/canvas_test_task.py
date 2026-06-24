import logging
from time import sleep
from typing import Callable, List, Tuple

from celery import chain, chord, group
from celery.canvas import Signature
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


@app.task()
def short_running_full_return(*args):
    return args


@app.task()
def short_running(*args):
    return args[-1]


@app.task()
def long_running(*args):
    sleep(2)
    return args[-1]


# === Base tasks for ordering tests ============================================


@app.task(base=TestTask)
def return_indexed_value(index: int) -> int:
    return index


@app.task(base=TestTask)
def return_indexed_value_delayed(index: int) -> int:
    sleep(2 / (index + 1))
    return index


@app.task(base=TestTask)
def collect_results(results: list[int]) -> list[int]:
    return results


@app.task(bind=True, base=TestTask)
def self_replace_with_group_of_chords(self) -> list[list[int]]:
    return self.replace(
        group(
            chord(
                [return_indexed_value.s(i) for i in range(10)],
                collect_results.s(),
            )
            for _ in range(2)
        )
    )


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

    def _impl(*args, **kwargs):
        return (
            sig_fn(*args, **kwargs)
            .delay()
            .get(disable_sync_subtasks=False, timeout=GET_TIMEOUT)
        )

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

    def _impl(_: TestTask, *args, **kwargs):
        return (
            self_replace.s(sig_fn(*args, **kwargs))
            .delay()
            .get(disable_sync_subtasks=False, timeout=GET_TIMEOUT)
        )

    _impl.__name__ = task_name
    _impl.__qualname__ = task_name
    _impl.__module__ = __name__

    task_obj = app.task(name=fully_qualified, bind=True, base=TestTask)(_impl)
    globals()[task_name] = task_obj
    return fully_qualified


def _autodefine_tests(prefix: str | None = None) -> list[str]:
    created_task_names: list[str] = []
    for case, fn in _CASES:
        if prefix and not case.startswith(prefix):
            continue
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
def signature_raise_complex_canvas1(ex: CanvasTestException) -> Signature:
    return group(signature_raise_exception_chain1(ex), noop.s())


@canvas_case()
def signature_raise_self_replace1(ex: CanvasTestException):
    return self_replace.s(raise_exception.s(ex))


# this works in the standalone but not here?
@canvas_case()
def signature_assert_group1():
    return chain(
        short_running.s(-1),
        group(
            long_running.s(2),
            chain(
                group(
                    short_running.s(-3),
                    short_running.s(-4),
                ),
                short_running.s(-5),
                group(
                    short_running.s(6),
                    long_running.s(7),
                ),
            ),
            short_running.s(8),
        ),
    )


@canvas_case()
def signature_assert_group2():
    return chain(
        group(
            long_running.s(1),
            chain(
                group(
                    short_running.s(-2),
                    short_running.s(-3),
                ),
                short_running.s(-4),
                group(
                    short_running.s(5),
                    long_running.s(6),
                    short_running.s(7),
                ),
            ),
            short_running.s(8),
        ),
        short_running_full_return.s(9),
    )


# times out in other test, give dubious error in this one?
@canvas_case()
def signature_assert_group3():
    return chain(
        group(
            long_running.s(1),
            chain(
                group(
                    short_running.s(-2),
                    short_running.s(-3),
                ),
                short_running.s(-4),
                group(
                    short_running.s(5),
                    long_running.s(6),
                    short_running.s(7),
                ),
            ),
            short_running.s(8),
        ),
    )


# fix via celery patch, long_running.s(1) is not awaited
@canvas_case()
def signature_assert_group4():
    return chain(
        group(
            long_running.s(1),
            chain(
                short_running.s(-2),
                group(
                    short_running.s(3),
                    short_running.s(4),
                ),
            ),
        ),
        # True means the task returns all args instead of just it's assigned value
        short_running_full_return.s(5),
    )


# === Canvases for ordering tests =====================================


@canvas_case()
def signature_chord_ordering1() -> Signature:
    return chord(
        [return_indexed_value.s(i) for i in range(10)],
        collect_results.s(),
    )


@canvas_case()
def signature_chord_ordering2() -> Signature:
    return chord(
        [return_indexed_value.s(i) for i in range(10)],
        chain(
            collect_results.s(),
        ),
    )


@canvas_case()
def signature_chord_ordering3() -> Signature:
    return group(
        chord(
            [return_indexed_value.s(i) for i in range(10)],
            collect_results.s(),
        )
    )


@canvas_case()
def signature_chord_ordering4() -> Signature:
    return chord(
        [return_indexed_value_delayed.s(i) for i in range(10)],
        collect_results.s(),
    )


@canvas_case()
def signature_chord_ordering5() -> Signature:
    """BUG: self.replace inside group() breaks chord result ordering.

    Regression test: for https://github.com/celery/celery/issues/10191
    """
    return group(
        self_replace_with_group_of_chords.s(),
        noop.s(),
    )


# === Generate tests for every signature_* above ==============================

_autodefine_tests()
