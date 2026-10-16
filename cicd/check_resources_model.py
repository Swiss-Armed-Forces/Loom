"""The domain model of the Kubernetes resource calculator.

The quantities, workloads and report a manifest is read into, and the parsing that turns
Kubernetes' unit syntax into integers. Separated from the calculation, reporting and CLI
in check_resources.py so that neither file has to be read whole to follow the other.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
class ResourceName(StrEnum):
    """Standard Kubernetes resource names."""

    CPU = "cpu"
    MEMORY = "memory"
    EPHEMERAL_STORAGE = "ephemeral-storage"


class WorkloadKind(StrEnum):
    """Kubernetes workload kinds that contain pods."""

    POD = "Pod"
    DEPLOYMENT = "Deployment"
    STATEFUL_SET = "StatefulSet"
    REPLICA_SET = "ReplicaSet"
    DAEMON_SET = "DaemonSet"
    JOB = "Job"
    CRON_JOB = "CronJob"


CPU_MILLICORES = {"m": 1, "": 1000}
# Conversion factors to bytes
MEMORY_UNITS = {
    # Binary units (IEC) - base 1024
    "Ki": 1024,
    "Mi": 1024**2,
    "Gi": 1024**3,
    "Ti": 1024**4,
    "Pi": 1024**5,
    # Decimal units (SI) - base 1000, converted to bytes
    "K": 1000,
    "M": 1000**2,
    "G": 1000**3,
    "T": 1000**4,
    "P": 1000**5,
}

REPLICATED_WORKLOADS: set[str] = {
    WorkloadKind.DEPLOYMENT,
    WorkloadKind.STATEFUL_SET,
    WorkloadKind.REPLICA_SET,
}
WORKLOADS_WITH_PODS: set[str] = {kind.value for kind in WorkloadKind}

# Compiled regex patterns
CPU_REGEX = re.compile(r"^(\d+(?:\.\d+)?)(m?)$")
# Case-insensitive regex for memory units
MEMORY_REGEX = re.compile(r"^(\d+(?:\.\d+)?)([KMGT]i?)$", re.IGNORECASE)
# Regex for bare numbers without units
BARE_NUMBER_REGEX = re.compile(r"^\d+(?:\.\d+)?$")


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ResourceQuantity:
    """Container for arbitrary resource quantities."""

    resources: dict[str, int] = field(default_factory=dict)

    def get(self, key: str, default: int = 0) -> int:
        """Get resource value by key."""
        return self.resources.get(key, default)

    def keys(self) -> set[str]:
        """Get all resource keys."""
        return set(self.resources.keys())

    def __add__(self, other: "ResourceQuantity") -> "ResourceQuantity":
        """Add two resource quantities."""
        merged = dict(self.resources)
        for key, val in other.resources.items():
            merged[key] = merged.get(key, 0) + val
        return ResourceQuantity(merged)

    def __mul__(self, multiplier: int) -> "ResourceQuantity":
        """Scale resources by multiplier."""
        return ResourceQuantity({k: v * multiplier for k, v in self.resources.items()})


@dataclass
class Container:
    """Container with resource specifications."""

    name: str
    container_type: str
    requests: ResourceQuantity
    limits: ResourceQuantity


@dataclass
class Workload:
    """Parsed Kubernetes workload."""

    kind: str
    name: str
    namespace: str
    replicas: int
    replica_source: str
    containers: list[Container] = field(default_factory=list)
    is_daemonset: bool = False


@dataclass(frozen=True)
class ParsedThreshold:
    """One `resource=value` threshold, and anything the user should know about it."""

    resource: str
    value: int
    warning: str | None = None


@dataclass(frozen=True)
class QuotaThresholds:
    """resourceQuotas.scalable, as read from a Helm values file."""

    requests: dict[str, int]
    limits: dict[str, int]
    enabled: bool


@dataclass(frozen=True)
class ContainerResources:
    """What a container asks for and what it is capped at."""

    requests: ResourceQuantity
    limits: ResourceQuantity


@dataclass(frozen=True)
class ReplicaCount:
    """How many copies of a workload's pod run, and which field said so."""

    count: int
    source: str
    scales_with_nodes: bool = False


