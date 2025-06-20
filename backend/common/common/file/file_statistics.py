"""File statistics."""

from typing import List

from pydantic import BaseModel


class StatisticsEntry(BaseModel):
    """Stats about a single tag or extension."""

    name: str
    hits_count: int


class StatisticsGeneric(BaseModel):
    """Stats about a single tag or extension."""

    stat: str
    key: str
    data: List[StatisticsEntry]
    total_no_of_files: int


class StatisticsSummary(BaseModel):
    """Stats about all files."""

    avg_file_size: int
    max_file_size: int
    min_file_size: int
    total_no_of_files: int
