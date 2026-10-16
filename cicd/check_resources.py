#!/usr/bin/env python3
"""Kubernetes Resource Calculator.

Calculates CPU, memory, and any extended resources from Kubernetes manifests. Unified
threshold handling for all resource types. Properly handles SI units (G, M, K) and
binary units (Gi, Mi, Ki). Warns when memory/storage thresholds lack units (interpreted
as bytes per K8s spec).
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, TextIO

import yaml

from check_resources_model import (
    REPLICATED_WORKLOADS,
    WORKLOADS_WITH_PODS,
    CalculatorReport,
    Container,
    ReplicaCount,
    ResourceQuantity,
    Workload,
    WorkloadKind,
    extract_resources,
    load_quota_thresholds,
    parse_threshold,
    read_replica_count,
)

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Calculator
# -----------------------------------------------------------------------------
class ManifestResourceCalculator:
    """Resource calculator reading directly from manifests."""

    def __init__(
        self,
        node_count: int = 1,
        exclude_ephemeral: bool = False,
        priority_class_filter: str | None = None,
    ):
        self.node_count = max(1, node_count)
        self.exclude_ephemeral = exclude_ephemeral
        self.priority_class_filter = priority_class_filter

    def extract_replica_count(self, doc: dict[str, Any]) -> ReplicaCount:
        """Extract replica count directly from manifest fields."""
        kind = doc.get("kind", "")
        spec = doc.get("spec") or {}

        if kind in REPLICATED_WORKLOADS:
            return read_replica_count(spec.get("replicas"), "spec.replicas")

        if kind == WorkloadKind.JOB:
            return read_replica_count(spec.get("parallelism"), "spec.parallelism")

        if kind == WorkloadKind.CRON_JOB:
            job_spec = (spec.get("jobTemplate") or {}).get("spec") or {}
            return read_replica_count(
                job_spec.get("parallelism"), "spec.jobTemplate.spec.parallelism"
            )

        if kind == WorkloadKind.DAEMON_SET:
            return ReplicaCount(
                count=self.node_count,
                source=f"spec.nodes ({self.node_count} nodes)",
                scales_with_nodes=True,
            )

        return ReplicaCount(count=1, source="unknown")

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
            pod_resources = extract_resources(pod_level_resources)
            containers.append(
                Container(
                    "pod-level", "pod", pod_resources.requests, pod_resources.limits
                )
            )
            return containers

        # Init containers
        for c_spec in pod_spec.get("initContainers", []):
            if not c_spec:
                continue
            name = str(c_spec.get("name", "unnamed"))
            resources = extract_resources(c_spec.get("resources"))
            containers.append(
                Container(name, "init", resources.requests, resources.limits)
            )

        # App containers
        for c_spec in pod_spec.get("containers", []):
            if not c_spec:
                continue
            name = str(c_spec.get("name", "unnamed"))
            resources = extract_resources(c_spec.get("resources"))
            containers.append(
                Container(name, "app", resources.requests, resources.limits)
            )

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

        if self.priority_class_filter:
            _spec = doc.get("spec") or {}
            if kind == WorkloadKind.CRON_JOB:
                _pod_spec = (
                    _spec.get("jobTemplate", {})
                    .get("spec", {})
                    .get("template", {})
                    .get("spec")
                    or {}
                )
            elif kind == WorkloadKind.POD:
                _pod_spec = _spec
            else:
                _pod_spec = _spec.get("template", {}).get("spec") or {}
            priority_class_name = _pod_spec.get("priorityClassName", "")
            if not fnmatch(priority_class_name, self.priority_class_filter):
                return None

        replica_count = self.extract_replica_count(doc)
        containers = self.extract_containers(doc)

        if not containers:
            logger.debug("Workload %s/%s has no containers, skipping", namespace, name)
            return None

        return Workload(
            kind=kind,
            name=name,
            namespace=namespace,
            replicas=replica_count.count,
            replica_source=replica_count.source,
            containers=containers,
            is_daemonset=replica_count.scales_with_nodes,
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
            except (
                AttributeError,
                KeyError,
                TypeError,
                ValueError,
                yaml.YAMLError,
            ) as e:
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
            return f"{millicores}m ({millicores / 1000:.2f} cores)"
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
        if resource_name in ("memory", "ephemeral-storage"):
            return ReportFormatter.format_memory(value)
        return ReportFormatter.format_generic(value)

    @staticmethod
    def calculate_multiplier(request: int, limit: int) -> str:
        """Calculate multiplier factor (limit/request).

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
        if ratio == int(ratio):
            return f"{int(ratio)}x"
        return f"{ratio:.2f}x"

    @classmethod
    def print_container_details(
        cls, container: Container, replicas: int, resource_types: list[str]
    ) -> None:
        """Print one container's share of its workload's resources."""
        print(f"      {container.name:<15} ({container.container_type})")
        for res in resource_types:
            req_val = container.requests.get(res) * replicas
            lim_val = container.limits.get(res) * replicas
            if req_val <= 0 and lim_val <= 0:
                continue
            mult = cls.calculate_multiplier(req_val, lim_val)
            print(
                f"        {res:<18}"
                f" Req: {cls.format_resource(res, req_val):<20}"
                f" Lim: {cls.format_resource(res, lim_val):<20} [{mult}]"
            )

    @classmethod
    def print_workload_details(
        cls, report: CalculatorReport, resource_types: list[str]
    ) -> None:
        """Print each workload's totals, and its containers when it has several."""
        print("\nWorkload Details")
        print("=" * 80)

        for wl in report.workloads:
            ds_marker = "[DS]" if wl.is_daemonset else ""
            header = f"{wl.kind}/{wl.namespace}/{wl.name}"
            print(
                f"\n{header} (Source: {wl.replica_source},"
                f" Replicas: {wl.replicas}) {ds_marker}"
            )

            wl_req = ResourceQuantity()
            wl_lim = ResourceQuantity()
            for c in wl.containers:
                wl_req = wl_req + (c.requests * wl.replicas)
                wl_lim = wl_lim + (c.limits * wl.replicas)

            for res in resource_types:
                req_val = wl_req.get(res)
                lim_val = wl_lim.get(res)
                if req_val <= 0 and lim_val <= 0:
                    continue
                mult = cls.calculate_multiplier(req_val, lim_val)
                print(
                    f"  {res:<20} Req: {cls.format_resource(res, req_val):<25} "
                    f"Lim: {cls.format_resource(res, lim_val):<25} [{mult}]"
                )

            if len(wl.containers) > 1:
                print("    Containers:")
                for c in wl.containers:
                    cls.print_container_details(c, wl.replicas, resource_types)

    @classmethod
    def print_report(cls, report: CalculatorReport, detailed: bool = False) -> None:
        """Print formatted report showing requests, limits, and multiplier."""
        resource_types = sorted(report.get_all_resource_types())

        res_width = max(max((len(r) for r in resource_types), default=10), 15)
        val_width = 30
        mult_width = 8
        total_width = res_width + 2 + val_width + 2 + val_width + 2 + mult_width

        if detailed and report.workloads:
            cls.print_workload_details(report, resource_types)

        # Summary table with requests, limits and multiplier
        print("\n" + "=" * total_width)
        print(f"CLUSTER TOTALS (Node count: {report.node_count})")
        print("=" * total_width)
        print(
            f"{'Resource':<{res_width}}  {'Requests':<{val_width}}"
            f"  {'Limits':<{val_width}}  {'Factor':<{mult_width}}"
        )
        print("-" * total_width)

        for res in resource_types:
            req_val = report.total_requests.get(res)
            lim_val = report.total_limits.get(res)
            req_str = cls.format_resource(res, req_val)
            lim_str = cls.format_resource(res, lim_val)
            mult_str = cls.calculate_multiplier(req_val, lim_val)
            print(
                f"{res:<{res_width}}  {req_str:<{val_width}}"
                f"  {lim_str:<{val_width}}  {mult_str:<{mult_width}}"
            )

        print("=" * total_width)
        print("\nFactor = Limits are N times the Requests (Limit ÷ Request)")

        daemonsets = [w for w in report.workloads if w.is_daemonset]
        if daemonsets:
            print(
                f"\nNote: {len(daemonsets)} DaemonSet(s) calculated using"
                f" {report.node_count} node(s)"
            )


