from typing import List

from common.file.file_statistics import StatisticsGeneric, StatisticsSummary
from pydantic import BaseModel, Field, RootModel, computed_field


class CacheStatisticsEntryModel(BaseModel):
    """Cache stats of task caching."""

    mem_size: int
    entries_count: int
    hits_count: int
    miss_count: int


class CacheStatistics(RootModel):
    root: dict[str, CacheStatisticsEntryModel] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def mem_size_total(self) -> int:
        return sum(caching_result.mem_size for caching_result in self.root.values())

    @computed_field  # type: ignore[misc]
    @property
    def entries_count_total(self) -> int:
        return sum(
            caching_result.entries_count for caching_result in self.root.values()
        )

    @computed_field  # type: ignore[misc]
    @property
    def hits_count_total(self) -> int:
        return sum(caching_result.hits_count for caching_result in self.root.values())

    @computed_field  # type: ignore[misc]
    @property
    def miss_count_total(self) -> int:
        return sum(caching_result.miss_count for caching_result in self.root.values())

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, newvalue):
        self.root[key] = newvalue


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
