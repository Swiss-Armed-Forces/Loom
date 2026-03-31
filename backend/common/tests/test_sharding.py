"""Tests for the sharding module."""

from uuid import UUID, uuid4

import pytest

from common.utils.sharding import (
    PERSISTER_SHARD_QUEUE_PREFIX,
    compute_shard,
    get_all_persister_shard_queues,
    get_persister_shard_queue_name,
    get_persister_shard_queues_for_worker,
    get_shards_for_persister,
)


class TestComputeShard:
    """Tests for compute_shard function."""

    def test_returns_integer_in_valid_range(self):
        """Shard should be between 0 and num_shards - 1."""
        entity_id = uuid4()
        shard = compute_shard(entity_id, num_shards=16)
        assert 0 <= shard < 16

    def test_returns_integer_in_valid_range_custom_shards(self):
        """Shard should respect custom num_shards."""
        entity_id = uuid4()
        num_shards = 8
        shard = compute_shard(entity_id, num_shards)
        assert 0 <= shard < num_shards

    def test_consistent_for_same_id(self):
        """Same entity ID should always produce the same shard."""
        entity_id = uuid4()
        shard1 = compute_shard(entity_id, num_shards=16)
        shard2 = compute_shard(entity_id, num_shards=16)
        assert shard1 == shard2

    def test_different_ids_can_produce_different_shards(self):
        """Different entity IDs should distribute across shards."""
        shards = {compute_shard(uuid4(), num_shards=16) for _ in range(100)}
        # With 100 random UUIDs and 16 shards, we should hit multiple shards
        assert len(shards) > 1

    def test_deterministic_for_known_uuid(self):
        """Test with a fixed UUID for regression testing."""
        entity_id = UUID("12345678-1234-5678-1234-567812345678")
        shard = compute_shard(entity_id, num_shards=16)
        # This should be deterministic - same UUID always gives same shard
        assert compute_shard(entity_id, num_shards=16) == shard

    def test_single_shard(self):
        """With one shard, all IDs should map to shard 0."""
        for _ in range(10):
            assert compute_shard(uuid4(), num_shards=1) == 0

    @pytest.mark.parametrize("num_shards", [2, 4, 8, 16, 32, 64])
    def test_various_shard_counts(self, num_shards: int):
        """Shards should be valid for various shard counts."""
        for _ in range(50):
            shard = compute_shard(uuid4(), num_shards)
            assert 0 <= shard < num_shards


class TestGetPersisterShardQueueName:
    """Tests for get_persister_shard_queue_name function."""

    def test_format(self):
        """Queue name should follow expected format."""
        assert get_persister_shard_queue_name(0) == f"{PERSISTER_SHARD_QUEUE_PREFIX}.0"
        assert get_persister_shard_queue_name(5) == f"{PERSISTER_SHARD_QUEUE_PREFIX}.5"
        assert (
            get_persister_shard_queue_name(15) == f"{PERSISTER_SHARD_QUEUE_PREFIX}.15"
        )

    def test_uses_prefix_constant(self):
        """Queue name should use the PERSISTER_SHARD_QUEUE_PREFIX constant."""
        queue_name = get_persister_shard_queue_name(0)
        assert queue_name.startswith(PERSISTER_SHARD_QUEUE_PREFIX)


class TestGetAllPersisterShardQueues:
    """Tests for get_all_persister_shard_queues function."""

    def test_returns_correct_count(self):
        """Should return specified number of queues."""
        queues = get_all_persister_shard_queues(num_shards=8)
        assert len(queues) == 8

    def test_queues_are_ordered(self):
        """Queues should be returned in order from 0 to num_shards - 1."""
        queues = get_all_persister_shard_queues(num_shards=4)
        assert queues == [
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.0",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.1",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.2",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.3",
        ]

    def test_queues_are_unique(self):
        """All queue names should be unique."""
        queues = get_all_persister_shard_queues(num_shards=16)
        assert len(queues) == len(set(queues))

    def test_single_shard(self):
        """Single shard should return one queue."""
        queues = get_all_persister_shard_queues(num_shards=1)
        assert queues == [f"{PERSISTER_SHARD_QUEUE_PREFIX}.0"]


