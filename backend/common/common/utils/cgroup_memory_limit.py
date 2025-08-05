import os


class MemoryLimitNotFoundError(Exception):
    """Raised when the memory limit could not be determined from the cgroup context."""


def get_cgroup_memory_limit() -> int:
    """Retrieves the memory limit for the current container from the cgroup filesystem.

    This function supports both cgroup v1 and cgroup v2 and reads the appropriate file
    to obtain the memory limit in bytes.

    Returns:
        int: The memory limit in bytes.

    Raises:
        MemoryLimitNotFoundError: If the memory limit could not be determined.
    """
    # Check for cgroup v2
    cgroup_v2_path = "/sys/fs/cgroup/memory.max"
    if os.path.exists(cgroup_v2_path):
        try:
            with open(cgroup_v2_path, "r", encoding="utf-8") as fd:
                value = fd.read().strip()
                if value == "max":
                    raise MemoryLimitNotFoundError(
                        "No memory limit set in cgroup v2 (value is 'max')."
                    )
                return int(value)
        except (OSError, ValueError) as ex:
            raise MemoryLimitNotFoundError(
                f"Failed to read cgroup v2 memory limit: {ex}"
            ) from ex

    # Check for cgroup v1
    cgroup_v1_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    if os.path.exists(cgroup_v1_path):
        try:
            with open(cgroup_v1_path, "r", encoding="utf-8") as fd:
                value = fd.read().strip()
                limit = int(value)
                # On some systems, "unlimited" might be represented by a very large number
                if limit >= 1 << 60:  # Treat as no limit
                    raise MemoryLimitNotFoundError(
                        "Memory limit is effectively unlimited in cgroup v1."
                    )
                return limit
        except (OSError, ValueError) as ex:
            raise MemoryLimitNotFoundError(
                f"Failed to read cgroup v1 memory limit: {ex}"
            ) from ex

    raise MemoryLimitNotFoundError("Cgroup memory limit file not found.")
