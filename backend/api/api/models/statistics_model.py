from typing import List

from common.file.file_statistics import StatisticsGeneric, StatisticsSummary
from pydantic import BaseModel


class TagsStatisticsEntryModel(BaseModel):
    """Stats about a single tag."""

    name: str
    hits_count: int


class HitsPerGroupEntryModel(BaseModel):
    """Stats about a single extension."""

    name: str
    hits_count: int


class SummaryStatisticsModel(BaseModel):
    """Summary stats about all files."""

    count: int
    min: int
    max: int
    avg: int

    @staticmethod
    def from_statistics_summary(stats: StatisticsSummary):
        return SummaryStatisticsModel(
            count=stats.total_no_of_files,
            min=stats.min_file_size,
            max=stats.max_file_size,
            avg=stats.avg_file_size,
        )


class GenericStatisticsModel(BaseModel):
    stat: str
    key: str
    data: List[HitsPerGroupEntryModel]
    file_count: int

    @staticmethod
    def from_statistics_generic(stats: StatisticsGeneric):
        return GenericStatisticsModel(
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
        )