class TestGetShardsForPersister:
    """Tests for get_shards_for_persister function."""

    def test_single_persister_gets_all_shards(self):
        """Single persister should get all shards."""
        shards = get_shards_for_persister(
            persister_id=0, persister_total=1, num_shards=16
        )
        assert shards == list(range(16))

    def test_two_persisters_split_shards_evenly(self):
        """Two persisters should each get half the shards."""
        shards_0 = get_shards_for_persister(
            persister_id=0, persister_total=2, num_shards=16
        )
        shards_1 = get_shards_for_persister(
            persister_id=1, persister_total=2, num_shards=16
        )

        assert shards_0 == [0, 2, 4, 6, 8, 10, 12, 14]
        assert shards_1 == [1, 3, 5, 7, 9, 11, 13, 15]

    def test_four_persisters_split_shards(self):
        """Four persisters should each get a quarter of the shards."""
        shards_0 = get_shards_for_persister(
            persister_id=0, persister_total=4, num_shards=16
        )
        shards_1 = get_shards_for_persister(
            persister_id=1, persister_total=4, num_shards=16
        )
        shards_2 = get_shards_for_persister(
            persister_id=2, persister_total=4, num_shards=16
        )
        shards_3 = get_shards_for_persister(
            persister_id=3, persister_total=4, num_shards=16
        )

        assert shards_0 == [0, 4, 8, 12]
        assert shards_1 == [1, 5, 9, 13]
        assert shards_2 == [2, 6, 10, 14]
        assert shards_3 == [3, 7, 11, 15]

    def test_covers_all_shards(self):
        """All persisters combined should cover all shards exactly once."""
        num_shards = 16
        persister_total = 3
        all_shards: list[int] = []

        for persister_id in range(persister_total):
            shards = get_shards_for_persister(persister_id, persister_total, num_shards)
            all_shards.extend(shards)

        assert sorted(all_shards) == list(range(num_shards))

    def test_no_overlap_between_persisters(self):
        """Different persisters should not share any shards."""
        num_shards = 16
        persister_total = 5

        all_shards: list[int] = []
        for persister_id in range(persister_total):
            shards = get_shards_for_persister(persister_id, persister_total, num_shards)
            all_shards.extend(shards)

        # No duplicates means no overlap
        assert len(all_shards) == len(set(all_shards))

    @pytest.mark.parametrize(
        "persister_total,num_shards",
        [(1, 16), (2, 16), (3, 16), (4, 16), (8, 16), (16, 16), (2, 8), (3, 9)],
    )
    def test_various_configurations_cover_all_shards(
        self, persister_total: int, num_shards: int
    ):
        """Various configurations should always cover all shards exactly once."""
        all_shards: list[int] = []

        for persister_id in range(persister_total):
            shards = get_shards_for_persister(persister_id, persister_total, num_shards)
            all_shards.extend(shards)

        assert sorted(all_shards) == list(range(num_shards))


class TestGetPersisterShardQueuesForWorker:
    """Tests for get_persister_shard_queues_for_worker function."""

    def test_returns_correct_queue_names(self):
        """Should return queue names for assigned shards."""
        queues = get_persister_shard_queues_for_worker(
            persister_id=0, persister_total=2, num_shards=4
        )
        assert queues == [
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.0",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.2",
        ]

    def test_single_persister_gets_all_queues(self):
        """Single persister should get all queues."""
        queues = get_persister_shard_queues_for_worker(
            persister_id=0, persister_total=1, num_shards=4
        )
        assert queues == get_all_persister_shard_queues(num_shards=4)

    def test_two_persisters_split_queues(self):
        """Two persisters should split queues evenly."""
        queues_0 = get_persister_shard_queues_for_worker(
            persister_id=0, persister_total=2, num_shards=4
        )
        queues_1 = get_persister_shard_queues_for_worker(
            persister_id=1, persister_total=2, num_shards=4
        )

        assert queues_0 == [
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.0",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.2",
        ]
        assert queues_1 == [
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.1",
            f"{PERSISTER_SHARD_QUEUE_PREFIX}.3",
        ]

    def test_single_persister_with_16_shards(self):
        """Single persister should get all 16 shards."""
        queues = get_persister_shard_queues_for_worker(
            persister_id=0, persister_total=1, num_shards=16
        )
        assert len(queues) == 16