# -----------------------------------------------------------------------------
# Threshold Checking
# -----------------------------------------------------------------------------
def check_thresholds(
    report: CalculatorReport,
    thresholds: dict[str, int],
    threshold_type: str = "request",
) -> bool:
    """Check if calculated resources exceed thresholds.

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
            actual = ReportFormatter.format_resource(resource_name, actual_value)
            allowed = ReportFormatter.format_resource(resource_name, max_value)
            print(
                f"\n✅ {resource_name} {type_label}: {actual} / {allowed}"
                f" ({usage_pct:.1f}%)"
            )

    return exceeded


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ThresholdSet:
    """Thresholds parsed from the command line, with anything worth warning about."""

    thresholds: dict[str, int]
    warnings: list[str]


def build_thresholds(threshold_args: list[str], threshold_type: str) -> ThresholdSet:
    """Build thresholds dict from CLI arguments."""
    thresholds: dict[str, int] = {}
    warnings: list[str] = []

    for th in threshold_args:
        try:
            parsed = parse_threshold(th)
            thresholds[parsed.resource] = parsed.value
            if parsed.warning:
                warnings.append(parsed.warning)
        except ValueError as e:
            raise ValueError(f"{threshold_type} threshold error: {e}") from e

    return ThresholdSet(thresholds=thresholds, warnings=warnings)


EXAMPLES = """
Examples:
  helm template . | python3 %(prog)s --nodes 3

  # Threshold for REQUESTS
  helm template . | python3 %(prog)s \\
      --threshold-request cpu=2000m --threshold-request memory=8Gi

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
"""


def build_argument_parser() -> argparse.ArgumentParser:
    """Define the command line."""
    parser = argparse.ArgumentParser(
        description="Calculate K8s resources from manifests with threshold checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES,
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=None,
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
    parser.add_argument(
        "--filter-priority-class",
        "-fpc",
        metavar="GLOB",
        default=None,
        help="Only count workloads whose pod priorityClassName matches this glob pattern "
        "(e.g. '*-scalable'). Workloads without a priorityClassName are excluded.",
    )
    parser.add_argument(
        "--quota-values",
        "-qv",
        metavar="FILE",
        default=None,
        help="Helm values YAML file from which to read resourceQuotas.scalable.hard as "
        "thresholds. If resourceQuotas.scalable.enabled is false and no explicit "
        "--threshold-* args are given, the check is skipped (exit 0).",
    )
    return parser


@dataclass(frozen=True)
class ResolvedThresholds:
    """What a run will check against, and why it might check nothing at all."""

    requests: dict[str, int]
    limits: dict[str, int]
    warnings: list[str]
    skip_reason: str | None = None


def resolve_thresholds(args: argparse.Namespace) -> ResolvedThresholds:
    """Combine the --threshold-* arguments with a Helm values file, if given.

    Raises ValueError when an argument or the values file cannot be read; the caller
    turns that into a message and a non-zero exit.
    """
    request_set = build_thresholds(args.threshold_request, "request")
    limit_set = build_thresholds(args.threshold_limit, "limit")

    requests = dict(request_set.thresholds)
    limits = dict(limit_set.thresholds)
    warnings = [*request_set.warnings, *limit_set.warnings]

    if not args.quota_values:
        return ResolvedThresholds(requests=requests, limits=limits, warnings=warnings)

    try:
        quota = load_quota_thresholds(args.quota_values)
    except (OSError, KeyError, TypeError, yaml.YAMLError) as e:
        raise ValueError(
            f"Error reading quota values from {args.quota_values}: {e}"
        ) from e

    if quota.enabled:
        requests.update(quota.requests)
        limits.update(quota.limits)
        return ResolvedThresholds(requests=requests, limits=limits, warnings=warnings)

    # Quotas are switched off. Explicit thresholds still apply; without any,
    # there is nothing left to check.
    skip_reason = None
    if not requests and not limits:
        skip_reason = (
            f"Note: resourceQuotas.scalable.enabled is false in"
            f" {args.quota_values} — skipping quota check."
        )
    return ResolvedThresholds(
        requests=requests, limits=limits, warnings=warnings, skip_reason=skip_reason
    )


def read_report(args: argparse.Namespace) -> CalculatorReport:
    """Calculate the report from the manifest file, or from stdin."""
    calculator = ManifestResourceCalculator(
        node_count=args.nodes,
        exclude_ephemeral=args.exclude_ephemeral,
        priority_class_filter=args.filter_priority_class,
    )
    if args.file:
        with args.file.open(encoding="utf-8") as manifests:
            return calculator.calculate(manifests)
    return calculator.calculate(sys.stdin)


def report_and_check(args: argparse.Namespace, resolved: ResolvedThresholds) -> int:
    """Print the report and return the exit code the thresholds imply."""
    report = read_report(args)

    if not report.workloads:
        if args.filter_priority_class:
            print(
                "No workloads found matching priority class filter"
                f" '{args.filter_priority_class}'",
                file=sys.stderr,
            )
            return 0
        print("No workloads found", file=sys.stderr)
        return 1

    ReportFormatter.print_report(report, detailed=args.detail)

    if resolved.requests or resolved.limits:
        print()  # Empty line separator

    exceeded = False
    if resolved.requests:
        if check_thresholds(report, resolved.requests, threshold_type="request"):
            exceeded = True
    if resolved.limits:
        if check_thresholds(report, resolved.limits, threshold_type="limit"):
            exceeded = True

    return 1 if exceeded else 0


def main() -> int:
    """Entry point."""
    args = build_argument_parser().parse_args()

    if args.nodes < 1:
        print("Error: Node count must be at least 1", file=sys.stderr)
        return 1

    try:
        resolved = resolve_thresholds(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if resolved.skip_reason:
        print(resolved.skip_reason)
        sys.stdin.read()
        return 0

    # Print any warnings about unit-less memory values before proceeding
    for warning in resolved.warnings:
        print(warning, file=sys.stderr)

    try:
        return report_and_check(args, resolved)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
