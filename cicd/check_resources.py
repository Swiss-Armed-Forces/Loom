#!/usr/bin/env python3
"""
Kubernetes Resource Calculator.

Calculates CPU, memory, and any extended resources from Kubernetes manifests.
Unified threshold handling for all resource types.
Properly handles SI units (G, M, K) and binary units (Gi, Mi, Ki).
Warns when memory/storage thresholds lack units (interpreted as bytes per K8s spec).
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TextIO

import yaml

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
class ResourceName:
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
    """Normalize unit string to match MEMORY_UNITS keys (e.g., 'ki' -> 'Ki', 'k' -> 'K')."""
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
    """Parse memory value to bytes. Raw numbers are treated as bytes."""
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


def parse_resource_value(resource_name: str, value: Any) -> int:
    """
    Parse any resource value to a normalized integer.
    """
    if value is None:
        return 0

    if resource_name == ResourceName.CPU:
        return parse_cpu(value)
    elif resource_name in (ResourceName.MEMORY, ResourceName.EPHEMERAL_STORAGE):
        return parse_memory(value)

    str_val = str(value).strip()

    # Try memory-style units for extended resources
    match = MEMORY_REGEX.match(str_val)
    if match:
        num, unit = match.groups()
        unit_normalized = normalize_unit(unit)
        multiplier = MEMORY_UNITS.get(unit_normalized)
        if multiplier:
            return int(float(num) * multiplier)

    # Try millicore-style (e.g., "500m")
    match = CPU_REGEX.match(str_val)
    if match:
        num, unit = match.groups()
        if unit == "m":
            return int(float(num))

    # Raw number
    try:
        if isinstance(value, (int, float)):
            return int(value)
        return int(float(str_val))
    except ValueError:
        logger.warning("Could not parse resource %r value: %r", resource_name, value)
        return 0


def parse_threshold(value: str) -> tuple[str, int, str | None]:
    """
    Parse threshold string 'resource=value'.

    Returns:
        Tuple of (resource_name, parsed_value, warning_message)
        warning_message is None if no warning, or a string to display

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
                    f"WARNING: {name} threshold '{val_str}' is interpreted as {byte_val} bytes "
                    f"({mib_val:.10f} MiB). Did you mean '{name}={val_str}Gi' or '{name}={val_str}Mi'?"
                )

    parsed_val = parse_resource_value(name, val_str)
    return name, parsed_val, warning


def extract_resources(
    resource_spec: dict[str, Any] | None,
) -> tuple[ResourceQuantity, ResourceQuantity]:
    """
    Extract requests and limits from resource spec.
    If a limit is set but no request, request defaults to limit (Kubernetes behavior).
    """
    if not resource_spec:
        return ResourceQuantity(), ResourceQuantity()

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

    return ResourceQuantity(req_resources), ResourceQuantity(lim_resources)


