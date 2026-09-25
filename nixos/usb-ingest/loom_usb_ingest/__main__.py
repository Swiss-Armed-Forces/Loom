"""Ingest one USB device into Loom.

Started per device by a udev rule, through `loom-usb-ingest@<kname>.service`. See
nixos/usb-ingest.nix for the wiring and Documentation/appliance.md for what this means
for the box's threat model.
"""

import argparse
import fcntl
import logging
import os
import pwd
import subprocess
import sys
import time
from collections.abc import Mapping
from typing import NamedTuple

from loom_usb_ingest import (
    devices,
    filesystems,
    mounts,
    naming,
    pane,
    progress,
    report,
    transfer,
    watch,
)
from loom_usb_ingest.manifest import (
    KeyGuardRecord,
    Manifest,
    Stick,
    Totals,
    VolumeMount,
    VolumePlan,
    annotate,
)

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
    # Optional, because two of the three modes below are not about one device: the
    # watcher draws every device there is, and neither it nor a release needs one
    # named on the command line.
    parser.add_argument(
        "device", nargs="?", help="whole-disk device node, e.g. /dev/sdb"
    )
    parser.add_argument("--bucket", default="loom-intake")
    parser.add_argument("--endpoint", default="https://s3.loom")
    parser.add_argument("--prefix", default="usb-crawled")
    parser.add_argument("--namespace", default="loom")
    parser.add_argument("--kubeconfig", default="/home/loom/.kube/config")
    parser.add_argument("--mount-root", default="/run/loom/usb")
    # Never the mount root: the lock, the mc configuration and state.json would
    # then share a directory with somebody else's mounted filesystems.
    parser.add_argument("--state-dir", default="/run/loom/usb-state")
    parser.add_argument("--key-guard-state-dir", default="/run/loom/key-guard")
    parser.add_argument("--console-socket", default="/run/loom/tmux.sock")
    parser.add_argument(
        "--progress-dir",
        default="/run/loom/usb-progress",
        help="where per-device progress records are published for the console pane",
    )
    parser.add_argument(
        "--owner",
        default="loom",
        help="user the mounted files are presented as owned by",
    )
    parser.add_argument(
        "--cluster-wait",
        type=int,
        default=transfer.CLUSTER_WAIT_TIMEOUT_S,
        help="seconds to wait for the intake bucket to answer before giving up;"
        " the default is an hour, because a box that has just been switched on"
        " takes most of one to bring Loom up",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the volumes, mount recipes and object keys, and change nothing",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="draw the progress of every ingest in flight; this is what the console"
        " pane runs, and it exits when the last device is gone",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="take the devices that are no longer plugged in out of the console"
        " pane; run from the udev remove rule, and from the unit's ExecStopPost",
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

    box.nix declares `loom` as an ordinary user without pinning a uid, so the value is
    only known on the running box.
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


def describe(
    disk: devices.Disk,
    identity: naming.StickIdentity,
    supported: frozenset[str],
) -> list[VolumePlan]:
    """The per-volume plan, used by --dry-run and by the manifest alike."""
    rows = []
    for index, volume in enumerate(disk.volumes, start=1):
        plan = filesystems.plan_mount(volume.fstype, 0, 0, supported)
        rows.append(
            VolumePlan(
                device=volume.path,
                prefix=_volume_prefix(identity, index, volume, len(disk.volumes)),
                fstype=volume.fstype,
                label=volume.label,
                size_bytes=volume.size,
                mount=VolumeMount(
                    policy=str(plan.policy),
                    options=plan.option_string,
                    driver=plan.helper or plan.fstype or "auto",
                    reason=plan.reason,
                ),
            )
        )
    return rows


def _duration(seconds: int) -> str:
    """How long the box waited, in the units somebody standing at it would use."""
    if seconds >= 120:
        return f"{seconds // 60} minutes"
    return f"{seconds} seconds"


def run(args: argparse.Namespace) -> int:
    # pylint: disable=too-many-locals,too-many-return-statements,too-many-branches
    disk = settle(args.device)
    if not disk.kernel_name:
        # Announced, not just logged: a stick the box cannot read at all is the one
        # case where nothing else will ever appear on the screen -- there is no pane,
        # no progress record and no manifest, so silence would read as "ignored".
        report.failure(
            f"{args.device} is not a block device this box can read",
            "",
            args.console_socket,
        )
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

    # Published, and the pane opened, before anything is copied -- the wait for the
    # cluster below is often the longest part of an ingest, and "waiting for Loom to
    # answer" is exactly what somebody standing at the box needs to be told.
    reporter = progress.Reporter(
        args.progress_dir, disk.kernel_name, disk.path, identity.prefix_component
    )
    pane.open_pane(
        args.console_socket,
        pane.watcher_command(args.progress_dir, args.console_socket),
    )

    config_dir = os.path.join(args.state_dir, "mc")
    os.makedirs(config_dir, mode=0o700, exist_ok=True)
    # Built once and handed to every call: the endpoint lives in here now (see
    # `mc_env`), so there is no step between here and the copy that can fail because
    # Loom has not finished starting.
    env = transfer.mc_env(config_dir, args.endpoint)

    waited = transfer.wait_for_cluster(
        args.bucket,
        env,
        args.cluster_wait,
        transfer.WaitHooks(
            # Retried by the wait rather than done once before it, because reading the
            # cluster's certificate needs the same cluster the wait is waiting for.
            trust=lambda: transfer.install_cluster_ca(
                config_dir, args.namespace, args.kubeconfig
            ),
            # What it is waiting on, on the row rather than in the journal: "waiting"
            # with no reason looks the same after five seconds and after an hour.
            on_attempt=lambda reason: reporter.note(report.condense(reason)),
        ),
    )
    if not waited.ready:
        reason = report.failure(
            f"{disk.path} was not ingested",
            f"{args.endpoint} never answered in {_duration(args.cluster_wait)}: "
            f"{waited.last_error}",
            args.console_socket,
        )
        reporter.finish(0, 0, 1, reason)
        return 1

    report.warn_if_short_on_space(
        "/", sum(v.size for v in disk.volumes), args.console_socket
    )

    return _ingest_volumes(
        args, disk, identity, plan_rows, supported, env, guard, owner, reporter
    )


def _ingest_volumes(
    args: argparse.Namespace,
    disk: devices.Disk,
    identity: naming.StickIdentity,
    plan_rows: list[VolumePlan],
    supported: frozenset[str],
    env: Mapping[str, str],
    guard: devices.KeyGuard,
    owner: _Owner,
    reporter: progress.Reporter,
) -> int:
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    total_objects = 0
    total_bytes = 0
    total_failures = 0
    # The first thing that went wrong on this stick, kept for the row the operator
    # reads at the end. Counts say how much went wrong; only this says what.
    first_error = ""

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
            plan_rows = annotate(plan_rows, volume.path, "skipped", mounted.reason)
            # A volume that could not be mounted is the commonest way for a stick to
            # produce fewer documents than the operator expected -- an encrypted
            # partition, a filesystem this box has no driver for -- and until now the
            # only account of it was in a manifest inside the bucket.
            first_error = first_error or f"{volume.path} skipped: {mounted.reason}"
            report.failure(
                f"{volume.path} was not copied", mounted.reason, args.console_socket
            )
            continue

        # Measured once the volume is mounted and before a byte moves: this is what
        # the bar in the console pane is a fraction of.
        reporter.start_volume(
            volume.path,
            index,
            len(disk.volumes),
            progress.volume_bytes(mounted.mountpoint),
        )

        try:
            result = transfer.mirror(
                mounted.mountpoint,
                args.bucket,
                f"{args.prefix}/{prefix}",
                env,
                on_event=reporter.advance,
            )
        finally:
            mounts.unmount(mounted.mountpoint)

        total_objects += result.objects
        total_bytes += result.bytes_transferred
        total_failures += result.failures
        plan_rows = annotate(
            plan_rows,
            volume.path,
            "ingested",
            f"{result.objects} objects, {result.failures} failures",
        )
        uploaded = (
            f"{volume.path}: {result.objects} files uploaded "
            f"({result.bytes_transferred / (1024 ** 3):.1f} GiB)"
        )
        if result.failures:
            first_error = first_error or result.first_error
            report.failure(
                f"{uploaded}, {result.failures} failed",
                result.first_error,
                args.console_socket,
            )
        else:
            report.announce(f"[loom] {uploaded}.", args.console_socket)

    manifest = Manifest(
        status="complete" if total_failures == 0 else "partial",
        prefix=f"{args.prefix}/{identity.prefix_component}",
        stick=Stick(
            device=disk.path,
            name=identity.name,
            identifier=identity.identifier,
            size_bytes=disk.size,
            udev=disk.properties,
        ),
        key_guard=KeyGuardRecord(
            state=str(guard.state), authoritative=guard.authoritative
        ),
        totals=Totals(
            objects=total_objects, bytes=total_bytes, failures=total_failures
        ),
        volumes=plan_rows,
    )

    manifest_error = transfer.put_manifest(
        manifest,
        args.bucket,
        f"{args.prefix}/{identity.prefix_component}/{MANIFEST_NAME}",
        env,
    )
    if manifest_error:
        first_error = first_error or f"provenance record not written: {manifest_error}"
        report.failure(
            f"{disk.path}: the provenance record was not written",
            manifest_error,
            args.console_socket,
        )
    report.write_state(args.state_dir, manifest)

    # Phrased so that the reason `report.failure` appends lands at the end of the
    # line rather than after the full stop of "safe to remove".
    summary = (
        f"{disk.path} done: {total_objects} files, "
        f"{total_bytes / (1024 ** 3):.1f} GiB, {total_failures} failures "
        "-- safe to remove"
    )

    # The pane keeps saying this until the stick is actually unplugged, which is the
    # half `announce` alone could never do: a line scrolls, a pane does not. What
    # takes the row away is the device going, not this call -- see `release`.
    reporter.finish(
        total_objects, total_bytes, total_failures, report.condense(first_error)
    )
    if total_failures:
        report.failure(summary, first_error, args.console_socket)
    else:
        report.announce(f"[loom] {summary}", args.console_socket)
    return 0 if total_failures == 0 else 1


def _print_dry_run(
    disk: devices.Disk, identity: naming.StickIdentity, rows: list[VolumePlan]
) -> None:
    print(f"device:     {disk.path} ({disk.size} bytes)")
    print(f"identity:   {identity.prefix_component}")
    for row in rows:
        print(
            f"  {row.device}  {row.fstype or '-'}  {row.mount.policy}  "
            f"driver={row.mount.driver}  opts={row.mount.options or '-'}"
        )
        print(f"    -> {row.prefix}")
        if row.mount.reason:
            print(f"    ({row.mount.reason})")


def release(args: argparse.Namespace) -> int:
    """Take the devices that are no longer plugged in out of the console pane.

    A sweep of every record rather than an instruction about one device, because the
    two places it runs from know different things:

      * The udev remove rule, through loom-usb-release.service. This is what normally
        ends a pane: it fires when a device actually goes away, which -- unlike the
        end of a copy -- is the event the pane is waiting for.
      * The ingest unit's ExecStopPost, which fires when the *copy* stops. A oneshot
        stops the moment its work is done, so this runs while a finished stick is
        still in the box, and the sweep deliberately leaves that record alone. This
        used to withdraw it unconditionally, which took the pane off the screen about
        a second after it had anything worth reading on it.

    `--release <device>` additionally says whose ingest has ended, which is the one
    thing a sweep cannot see: a record for a device that is still present but whose
    copy is over without having finished would otherwise claim to be copying for as
    long as the stick stayed in. Only that device is judged -- another stick's copy
    may legitimately be running.

    The pane is closed here only as a backstop. The watcher ends itself when the last
    record is gone, and a pane whose command exits is closed by tmux; this covers the
    case where the watcher is not running at all, so that a stale split cannot outlive
    every stick that justified it.
    """
    ending = os.path.basename(args.device) if args.device else None

    for record in progress.read_all(args.progress_dir):
        if not progress.device_present(record):
            progress.withdraw(args.progress_dir, record.kernel_name)
        elif record.kernel_name == ending and not record.finished:
            progress.mark_interrupted(args.progress_dir, record)

    if not progress.read_all(args.progress_dir):
        pane.close_pane(args.console_socket)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.watch:
        return watch.watch(args.progress_dir)

    if args.release:
        return release(args)

    if not args.device:
        logger.error("No device given. Pass one, or --watch, or --release.")
        return 2

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