def read_replica_count(value: Any, source: str) -> ReplicaCount:
    """Read a replica field, falling back to one when it is absent or unusable."""
    if (
        value is not None
        and isinstance(value, (int, float, str))
        and not isinstance(value, bool)
    ):
        count = safe_int(value)
        if count >= 0:
            return ReplicaCount(count=count, source=source)
    return ReplicaCount(count=1, source=f"{source} (default)")


@dataclass
class CalculatorReport:
    """Calculation results."""

    total_requests: ResourceQuantity
    total_limits: ResourceQuantity
    workloads: list[Workload]
    node_count: int

    def get_all_resource_types(self) -> set[str]:
        """Get all resource types found in the calculation."""
        return self.total_requests.keys() | self.total_limits.keys()


# -----------------------------------------------------------------------------
# Parsing Utilities
# -----------------------------------------------------------------------------
def normalize_unit(unit: str) -> str:
    """Normalize unit string to match MEMORY_UNITS keys (e.g., 'ki' -> 'Ki', 'k' ->
    'K')."""
    if len(unit) > 1:
        return unit[0].upper() + unit[1:].lower()
    return unit.upper()


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return default
    return default


def parse_cpu(value: Any) -> int:
    """Parse CPU value to millicores."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value * 1000)

    str_val = str(value).strip()
    match = CPU_REGEX.match(str_val)
    if not match:
        logger.warning("Could not parse CPU value: %r", value)
        return 0

    num, unit = match.groups()
    multiplier = CPU_MILLICORES.get(unit, 1000)
    return int(float(num) * multiplier)


def is_bare_number(val: str) -> bool:
    """Check if value is a bare number without units."""
    return bool(BARE_NUMBER_REGEX.match(val.strip()))


def parse_memory(value: Any) -> int:
    """Parse memory value to bytes.

    Raw numbers are treated as bytes.
    """
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        # Raw integer/float is treated as bytes
        return int(value)

    str_val = str(value).strip()
    match = MEMORY_REGEX.match(str_val)
    if match:
        num, unit = match.groups()
        unit_normalized = normalize_unit(unit)
        multiplier = MEMORY_UNITS.get(unit_normalized)
        if multiplier is not None:
            return int(float(num) * multiplier)

    # Try parsing as raw bytes if no unit matches
    try:
        result = int(float(str_val))
        logger.debug("Parsed memory value %r as raw bytes: %d", value, result)
        return result
    except ValueError:
        logger.warning("Could not parse memory value: %r", value)
        return 0


def parse_extended_resource_value(resource_name: str, value: Any) -> int:
    """Parse a resource Kubernetes has no unit convention for.

    Extended resources (`nvidia.com/gpu` and the like) are counts, but a values file may
    still spell one with a memory or millicore suffix, so both are accepted before
    falling back to a plain number.
    """
    str_val = str(value).strip()

    match = MEMORY_REGEX.match(str_val)
    if match:
        num, unit = match.groups()
        multiplier = MEMORY_UNITS.get(normalize_unit(unit))
        if multiplier:
            return int(float(num) * multiplier)

    match = CPU_REGEX.match(str_val)
    if match:
        num, unit = match.groups()
        if unit == "m":
            return int(float(num))

    try:
        if isinstance(value, (int, float)):
            return int(value)
        return int(float(str_val))
    except ValueError:
        logger.warning("Could not parse resource %r value: %r", resource_name, value)
        return 0


def parse_resource_value(resource_name: str, value: Any) -> int:
    """Parse any resource value to a normalized integer."""
    if value is None:
        return 0

    if resource_name == ResourceName.CPU:
        return parse_cpu(value)
    if resource_name in (ResourceName.MEMORY, ResourceName.EPHEMERAL_STORAGE):
        return parse_memory(value)

    return parse_extended_resource_value(resource_name, value)


def parse_threshold(value: str) -> ParsedThreshold:
    """Parse threshold string 'resource=value'.

    A warning is attached when the value is unit-less, which Kubernetes reads
    as bytes.

    Examples:
        cpu=2000m
        memory=1G      # 1 Gigabyte
        memory=1Gi     # 1 Gibibyte
        memory=2       # 2 bytes - will return a warning!
    """
    if "=" not in value:
        raise ValueError(
            f"Invalid threshold format: {value}. Expected 'resource=value'"
        )

    name, val = value.split("=", 1)
    name = name.strip()
    val_str = val.strip()
    warning: str | None = None

    # Validation for memory-like resources: warn on bare numbers (interpreted as bytes)
    if name in (ResourceName.MEMORY, ResourceName.EPHEMERAL_STORAGE):
        if is_bare_number(val_str):
            # It's just a number like "2" or "1048576" - means bytes
            byte_val = int(float(val_str))
            mib_val = byte_val / (1024 * 1024)
            if byte_val > 0:
                warning = (
                    f"WARNING: {name} threshold '{val_str}' is interpreted as"
                    f" {byte_val} bytes ({mib_val:.10f} MiB). Did you mean"
                    f" '{name}={val_str}Gi' or '{name}={val_str}Mi'?"
                )

    parsed_val = parse_resource_value(name, val_str)
    return ParsedThreshold(resource=name, value=parsed_val, warning=warning)


def load_quota_thresholds(values_path: str) -> QuotaThresholds:
    """Read resourceQuotas.scalable from a Helm values file.

    Maps Kubernetes ResourceQuota hard keys (e.g. 'requests.cpu', 'limits.memory') to
    the resource names used by this tool. 'pods' is ignored.
    """
    with open(values_path, encoding="utf-8") as f:
        values = yaml.safe_load(f)

    rq = (values or {}).get("resourceQuotas", {}).get("scalable", {})
    enabled = bool(rq.get("enabled", False))
    hard: dict[str, Any] = rq.get("hard") or {}

    request_thresholds: dict[str, int] = {}
    limit_thresholds: dict[str, int] = {}

    for key, value in hard.items():
        if key.startswith("requests."):
            resource = key[len("requests.") :]
            if resource in (
                ResourceName.CPU,
                ResourceName.MEMORY,
                ResourceName.EPHEMERAL_STORAGE,
            ):
                request_thresholds[resource] = parse_resource_value(resource, value)
        elif key.startswith("limits."):
            resource = key[len("limits.") :]
            if resource in (
                ResourceName.CPU,
                ResourceName.MEMORY,
                ResourceName.EPHEMERAL_STORAGE,
            ):
                limit_thresholds[resource] = parse_resource_value(resource, value)

    return QuotaThresholds(
        requests=request_thresholds,
        limits=limit_thresholds,
        enabled=enabled,
    )


def extract_resources(
    resource_spec: dict[str, Any] | None,
) -> ContainerResources:
    """Extract requests and limits from resource spec.

    If a limit is set but no request, request defaults to limit (Kubernetes behavior).
    """
    if not resource_spec:
        return ContainerResources(
            requests=ResourceQuantity(), limits=ResourceQuantity()
        )

    requests_spec = resource_spec.get("requests") or {}
    limits_spec = resource_spec.get("limits") or {}

    # Parse limits first
    lim_resources: dict[str, int] = {}
    for name, value in limits_spec.items():
        if value:
            lim_resources[name] = parse_resource_value(name, value)

    # Parse requests
    req_resources: dict[str, int] = {}
    for name, value in requests_spec.items():
        if value:
            req_resources[name] = parse_resource_value(name, value)

    # K8s behavior: if limit is set but request is not, request = limit
    for resource_name, limit_value in lim_resources.items():
        if resource_name not in req_resources:
            req_resources[resource_name] = limit_value

    return ContainerResources(
        requests=ResourceQuantity(req_resources),
        limits=ResourceQuantity(lim_resources),
    )