# -----------------------------------------------------------------------------
# Calculator
# -----------------------------------------------------------------------------
class ManifestResourceCalculator:
    """Resource calculator reading directly from manifests."""

    def __init__(self, node_count: int = 1, exclude_ephemeral: bool = False):
        self.node_count = max(1, node_count)
        self.exclude_ephemeral = exclude_ephemeral

    def extract_replica_count(self, doc: dict[str, Any]) -> tuple[int, str, bool]:
        """Extract replica count directly from manifest fields."""
        kind = doc.get("kind", "")
        spec = doc.get("spec") or {}

        if kind in REPLICATED_WORKLOADS:
            replicas = spec.get("replicas")
            if (
                replicas is not None
                and isinstance(replicas, (int, float, str))
                and not isinstance(replicas, bool)
            ):
                count = safe_int(replicas)
                if count >= 0:
                    return count, "spec.replicas", False
            return 1, "spec.replicas (default)", False

        elif kind == WorkloadKind.JOB:
            parallelism = spec.get("parallelism")
            if (
                parallelism is not None
                and isinstance(parallelism, (int, float, str))
                and not isinstance(parallelism, bool)
            ):
                count = safe_int(parallelism)
                if count >= 0:
                    return count, "spec.parallelism", False
            return 1, "spec.parallelism (default)", False

        elif kind == WorkloadKind.CRON_JOB:
            job_template = spec.get("jobTemplate") or {}
            job_spec = job_template.get("spec") or {}
            parallelism = job_spec.get("parallelism")
            if (
                parallelism is not None
                and isinstance(parallelism, (int, float, str))
                and not isinstance(parallelism, bool)
            ):
                count = safe_int(parallelism)
                if count >= 0:
                    return count, "spec.jobTemplate.spec.parallelism", False
            return 1, "spec.jobTemplate.spec.parallelism (default)", False

        elif kind == WorkloadKind.DAEMON_SET:
            return self.node_count, f"spec.nodes ({self.node_count} nodes)", True

        return 1, "unknown", False

    def extract_containers(self, doc: dict[str, Any]) -> list[Container]:
        """Extract all containers from pod template.

        Supports Pod-level resource specification:
        - If spec.resources is defined at pod level, use only those resources
        - Otherwise, sum resources from all containers individually
        """
        kind = doc.get("kind", "")
        spec = doc.get("spec") or {}

        if kind == WorkloadKind.CRON_JOB:
            template = spec.get("jobTemplate", {}).get("spec", {}).get("template", {})
            pod_spec = template.get("spec") or {}
        elif kind == WorkloadKind.POD:
            # For standalone Pods, the spec is directly under spec
            pod_spec = spec
        elif kind in WORKLOADS_WITH_PODS:
            pod_spec = spec.get("template", {}).get("spec") or {}
        else:
            return []

        containers: list[Container] = []

        # Check for Pod-level resources
        pod_level_resources = pod_spec.get("resources")
        if pod_level_resources:
            # Pod-level resources defined - use only these resources
            req, lim = extract_resources(pod_level_resources)
            containers.append(Container("pod-level", "pod", req, lim))
            return containers

        # Init containers
        for c_spec in pod_spec.get("initContainers", []):
            if not c_spec:
                continue
            name = str(c_spec.get("name", "unnamed"))
            resources = c_spec.get("resources")
            req, lim = extract_resources(resources)
            containers.append(Container(name, "init", req, lim))

        # App containers
        for c_spec in pod_spec.get("containers", []):
            if not c_spec:
                continue
            name = str(c_spec.get("name", "unnamed"))
            resources = c_spec.get("resources")
            req, lim = extract_resources(resources)
            containers.append(Container(name, "app", req, lim))

        return containers

    def parse_workload(self, doc: dict[str, Any]) -> Workload | None:
        """Parse a single YAML document into a Workload."""
        if not isinstance(doc, dict):
            logger.warning("Skipping non-dictionary document: %r", type(doc))
            return None

        kind = doc.get("kind", "")
        if kind not in WORKLOADS_WITH_PODS:
            return None

        # Skip ephemeral workloads if exclude_ephemeral is enabled
        if self.exclude_ephemeral and kind in (WorkloadKind.JOB, WorkloadKind.CRON_JOB):
            return None

        # Validate required fields
        metadata = doc.get("metadata")
        if not isinstance(metadata, dict):
            logger.warning("Workload %r missing valid metadata", kind)
            metadata = {}

        name = str(metadata.get("name", "unknown"))
        namespace = str(metadata.get("namespace", "default"))

        replicas, source, is_daemonset = self.extract_replica_count(doc)
        containers = self.extract_containers(doc)

        if not containers:
            logger.debug("Workload %s/%s has no containers, skipping", namespace, name)
            return None

        return Workload(
            kind=kind,
            name=name,
            namespace=namespace,
            replicas=replicas,
            replica_source=source,
            containers=containers,
            is_daemonset=is_daemonset,
        )

    def calculate(self, yaml_stream: TextIO) -> CalculatorReport:
        """Calculate totals from YAML stream."""
        total_requests = ResourceQuantity()
        total_limits = ResourceQuantity()
        workloads: list[Workload] = []

        try:
            documents = yaml.safe_load_all(yaml_stream)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}") from e

        doc_count = 0
        for doc in documents:
            doc_count += 1
            if not doc:
                continue

            try:
                workload = self.parse_workload(doc)
                if workload:
                    workloads.append(workload)

                    for container in workload.containers:
                        scaled_req = container.requests * workload.replicas
                        scaled_lim = container.limits * workload.replicas

                        total_requests = total_requests + scaled_req
                        total_limits = total_limits + scaled_lim
            except Exception as e:
                logger.warning("Error parsing document %d: %s", doc_count, e)
                continue

        return CalculatorReport(
            total_requests=total_requests,
            total_limits=total_limits,
            workloads=workloads,
            node_count=self.node_count,
        )


