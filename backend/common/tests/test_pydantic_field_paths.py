from typing import Optional

from pydantic import BaseModel

from common.utils.pydantic_field_paths import iter_field_paths_by_type


class Leaf(BaseModel):
    pass


class Target(BaseModel):
    pass


class FlatModel(BaseModel):
    a: Target
    b: str
    c: int


class OptionalModel(BaseModel):
    a: Optional[Target]
    b: Target | None
    c: str


class NestedModel(BaseModel):
    inner: FlatModel
    direct: Target


class DeepModel(BaseModel):
    level1: NestedModel


class MultiTargetModel(BaseModel):
    first: Target
    middle: str
    second: Target


class MultiUnionModel(BaseModel):
    ambiguous: Target | str  # two non-None arms — should NOT match


class NoMatchModel(BaseModel):
    a: str
    b: int
    c: Leaf


def _paths(model: type[BaseModel], suffix: str = "") -> list[str]:
    return list(iter_field_paths_by_type(model, Target, suffix=suffix))


def test_direct_field_match() -> None:
    assert _paths(FlatModel) == ["a"]


def test_non_matching_fields_excluded() -> None:
    paths = _paths(FlatModel)
    assert "b" not in paths
    assert "c" not in paths


def test_no_match_returns_empty() -> None:
    assert not _paths(NoMatchModel)


def test_optional_field_unwrapped() -> None:
    paths = _paths(OptionalModel)
    assert "a" in paths
    assert "b" in paths
    assert "c" not in paths


def test_nested_model_recurse() -> None:
    paths = _paths(NestedModel)
    assert "inner.a" in paths
    assert "direct" in paths


def test_deeply_nested_model() -> None:
    paths = _paths(DeepModel)
    assert "level1.inner.a" in paths
    assert "level1.direct" in paths


def test_multiple_matches() -> None:
    paths = _paths(MultiTargetModel)
    assert paths == ["first", "second"]


def test_suffix_appended() -> None:
    paths = _paths(FlatModel, suffix=".service_id")
    assert paths == ["a.service_id"]


def test_suffix_appended_nested() -> None:
    paths = _paths(NestedModel, suffix=".id")
    assert "inner.a.id" in paths
    assert "direct.id" in paths


def test_union_with_multiple_non_none_arms_not_matched() -> None:
    # Target | str has two non-None arms — should not be treated as Target
    assert not _paths(MultiUnionModel)


def test_empty_model() -> None:
    class Empty(BaseModel):
        pass

    assert not _paths(Empty)


def test_no_suffix_by_default() -> None:
    paths = list(iter_field_paths_by_type(FlatModel, Target))
    assert paths == ["a"]
