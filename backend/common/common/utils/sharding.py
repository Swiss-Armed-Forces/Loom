"""Sharding utilities for persister task routing."""

import hashlib
from uuid import UUID

PERSISTER_SHARD_QUEUE_PREFIX: str = "celery.persister.shard"


def compute_shard(entity_id: UUID, num_shards: int) -> int:
    """Compute shard number for an entity ID using consistent hashing.

    Args:
        entity_id: The UUID of the entity to shard.
        num_shards: The total number of shards.

    Returns:
        The shard number (0 to num_shards-1).
    """
    hash_bytes = hashlib.sha256(entity_id.bytes).digest()[:8]
    return int.from_bytes(hash_bytes, byteorder="big") % num_shards


def get_persister_shard_queue_name(shard: int) -> str:
    """Get the queue name for a given persister shard.

    Args:
        shard: The shard number.

    Returns:
        The queue name for the shard.
    """
    return f"{PERSISTER_SHARD_QUEUE_PREFIX}.{shard}"


def get_all_persister_shard_queues(num_shards: int) -> list[str]:
    """Get all persister shard queue names.

    Args:
        num_shards: The total number of shards.

    Returns:
        List of all persister shard queue names.
    """
    return [get_persister_shard_queue_name(i) for i in range(num_shards)]


def get_shards_for_persister(
    persister_id: int,
    persister_total: int,
    num_shards: int,
) -> list[int]:
    """Get the shard numbers assigned to a specific persister worker.

    Shards are distributed across persisters using modulo assignment:
    persister_id=0 gets shards 0, persister_total, 2*persister_total, ...
    persister_id=1 gets shards 1, persister_total+1, 2*persister_total+1, ...

    Args:
        persister_id: The ID of this persister worker (0 to persister_total-1).
        persister_total: Total number of persister workers.
        num_shards: The total number of shards.

    Returns:
        List of shard numbers assigned to this persister.
    """
    return [s for s in range(num_shards) if s % persister_total == persister_id]


def get_persister_shard_queues_for_worker(
    persister_id: int,
    persister_total: int,
    num_shards: int,
) -> list[str]:
    """Get the queue names for shards assigned to this persister worker.

    Args:
        persister_id: The ID of this persister worker (0 to persister_total-1).
        persister_total: Total number of persister workers.
        num_shards: The total number of shards.

    Returns:
        List of queue names for the shards assigned to this worker.
    """
    shards = get_shards_for_persister(persister_id, persister_total, num_shards)
    return [get_persister_shard_queue_name(s) for s in shards]