# -----------------------------------------------------------------------------
# Output Formatting
# -----------------------------------------------------------------------------
class ReportFormatter:
    """Report formatting utilities."""

    @staticmethod
    def format_cpu(millicores: int) -> str:
        if millicores == 0:
            return "-"
        if millicores >= 1000:
            return f"{millicores}m ({millicores/1000:.2f} cores)"
        return f"{millicores}m"

    @staticmethod
    def format_memory(bytes_val: int) -> str:
        """Format byte value to human-readable string (KiB, MiB, GiB, TiB)."""
        if bytes_val == 0:
            return "-"

        # Use IEC binary units (KiB, MiB, GiB, TiB)
        units = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB"]
        unit_index = 0
        value = float(bytes_val)

        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(value)} bytes"

        # Format with appropriate precision
        if value == int(value):
            return f"{int(value)} {units[unit_index]}"
        return f"{value:.2f} {units[unit_index]}"

    @staticmethod
    def format_generic(value: int) -> str:
        if value == 0:
            return "-"
        return str(value)

    @staticmethod
    def format_resource(resource_name: str, value: int) -> str:
        """Format any resource value appropriately."""
        if resource_name == "cpu":
            return ReportFormatter.format_cpu(value)
        elif resource_name in ("memory", "ephemeral-storage"):
            return ReportFormatter.format_memory(value)
        else:
            return ReportFormatter.format_generic(value)

    @staticmethod
    def calculate_multiplier(request: int, limit: int) -> str:
        """
        Calculate multiplier factor (limit/request).
        Shows how many times limits exceed requests.
        """
        if request == 0:
            if limit == 0:
                return "-"
            return "inf"

        if limit == 0:
            return "0x"

        ratio = limit / request
        if ratio == 1.0:
            return "1x"
        elif ratio == int(ratio):
            return f"{int(ratio)}x"
        else:
            return f"{ratio:.2f}x"

    @classmethod
    def print_report(cls, report: CalculatorReport, detailed: bool = False) -> None:
        """Print formatted report showing requests, limits, and multiplier."""
        resource_types = sorted(report.get_all_resource_types())

        # Calculate column widths
        max_res_len = max((len(r) for r in resource_types), default=10)
        res_width = max(max_res_len, 15)
        val_width = 30
        mult_width = 8

        total_width = res_width + 2 + val_width + 2 + val_width + 2 + mult_width

        if detailed and report.workloads:
            print(f"\n{'Workload Details'}")
            print("=" * 80)

            for wl in report.workloads:
                ds_marker = "[DS]" if wl.is_daemonset else ""
                header = f"{wl.kind}/{wl.namespace}/{wl.name}"
                print(
                    f"\n{header} (Source: {wl.replica_source}, Replicas: {wl.replicas}) {ds_marker}"
                )

                # Aggregate per workload
                wl_req = ResourceQuantity()
                wl_lim = ResourceQuantity()
                for c in wl.containers:
                    wl_req = wl_req + (c.requests * wl.replicas)
                    wl_lim = wl_lim + (c.limits * wl.replicas)

                # Show workload totals with multiplier
                for res in resource_types:
                    req_val = wl_req.get(res)
                    lim_val = wl_lim.get(res)
                    if req_val > 0 or lim_val > 0:
                        mult = cls.calculate_multiplier(req_val, lim_val)
                        print(
                            f"  {res:<20} Req: {cls.format_resource(res, req_val):<25} "
                            f"Lim: {cls.format_resource(res, lim_val):<25} [{mult}]"
                        )

                # Per-container breakdown
                if len(wl.containers) > 1:
                    print(f"    Containers:")
                    for c in wl.containers:
                        print(f"      {c.name:<15} ({c.container_type})")
                        for res in resource_types:
                            req_val = c.requests.get(res) * wl.replicas
                            lim_val = c.limits.get(res) * wl.replicas
                            if req_val > 0 or lim_val > 0:
                                mult = cls.calculate_multiplier(req_val, lim_val)
                                print(
                                    f"        {res:<18} Req: {cls.format_resource(res, req_val):<20} "
                                    f"Lim: {cls.format_resource(res, lim_val):<20} [{mult}]"
                                )

        # Summary table with requests, limits and multiplier
        print("\n" + "=" * total_width)
        print(f"CLUSTER TOTALS (Node count: {report.node_count})")
        print("=" * total_width)
        print(
            f"{'Resource':<{res_width}}  {'Requests':<{val_width}}  {'Limits':<{val_width}}  {'Factor':<{mult_width}}"
        )
        print("-" * total_width)

        for res in resource_types:
            req_val = report.total_requests.get(res)
            lim_val = report.total_limits.get(res)
            req_str = cls.format_resource(res, req_val)
            lim_str = cls.format_resource(res, lim_val)
            mult_str = cls.calculate_multiplier(req_val, lim_val)
            print(
                f"{res:<{res_width}}  {req_str:<{val_width}}  {lim_str:<{val_width}}  {mult_str:<{mult_width}}"
            )

        print("=" * total_width)
        print("\nFactor = Limits are N times the Requests (Limit ÷ Request)")

        daemonsets = [w for w in report.workloads if w.is_daemonset]
        if daemonsets:
            print(
                f"\nNote: {len(daemonsets)} DaemonSet(s) calculated using {report.node_count} node(s)"
            )


