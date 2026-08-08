"""File statistics."""

import dataclasses
from typing import Callable, Literal, TypeVar

from pydantic import BaseModel

from common.utils.pydantic_field_paths import iter_field_paths_by_metadata


def snake_to_title(name: str) -> str:
    return name.replace("_", " ").title()


def _boolean_transform(s: str) -> str:
    return str(bool(int(s))).lower()


@dataclasses.dataclass(frozen=True)
class Stat:
    """Base annotation marker for statistics fields.

    Do not use directly — annotate fields with ``TermsStat``,
    ``DateHistogramStat``, or ``NumberHistogramStat`` instead.
    ``discover_stats`` recognises any instance of this class (or its
    subclasses) as a stat marker.

    Attributes:
        label: Human-readable label; auto-derived from the field name if empty.
        transform: Optional value transform applied to each bucket key before display.
        keyword: When True, append ``.keyword`` to the derived ES field path.
          Use for text fields that have a ``.keyword`` sub-field in the mapping.
    """

    label: str = ""
    transform: Callable[[str], str] | None = None
    keyword: bool = False


@dataclasses.dataclass(frozen=True)
class TermsStat(Stat):
    """Stat annotation for keyword/boolean fields aggregated as ES terms."""


@dataclasses.dataclass(frozen=True)
class BooleanTermsStat(TermsStat):
    """TermsStat for boolean fields.

    Automatically applies the boolean transform (ES stores booleans as 0/1 strings) and
    omits the ``missing`` parameter from aggregations (ES rejects non-boolean missing
    values).
    """

    transform: Callable[[str], str] | None = _boolean_transform


@dataclasses.dataclass(frozen=True)
class HistogramStat(Stat):
    """Base annotation marker for histogram stat fields (date or number).

    Do not use directly — annotate fields with ``DateHistogramStat`` or
    ``NumberHistogramStat`` instead.
    """


@dataclasses.dataclass(frozen=True)
class DateHistogramStat(HistogramStat):
    """Stat annotation for date fields aggregated as ES auto_date_histogram."""


@dataclasses.dataclass(frozen=True)
class NumberHistogramStat(HistogramStat):
    """Stat annotation for numeric fields aggregated as ES histogram."""


@dataclasses.dataclass(frozen=True)
class PreviewableField:
    """Annotation marker for File fields that can be included in preview responses.

    Annotate a field with this to expose it via ``GET /files/preview-fields`` and
    allow clients to request it via the ``fields`` query param.

    Attributes:
        label: Human-readable label; auto-derived from the field name if empty.
        id: Preview field ID sent to the client; defaults to the field name.
            Set explicitly when the Python field name differs from the desired
            preview key (e.g. ``translations`` → ``"translation_preview"``).
    """

    label: str = ""
    id: str = ""


@dataclasses.dataclass(frozen=True)
class DiscoveredPreviewField:
    """A preview field as resolved by discover_preview_fields().

    Attributes:
        id: Preview field ID used in API requests/responses.
        label: Human-readable label shown in the UI.
        path: Dotted model path (e.g. ``"tika_meta.dc_title"``).
            Use this to traverse the ``File`` object at extraction time.
    """

    id: str
    label: str
    path: str


def discover_preview_fields(
    model_class: type[BaseModel],
) -> dict[str, DiscoveredPreviewField]:
    """Discover fields annotated with PreviewableField on a Pydantic model.

    Returns a dict mapping preview field ID → DiscoveredPreviewField with resolved id,
    label, and the dotted model path for generic extraction.
    """
    result: dict[str, DiscoveredPreviewField] = {}
    for field in iter_field_paths_by_metadata(model_class, PreviewableField):
        parts = field.path.split(".")
        field_id = field.marker.id or field.path
        label = field.marker.label or snake_to_title(parts[-1])
        result[field_id] = DiscoveredPreviewField(
            id=field_id, label=label, path=field.path
        )
    return result


_T = TypeVar("_T", bound=Stat)


def discover_stats(
    model_class: type[BaseModel],
    stat_type: type[_T],
) -> dict[str, _T]:
    """Build a stat registry from annotated fields in a Pydantic model.

    Traverses ``model_class`` recursively (including nested models and list-of-model
    fields) and collects every field carrying an annotation that is an instance of
    ``stat_type``.  The dict key is the ES field path; the value is the annotation
    instance with ``label`` resolved and ``keyword`` cleared (already baked into the
    key).
    """
    result: dict[str, _T] = {}
    for field in iter_field_paths_by_metadata(model_class, Stat):
        if not isinstance(field.marker, stat_type):
            continue
        es_field = f"{field.path}.keyword" if field.marker.keyword else field.path
        if field.marker.label:
            label = field.marker.label
        else:
            parts = field.path.split(".")
            label_parts = parts[-2:] if len(parts) >= 3 else parts[-1:]
            label = snake_to_title("_".join(label_parts))
        result[es_field] = dataclasses.replace(field.marker, label=label, keyword=False)
    return result


class StatisticsEntry(BaseModel):
    """Stats about a single tag or extension."""

    name: str
    hits_count: int


class TermsStatistics(BaseModel):
    """Stats about a single tag or extension."""

    stat: str
    key: str
    data: list[StatisticsEntry]
    total_no_of_files: int
    others_count: int = 0
    min_value: float | None = None
    max_value: float | None = None


class GroupedStatisticsEntry(BaseModel):
    """One time bucket in a grouped date-histogram stat."""

    name: str
    groups: dict[str, int]
    hits_count: int


class GroupedHistogramStatistics(BaseModel):
    """Histogram stat with per-bucket term breakdown."""

    stat: str
    group_by: str
    key: str
    histogram_type: Literal["date", "number"]
    data: list[GroupedStatisticsEntry]
    total_no_of_files: int
    min_value: float | None = None
    max_value: float | None = None


class AvailableStat(BaseModel):
    """A stat field that can be queried via the stats endpoints."""

    id: str
    label: str
