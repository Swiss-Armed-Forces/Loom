from random import shuffle
from uuid import uuid4

import pytest
from common.services.lazybytes_service import LazyBytes

from worker.ai.tasks.rag import RankedSearchEmbedding, filter_ranked_search_embeddings


@pytest.mark.parametrize(
    "clusters,",
    [
        ([1.0, 1.0, 1.0], [3.0, 3.0], [5.0, 5.0, 5.0]),
        ([1.0, 1.0, 1.0, 1.0, 1.0], [5.0]),
        ([1.0, 1.0, 1.0, 1.0, 1.0],),
        (
            [
                1.0,
            ],
        ),
    ],
)
def test_filter_ranked_file_text(clusters: list[list[float]]):
    def get_ranked_search_embedding(rank: float):
        return RankedSearchEmbedding(
            file_id=uuid4(),
            file_score=1,
            text_score=1,
            text_lazy=LazyBytes(embedded_data=b""),
            rank=rank,
        )

    shuffled_ranked_search_embedding: list[RankedSearchEmbedding] = []
    for cluster in clusters:
        last_cluster_ranked_search_embedding: list[RankedSearchEmbedding] = []
        for rank in cluster:
            ranked_search_embedding = get_ranked_search_embedding(rank)
            shuffled_ranked_search_embedding.append(ranked_search_embedding)
            last_cluster_ranked_search_embedding.append(ranked_search_embedding)

    # repeat for different input orderings
    for _ in range(len(shuffled_ranked_search_embedding)):
        shuffle(shuffled_ranked_search_embedding)

        filtered_ranks = filter_ranked_search_embeddings(
            shuffled_ranked_search_embedding
        )

        assert len(filtered_ranks) == len(last_cluster_ranked_search_embedding)
        for c in last_cluster_ranked_search_embedding:
            assert c in filtered_ranks
