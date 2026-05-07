import pytest
from pydantic import BaseModel

from worker.utils.clustering import kde_filter_highest_cluster


class FooScore(BaseModel):
    score: float


@pytest.mark.parametrize(
    "items",
    [[]],
)
def test_empty(items: list[FooScore]):
    filtered_items = kde_filter_highest_cluster(items, lambda fs: fs.score)
    assert len(filtered_items) == 0


LOW_CLUSTER = [
    0.1,
    0.11,
    0.12,
]
HIGH_CLUSTER = [
    0.8,
    0.85,
    0.9,
]


@pytest.mark.parametrize(
    "items,expected_scores",
    [
        [
            [FooScore(score=score) for score in [*HIGH_CLUSTER, *LOW_CLUSTER]],
            HIGH_CLUSTER,
        ],
        [
            [FooScore(score=score) for score in [*LOW_CLUSTER, *HIGH_CLUSTER]],
            HIGH_CLUSTER,
        ],
    ],
)
def test_returns_highest_of_two_clusters(items: list[FooScore], expected_scores):
    filtered_items = kde_filter_highest_cluster(items, lambda fs: fs.score)
    filtered_scores = [score.score for score in filtered_items]
    for score in expected_scores:
        assert score in filtered_scores


@pytest.mark.parametrize(
    "items",
    [
        [
            FooScore(score=score)
            for score in [
                0.1,
                0.2,
                0.3,
                0.4,
                0.5,
            ]
        ]
    ],
)
def test_uniform_distribution_has_no_clusters(items: list[FooScore]):
    filtered_items = kde_filter_highest_cluster(items, lambda fs: fs.score)
    assert filtered_items == items


@pytest.mark.parametrize(
    "items",
    [
        [
            FooScore(score=score)
            for score in [
                0.81,
                0.82,
                0.83,
                0.84,
            ]
        ]
    ],
)
def test_returns_single_cluster_unchanged(items: list[FooScore]):
    filtered_items = kde_filter_highest_cluster(items, lambda fs: fs.score)
    assert filtered_items == items
