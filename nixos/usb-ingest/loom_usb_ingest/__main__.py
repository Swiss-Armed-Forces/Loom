"""Ingest one USB device into Loom.

Started per device by a udev rule, through `loom-usb-ingest@<kname>.service`.
See nixos/usb-ingest.nix for the wiring and Documentation/appliance.md for what
this means for the box's threat model.
"""

import argparse
import fcntl
import logging
import os
import pwd
import subprocess
import sys
import time
from typing import NamedTuple

from loom_usb_ingest import devices, filesystems, mounts, naming, report, transfer

logger = logging.getLogger("loom-usb-ingest")

# How long to wait for the key guard to make up its mind before ingesting
# anything. The key stick is present at boot and the guard arms within a couple
# of seconds, but a udev event can easily beat it -- and acting before the guard
# has spoken means acting without the authoritative exclusion.
GUARD_WAIT_S = 120
GUARD_POLL_S = 2

# Partitions appear a moment after the disk they belong to.
SETTLE_POLL_S = 1
SETTLE_ATTEMPTS = 15

MANIFEST_NAME = "_loom-usb.json"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="loom-usb-ingest")
    parser.add_argument("device", help="whole-disk device node, e.g. /dev/sdb")
    parser.add_argument("--bucket", default="loom-intake")
    parser.add_argument("--endpoint", default="https://s3.loom")
    parser.add_argument("--prefix", default="usb-crawled")
    parser.add_argument("--namespace", default="loom")
    parser.add_argument("--kubeconfig", default="/home/loom/.kube/config")
    parser.add_argument("--mount-root", default="/run/loom/usb")
    parser.add_argument("--state-dir", default="/run/loom/usb")
    parser.add_argument("--key-guard-state-dir", default="/run/loom/key-guard")
    parser.add_argument("--console-socket", default="/run/loom/tmux.sock")
    parser.add_argument(
        "--owner",
        default="loom",
        help="user the mounted files are presented as owned by",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the volumes, mount recipes and object keys, and change nothing",
    )
    return parser.parse_args(argv)


def wait_for_key_guard(state_dir: str) -> devices.KeyGuard:
    """Give the guard a chance to identify the key stick before we look at any."""
    deadline = time.monotonic() + GUARD_WAIT_S
    guard = devices.read_key_guard(state_dir)

    while time.monotonic() < deadline and not guard.authoritative:
        if guard.state in (devices.GuardState.DISARMED, devices.GuardState.IDLE):
            # A settled answer, just not an authoritative one -- a box booted on
            # the recovery passphrase never arms. Waiting longer changes nothing.
            break
        time.sleep(GUARD_POLL_S)
        guard = devices.read_key_guard(state_dir)

    return guard


class _Owner(NamedTuple):
    uid: int
    gid: int


def _resolve_owner(name: str) -> _Owner:
    """Look the operator account up rather than hardcoding its numbers.

    box.nix declares `loom` as an ordinary user without pinning a uid, so the
    value is only known on the running box.
    """
    try:
        entry = pwd.getpwnam(name)
    except KeyError:
        logger.warning("No user '%s'; mounting owned by root", name)
        return _Owner(0, 0)
    return _Owner(entry.pw_uid, entry.pw_gid)


def settle(device: str) -> devices.Disk:
    """Wait for udev, then for the partition table to actually show up."""
    try:
        subprocess.run(["udevadm", "settle"], check=False, timeout=60)
    except (subprocess.SubprocessError, OSError):
        pass

    disk = devices.inspect_disk(device)
    attempts = 0
    while not disk.volumes and attempts < SETTLE_ATTEMPTS:
        time.sleep(SETTLE_POLL_S)
        disk = devices.inspect_disk(device)
        attempts += 1
    return disk


def _volume_prefix(
    identity: naming.StickIdentity, index: int, volume: devices.Volume, total: int
) -> str:
    """Where one volume's contents land, relative to the ingest prefix."""
    component = identity.prefix_component
    if total <= 1:
        return component
    return f"{component}/{naming.volume_component(index, volume.label)}"


def describe(disk: devices.Disk, identity: naming.StickIdentity, supported) -> list[dict]:
    """The per-volume plan, used by --dry-run and by the manifest alike."""
    rows = []
    for index, volume in enumerate(disk.volumes, start=1):
        plan = filesystems.plan_mount(volume.fstype, 0, 0, supported)
        rows.append(
            {
                "device": volume.path,
                "fstype": volume.fstype,
                "label": volume.label,
                "size_bytes": volume.size,
                "policy": str(plan.policy),
                "mount_options": plan.option_string,
                "driver": plan.helper or plan.fstype or "auto",
                "reason": plan.reason,
                "prefix": _volume_prefix(
                    identity, index, volume, len(disk.volumes)
                ),
            }
        )
    return rows


