from typing import Literal

from common.file.file_statistics import (
    GroupedHistogramStatistics,
    TermsStatistics,
)
from pydantic import BaseModel


class TagsStatisticsEntryModel(BaseModel):
    """Stats about a single tag."""

    name: str
    hits_count: int


class HitsPerGroupEntryModel(BaseModel):
    """Stats about a single extension."""

    name: str
    hits_count: int


class TermsStatisticsModel(BaseModel):
    stat: str
    key: str
    data: list[HitsPerGroupEntryModel]
    file_count: int
    others_count: int = 0
    min_value: float | None = None
    max_value: float | None = None

    @staticmethod
    def from_terms_statistics(stats: TermsStatistics) -> "TermsStatisticsModel":
        return TermsStatisticsModel(
            stat=stats.stat,
            key=stats.key,
            data=list(
                map(
                    lambda e: HitsPerGroupEntryModel(
                        name=e.name, hits_count=e.hits_count
                    ),
                    stats.data,
                )
            ),
            file_count=stats.total_no_of_files,
            others_count=stats.others_count,
            min_value=stats.min_value,
            max_value=stats.max_value,
        )


class GroupedHitsPerGroupEntryModel(BaseModel):
    name: str
    groups: dict[str, int]
    hits_count: int


class GroupedHistogramStatisticsModel(BaseModel):
    stat: str
    group_by: str
    key: str
    histogram_type: Literal["date", "number"]
    data: list[GroupedHitsPerGroupEntryModel]
    file_count: int
    min_value: float | None = None
    max_value: float | None = None

    @staticmethod
    def from_grouped_histogram_statistics(
        stats: GroupedHistogramStatistics,
    ) -> "GroupedHistogramStatisticsModel":
        return GroupedHistogramStatisticsModel(
            stat=stats.stat,
            group_by=stats.group_by,
            key=stats.key,
            histogram_type=stats.histogram_type,
            data=[
                GroupedHitsPerGroupEntryModel(
                    name=e.name,
                    groups=e.groups,
                    hits_count=e.hits_count,
                )
                for e in stats.data
            ],
            file_count=stats.total_no_of_files,
            min_value=stats.min_value,
            max_value=stats.max_value,
        )