# -----------------------------------------------------------------------------
# Threshold Checking
# -----------------------------------------------------------------------------
def check_thresholds(
    report: CalculatorReport,
    thresholds: dict[str, int],
    threshold_type: str = "request",
) -> bool:
    """
    Check if calculated resources exceed thresholds.

    Args:
        report: CalculatorReport with totals
        thresholds: Dict of resource_name -> max_value
        threshold_type: "request" or "limit" - which value to check

    Returns:
        True if any threshold was exceeded
    """
    exceeded = False

    for resource_name, max_value in thresholds.items():
        if max_value <= 0:
            continue

        # Get the appropriate value based on threshold type
        if threshold_type == "limit":
            actual_value = report.total_limits.get(resource_name)
            type_label = "LIMIT"
        else:
            actual_value = report.total_requests.get(resource_name)
            type_label = "REQUEST"

        if actual_value > max_value:
            usage_pct = (actual_value / max_value) * 100 if max_value > 0 else 0
            print(
                f"\n❌ {type_label} THRESHOLD EXCEEDED: {resource_name}",
                file=sys.stderr,
            )
            print(
                f"   Maximum: {ReportFormatter.format_resource(resource_name, max_value)}",
                file=sys.stderr,
            )
            print(
                f"   Used:    {ReportFormatter.format_resource(resource_name, actual_value)}",
                file=sys.stderr,
            )
            print(f"   Usage:   {usage_pct:.1f}%", file=sys.stderr)
            exceeded = True
        else:
            # Only show status if threshold was specified
            usage_pct = (actual_value / max_value) * 100 if max_value > 0 else 0
            print(
                f"\n✅ {resource_name} {type_label}: {ReportFormatter.format_resource(resource_name, actual_value)} / {ReportFormatter.format_resource(resource_name, max_value)} ({usage_pct:.1f}%)"
            )

    return exceeded


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_thresholds(
    threshold_args: list[str], threshold_type: str
) -> tuple[dict[str, int], list[str]]:
    """Build thresholds dict from CLI arguments."""
    thresholds: dict[str, int] = {}
    warnings: list[str] = []

    for th in threshold_args:
        try:
            name, value, warning = parse_threshold(th)
            thresholds[name] = value
            if warning:
                warnings.append(warning)
        except ValueError as e:
            raise ValueError(f"{threshold_type} threshold error: {e}") from e

    return thresholds, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate K8s resources from manifests with threshold checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  helm template . | python3 %(prog)s --nodes 3

  # Threshold for REQUESTS
  helm template . | python3 %(prog)s --threshold-request cpu=2000m --threshold-request memory=8Gi

  # Threshold for LIMITS
  helm template . | python3 %(prog)s --threshold-limit cpu=4000m --threshold-limit memory=16Gi

  # Check both requests and limits
  helm template . | python3 %(prog)s \\
      --threshold-request cpu=2000m --threshold-request memory=8Gi \\
      --threshold-limit cpu=4000m --threshold-limit memory=16Gi

  # Check from file, excluding ephemeral workloads (Job, CronJob)
  python3 %(prog)s --file manifest.yaml --exclude-ephemeral --threshold-request cpu=2000m

  # Extended resources work the same way
  helm template . | python3 %(prog)s --threshold-request nvidia.com/gpu=2
        """,
    )
    parser.add_argument(
        "--file",
        "-f",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="YAML file (default: stdin)",
    )
    parser.add_argument(
        "--detail",
        "-d",
        action="store_true",
        help="Show per-workload details with requests and limits",
    )
    parser.add_argument(
        "--nodes",
        "-n",
        type=int,
        default=1,
        help="Number of cluster nodes for DaemonSet calculations (default: 1)",
    )
    parser.add_argument(
        "--threshold-request",
        "-tr",
        action="append",
        default=[],
        metavar="RESOURCE=VALUE",
        help="Resource REQUEST threshold (e.g., 'cpu=2000m', 'memory=4Gi'). "
        "Checks if resource REQUESTS exceed this value.",
    )
    parser.add_argument(
        "--threshold-limit",
        "-tl",
        action="append",
        default=[],
        metavar="RESOURCE=VALUE",
        help="Resource LIMIT threshold (e.g., 'cpu=4000m', 'memory=8Gi'). "
        "Checks if resource LIMITS exceed this value.",
    )
    parser.add_argument(
        "--exclude-ephemeral",
        "-e",
        action="store_true",
        help="Exclude ephemeral workloads (Job, CronJob) from resource calculation.",
    )
    args = parser.parse_args()

    if args.nodes < 1:
        print("Error: Node count must be at least 1", file=sys.stderr)
        return 1

    # Build thresholds dictionaries
    request_thresholds: dict[str, int] = {}
    limit_thresholds: dict[str, int] = {}
    all_warnings: list[str] = []

    try:
        # --threshold-request thresholds
        thresholds, warnings = build_thresholds(args.threshold_request, "request")
        request_thresholds.update(thresholds)
        all_warnings.extend(warnings)

        # --threshold-limit thresholds
        thresholds, warnings = build_thresholds(args.threshold_limit, "limit")
        limit_thresholds.update(thresholds)
        all_warnings.extend(warnings)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Print any warnings about unit-less memory values before proceeding
    for warning in all_warnings:
        print(warning, file=sys.stderr)

    try:
        calculator = ManifestResourceCalculator(
            node_count=args.nodes, exclude_ephemeral=args.exclude_ephemeral
        )
        report = calculator.calculate(args.file)

        if not report.workloads:
            print("No workloads found", file=sys.stderr)
            return 1

        # Print the report
        ReportFormatter.print_report(report, detailed=args.detail)

        # Check thresholds if specified
        if request_thresholds or limit_thresholds:
            print()  # Empty line separator

        exceeded = False

        # Check request thresholds
        if request_thresholds:
            if check_thresholds(report, request_thresholds, threshold_type="request"):
                exceeded = True

        # Check limit thresholds
        if limit_thresholds:
            if check_thresholds(report, limit_thresholds, threshold_type="limit"):
                exceeded = True

        if exceeded:
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