def run(args: argparse.Namespace) -> int:
    # pylint: disable=too-many-locals,too-many-return-statements,too-many-branches
    disk = settle(args.device)
    if not disk.kernel_name:
        logger.error("%s is not a block device this box can read", args.device)
        return 1

    guard = wait_for_key_guard(args.key_guard_state_dir)
    verdict = devices.classify_disk(disk, guard, devices.protected_disks())

    if not verdict.ingest:
        logger.info("Not ingesting %s: it %s", disk.path, verdict.reason)
        return 0

    if not guard.authoritative:
        report.announce(
            f"[loom] Ingesting {disk.path} while the key guard is "
            f"'{guard.state}' -- the USB key is identified by partition label "
            "only. Check which stick is the key before removing any.",
            args.console_socket,
        )

    identity = naming.derive_identity(disk.properties, disk.size)
    owner = _resolve_owner(args.owner)
    supported = mounts.kernel_filesystems()
    plan_rows = describe(disk, identity, supported)

    if args.dry_run:
        _print_dry_run(disk, identity, plan_rows)
        return 0

    report.announce(
        f"[loom] Ingesting {disk.path} as '{identity.prefix_component}' "
        f"({len(disk.volumes)} volume(s)). It is mounted read-only.",
        args.console_socket,
    )

    config_dir = os.path.join(args.state_dir, "mc")
    os.makedirs(config_dir, mode=0o700, exist_ok=True)
    transfer.install_cluster_ca(config_dir, args.namespace, args.kubeconfig)

    try:
        transfer.configure_alias(args.endpoint, config_dir)
    except transfer.TransferError as error:
        logger.error("%s", error)
        return 1

    if not transfer.wait_for_cluster(
        args.endpoint, config_dir, transfer.CLUSTER_WAIT_TIMEOUT_S
    ):
        report.announce(
            f"[loom] {args.endpoint} never answered; {disk.path} was not ingested.",
            args.console_socket,
        )
        return 1

    report.warn_if_short_on_space(
        "/", sum(v.size for v in disk.volumes), args.console_socket
    )

    return _ingest_volumes(
        args, disk, identity, plan_rows, supported, config_dir, guard, owner
    )


def _ingest_volumes(
    args, disk, identity, plan_rows, supported, config_dir, guard, owner
) -> int:
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    total_objects = 0
    total_bytes = 0
    total_failures = 0

    for index, volume in enumerate(disk.volumes, start=1):
        prefix = _volume_prefix(identity, index, volume, len(disk.volumes))
        # Keyed by kernel name rather than by the stick's identity, so the
        # unit's ExecStopPost can unmount everything for this device without
        # having to re-derive the identity of a stick that may already be gone.
        mountpoint = os.path.join(args.mount_root, disk.kernel_name, f"p{index}")

        mounted = mounts.mount_volume(
            volume, mountpoint, owner.uid, owner.gid, supported
        )
        if isinstance(mounted, mounts.SkippedVolume):
            _annotate(plan_rows, volume.path, "skipped", mounted.reason)
            continue

        try:
            result = transfer.mirror(
                mounted.mountpoint,
                args.bucket,
                f"{args.prefix}/{prefix}",
                config_dir,
            )
        finally:
            mounts.unmount(mounted.mountpoint)

        total_objects += result.objects
        total_bytes += result.bytes_transferred
        total_failures += result.failures
        _annotate(
            plan_rows,
            volume.path,
            "ingested",
            f"{result.objects} objects, {result.failures} failures",
        )
        report.announce(
            f"[loom] {volume.path}: {result.objects} files uploaded "
            f"({result.bytes_transferred / (1024 ** 3):.1f} GiB).",
            args.console_socket,
        )

    status = "complete" if total_failures == 0 else "partial"
    manifest = {
        "status": status,
        "device": disk.path,
        "prefix": f"{args.prefix}/{identity.prefix_component}",
        "name": identity.name,
        "identifier": identity.identifier,
        "size_bytes": disk.size,
        "objects": total_objects,
        "bytes": total_bytes,
        "failures": total_failures,
        "key_guard_state": str(guard.state),
        "key_guard_authoritative": guard.authoritative,
        "udev": disk.properties,
        "volumes": plan_rows,
    }

    transfer.put_manifest(
        manifest,
        args.bucket,
        f"{args.prefix}/{identity.prefix_component}/{MANIFEST_NAME}",
        config_dir,
    )
    report.write_state(args.state_dir, manifest)

    report.announce(
        f"[loom] {disk.path} done: {total_objects} files, "
        f"{total_bytes / (1024 ** 3):.1f} GiB, {total_failures} failures. "
        "Safe to remove.",
        args.console_socket,
    )
    return 0 if total_failures == 0 else 1


def _annotate(rows: list[dict], device: str, outcome: str, detail: str) -> None:
    for row in rows:
        if row["device"] == device:
            row["outcome"] = outcome
            row["detail"] = detail


def _print_dry_run(disk, identity, rows) -> None:
    print(f"device:     {disk.path} ({disk.size} bytes)")
    print(f"identity:   {identity.prefix_component}")
    for row in rows:
        print(
            f"  {row['device']}  {row['fstype'] or '-'}  {row['policy']}  "
            f"driver={row['driver']}  opts={row['mount_options'] or '-'}"
        )
        print(f"    -> {row['prefix']}")
        if row["reason"]:
            print(f"    ({row['reason']})")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.dry_run:
        return run(args)

    # One stick at a time. Two large copies at once would contend for the same
    # USB bus, the same disk and the same cluster, and finish later than if they
    # had queued.
    os.makedirs(args.state_dir, mode=0o700, exist_ok=True)
    with open(os.path.join(args.state_dir, ".lock"), "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return run(args)


if __name__ == "__main__":
    sys.exit(main())
