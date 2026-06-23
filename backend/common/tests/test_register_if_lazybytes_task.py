import dataclasses
from typing import Optional, cast
from unittest.mock import MagicMock

import pytest
from celery import Task
from pydantic import BaseModel

from common.celery_app import (
    TaskGroupName,
    _task_groups,
    register_if_lazybytes_task,
)
from common.services.lazybytes_service import FileStorageTag, LazyBytes, TempStorageTag

# ---------------------------------------------------------------------------
# Helpers – standalone functions used as mock task.run implementations.
# These must be module-level so get_type_hints can resolve their annotations.
# ---------------------------------------------------------------------------


def _run_no_lazybytes() -> None:
    raise NotImplementedError


def _run_producing_only() -> LazyBytes[TempStorageTag]:
    raise NotImplementedError


def _run_consuming_only(_data: LazyBytes[TempStorageTag]) -> None:
    raise NotImplementedError


def _run_producing_and_consuming(
    _data: LazyBytes[TempStorageTag],
) -> LazyBytes[TempStorageTag]:
    raise NotImplementedError


def _run_wrong_tag_param(_data: LazyBytes[FileStorageTag]) -> None:
    raise NotImplementedError


def _run_wrong_tag_return() -> LazyBytes[FileStorageTag]:
    raise NotImplementedError


def _run_optional_temp_return() -> Optional[LazyBytes[TempStorageTag]]:
    raise NotImplementedError


def _run_union_temp_return() -> LazyBytes[TempStorageTag] | None:
    raise NotImplementedError


def _run_nested_return() -> tuple[LazyBytes[TempStorageTag], str]:
    raise NotImplementedError


def _run_consuming_nested_param(
    _data: tuple[LazyBytes[TempStorageTag], str],
) -> None:
    raise NotImplementedError


def _run_list_return() -> list[LazyBytes[TempStorageTag]]:
    raise NotImplementedError


def _run_list_param(_data: list[LazyBytes[TempStorageTag]]) -> None:
    raise NotImplementedError


def _run_dict_return() -> dict[str, LazyBytes[TempStorageTag]]:
    raise NotImplementedError


def _run_dict_param(_data: dict[str, LazyBytes[TempStorageTag]]) -> None:
    raise NotImplementedError


def _run_deeply_nested_return() -> Optional[list[LazyBytes[TempStorageTag]]]:
    raise NotImplementedError


def _run_wrong_tag_in_list_return() -> list[LazyBytes[FileStorageTag]]:
    raise NotImplementedError


# Pydantic model helpers


class _PydanticWithLazyBytes(BaseModel):
    data: LazyBytes[TempStorageTag]


class _PydanticWithWrongTag(BaseModel):
    data: LazyBytes[FileStorageTag]


class _PydanticWithoutLazyBytes(BaseModel):
    name: str


def _run_pydantic_param(_m: _PydanticWithLazyBytes) -> None:
    raise NotImplementedError


def _run_pydantic_return() -> _PydanticWithLazyBytes:
    raise NotImplementedError


def _run_pydantic_wrong_tag_param(_m: _PydanticWithWrongTag) -> None:
    raise NotImplementedError


def _run_pydantic_no_lazybytes_param(_m: _PydanticWithoutLazyBytes) -> None:
    raise NotImplementedError


# Dataclass helpers


@dataclasses.dataclass
class _DataclassWithLazyBytes:
    data: LazyBytes[TempStorageTag]


@dataclasses.dataclass
class _DataclassWithWrongTag:
    data: LazyBytes[FileStorageTag]


@dataclasses.dataclass
class _DataclassWithoutLazyBytes:
    name: str


def _run_dataclass_param(_m: _DataclassWithLazyBytes) -> None:
    raise NotImplementedError


def _run_dataclass_return() -> _DataclassWithLazyBytes:
    raise NotImplementedError


def _run_dataclass_wrong_tag_param(_m: _DataclassWithWrongTag) -> None:
    raise NotImplementedError


def _run_dataclass_no_lazybytes_param(_m: _DataclassWithoutLazyBytes) -> None:
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_task_groups():
    _task_groups.clear()
    yield
    _task_groups.clear()


def _make_task(name: str, run_func) -> type[Task]:
    task = MagicMock(spec=Task)
    task.name = name
    task.run = run_func
    return cast(type[Task], task)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "run_func, in_producing, in_consuming, in_consuming_producing",
    [
        (_run_no_lazybytes, False, False, False),
        (_run_producing_only, True, False, False),
        (_run_consuming_only, False, True, False),
        (_run_producing_and_consuming, False, False, True),
        (_run_wrong_tag_param, False, False, False),
        (_run_wrong_tag_return, False, False, False),
        (_run_optional_temp_return, True, False, False),
        (_run_union_temp_return, True, False, False),
        (_run_nested_return, True, False, False),
        (_run_consuming_nested_param, False, True, False),
        # Complex return types containing LazyBytes[TempStorageTag]
        (_run_list_return, True, False, False),
        (_run_dict_return, True, False, False),
        (_run_deeply_nested_return, True, False, False),
        # Complex param types containing LazyBytes[TempStorageTag]
        (_run_list_param, False, True, False),
        (_run_dict_param, False, True, False),
        # Wrong tag inside a container – must not register
        (_run_wrong_tag_in_list_return, False, False, False),
        # Pydantic BaseModel with LazyBytes field
        (_run_pydantic_param, False, True, False),
        (_run_pydantic_return, True, False, False),
        (_run_pydantic_wrong_tag_param, False, False, False),
        (_run_pydantic_no_lazybytes_param, False, False, False),
        # Dataclass with LazyBytes field
        (_run_dataclass_param, False, True, False),
        (_run_dataclass_return, True, False, False),
        (_run_dataclass_wrong_tag_param, False, False, False),
        (_run_dataclass_no_lazybytes_param, False, False, False),
        # Non-callable run – get_type_hints raises, task must not register
        pytest.param("not a callable", False, False, False, id="bad_type_hints"),
    ],
)
def test_registration(
    run_func, in_producing: bool, in_consuming: bool, in_consuming_producing: bool
) -> None:
    name = f"test.{run_func.__name__ if callable(run_func) else 'bad_hints'}"
    task = _make_task(name, run_func)
    register_if_lazybytes_task(task)
    assert (
        name in _task_groups.get(TaskGroupName.LAZYBYTES_PRODUCING, [])
    ) == in_producing
    assert (
        name in _task_groups.get(TaskGroupName.LAZYBYTES_CONSUMING, [])
    ) == in_consuming
    assert (
        name in _task_groups.get(TaskGroupName.LAZYBYTES_CONSUMING_PRODUCING, [])
    ) == in_consuming_producing
