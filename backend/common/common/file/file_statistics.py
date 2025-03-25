"""File statistics."""

from dataclasses import dataclass
from typing import List


@dataclass
class StatisticsEntry:
    """Stats about a single tag or extension."""

    name: str
    hits_count: int


@dataclass
class StatisticsGeneric:
    """Stats about a single tag or extension."""

    stat: str
    key: str
    data: List[StatisticsEntry]
    total_no_of_files: int


@dataclass
class StatisticsSummary:
    """Stats about all files."""

    avg_file_size: int
    max_file_size: int
    min_file_size: int
    total_no_of_files: int


# pylint: disable=too-many-instance-attributes
@dataclass
class FileStatistics:
    """Stats about all files."""

    avg_file_size: float
    max_file_size: int
    min_file_size: int
    total_no_of_files: int
    sources: List[StatisticsEntry]
    states: List[StatisticsEntry]
    extensions: List[StatisticsEntry]
    tags: List[StatisticsEntry]
    file_type_tika: List[StatisticsEntry]
    file_type_magic: List[StatisticsEntry]
    language_tika: List[StatisticsEntry]
    language_libretranslate: List[StatisticsEntry]
    is_spam: List[StatisticsEntry]
