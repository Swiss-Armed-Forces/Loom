import dataclasses
from typing import Annotated, Optional

from pydantic import BaseModel, computed_field

from common.utils.pydantic_field_paths import (
    iter_field_paths_by_metadata,
    iter_field_paths_by_type,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# iter_field_paths_by_type tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# iter_field_paths_by_metadata tests
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Mark:
    """Dummy metadata marker for testing."""

    value: str = ""


class FlatMarked(BaseModel):
    a: Annotated[str, Mark("x")]
    b: str
    c: int


class OptionalMarked(BaseModel):
    a: Annotated[str | None, Mark()]
    b: str | None


class NestedMarked(BaseModel):
    class Inner(BaseModel):
        x: Annotated[str, Mark()]
        y: str

    inner: Inner
    top: Annotated[str, Mark()]


class ListOfMarked(BaseModel):
    class Item(BaseModel):
        name: Annotated[str, Mark()]
        skip: str

    items: list[Item]


class ComputedMarked(BaseModel):
    plain: str

    @computed_field  # type: ignore[misc]
    @property
    def derived(self) -> Annotated[str, Mark()]:
        return self.plain.upper()


class NoMarks(BaseModel):
    a: str
    b: int


def _meta_paths(model: type[BaseModel]) -> list[str]:
    return [result.path for result in iter_field_paths_by_metadata(model, Mark)]


def test_meta_direct_match() -> None:
    assert _meta_paths(FlatMarked) == ["a"]


def test_meta_unmarked_fields_excluded() -> None:
    paths = _meta_paths(FlatMarked)
    assert "b" not in paths
    assert "c" not in paths


def test_meta_optional_unwrapped() -> None:
    assert "a" in _meta_paths(OptionalMarked)
    assert "b" not in _meta_paths(OptionalMarked)


def test_meta_nested_model_recurse() -> None:
    paths = _meta_paths(NestedMarked)
    assert "inner.x" in paths
    assert "top" in paths
    assert "inner.y" not in paths


def test_meta_list_of_model_recurse() -> None:
    paths = _meta_paths(ListOfMarked)
    assert "items.name" in paths
    assert "items.skip" not in paths


def test_meta_computed_field() -> None:
    assert "derived" in _meta_paths(ComputedMarked)
    assert "plain" not in _meta_paths(ComputedMarked)


def test_meta_no_marks_returns_empty() -> None:
    assert not _meta_paths(NoMarks)


def test_meta_marker_value_preserved() -> None:
    results = {r.path: r.marker for r in iter_field_paths_by_metadata(FlatMarked, Mark)}
    assert results["a"].value == "x"
