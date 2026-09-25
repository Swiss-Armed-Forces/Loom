#!/usr/bin/env bash
# Prepares any USB stick as a Loom USB-ingest test fixture.
#
# nixos/usb-ingest/ decides, per volume, whether the appliance mounts media
# someone handed it and with which driver and options. filesystems.py has three
# tiers -- a REFUSED table of six container formats, a KNOWN allowlist of
# fifteen filesystem types, and a generic `mount -t auto` for anything else the
# running kernel admits to supporting -- and devices.py takes every partition on
# every USB disk. The only test that makes real filesystems is the VM test, and
# it creates four: vfat, ext4, ntfs and a LUKS container, on virtio disks, so
# even the ID_BUS=="usb" udev rule is bypassed.
#
# This writes 26 partitions, one filesystem each, so that plugging the result
# into an appliance takes every branch of plan_mount at once. Nothing about the
# stick is baked in: the table is a fixed 2976 MiB whatever the capacity, so any
# stick of 4 GiB or more produces the identical layout and the remainder is left
# unallocated.
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# This runs under sudo, where PATH is whatever sudoers allows and git may not be
# on it at all. The repository root is two levels up from nixos/scripts/ either
# way; git is only asked because a worktree or a symlinked checkout can make the
# literal path wrong, and a failure there is not worth aborting over.
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "${CONTEXT_DIR}" ]]; then
    CONTEXT_DIR=$( cd -- "${SCRIPT_DIR}/../.." &> /dev/null && pwd )
fi

# The stick, as a /dev/disk/by-id/usb-* handle. No default, and /dev/sdX is
# refused outright: kernel names move between plugs, and the whole point of the
# guards below is that the disk about to be erased was identified deliberately.
DEVICE=""

# What lands on every populated partition. The integration suite's fixtures are
# a good corpus for this: real archives, mail, Office documents and images, with
# one deliberately hostile filename.
ASSETS_DIR="${CONTEXT_DIR}/integrationtest/assets"

# A buildEnv of mkfs tools, passed as --tools by the build-ingest-test-stick
# devenv script so the run does not depend on what happens to be on PATH. No
# default: preflight says so rather than letting a mkfs fail halfway.
TOOLS=""

# Must be the stick's own ID_SERIAL_SHORT. Reading the serial off the device and
# typing it back is what keeps a device-agnostic script safe -- it cannot be
# satisfied without having looked at which disk is about to be erased.
CONSENT=""

# Empty means every row. Both take comma-separated partition numbers, and exist
# because reformatting one row must not mean re-cutting the whole table.
ONLY=""
EXCLUDE=""

WORK_DIR=""
KEEP_WORK=false

# Set by report_result. A failed row's own mkfs output is the only thing that
# explains it, so the scratch directory survives when there is something in it
# worth reading.
FAILURES=0

# 256 KiB captured from a real ZFS vdev label, because a pool cannot be created
# without the kernel module. See make_zfs.
ZFS_FIXTURE="${SCRIPT_DIR}/ingest_test_stick_zfs_label.bin"

# The table is 2976 MiB; 4 GiB leaves room for GPT, alignment and a little
# slack. Refusing is deliberate -- silently shrinking rows would produce a stick
# that looks like this one and is not.
MIN_CAPACITY_BYTES=$(( 4 * 1024 * 1024 * 1024 ))

# FAT32 is only FAT32 above this many clusters; below it the filesystem is
# detected as FAT16 instead. mkfs.fat warns rather than failing, so it is
# asserted in make_fat32.
FAT32_MIN_CLUSTERS=65525

# Partition labels the appliance itself uses, copied from
# nixos/usb-ingest/loom_usb_ingest/devices.py, which owns them. A disk carrying
# any of these is Loom's own media -- a key stick or an installer stick -- and
# erasing one is not a cosmetic mistake: nixos/key-guard.nix powers the box off
# ten seconds after its key stick stops reading.
LOOM_PARTLABELS=(loom-key loom-esp loom-root-luks loom-live-esp loom-live-store)

# What this script's own partition labels look like. A stick it already built
# has to be rebuildable, and partition 20 of that stick is a LUKS container by
# design -- so the "this might be a key stick" refusal below has to be able to
# tell the fixture's LUKS apart from everybody else's.
OWN_PARTLABEL_PATTERN='^fstest[0-9][0-9]-'

# One writer at a time, in a root-owned directory rather than /tmp.
#
# /tmp is sticky and world-writable, and this host -- like any recent NixOS --
# runs fs.protected_regular=2, under which even root is refused a write-open on
# a file it does not own in such a directory. A lock there is therefore poisoned
# for every later run the moment one non-root invocation creates it.
LOCK_FILE="/run/lock/loom-ingest-test-stick.lock"

# The LUKS passphrase on partition 20. Deliberately weak and deliberately
# written down here: the container is a signature for blkid to find, never a
# secret, and the weak PBKDF keeps luksFormat from spending seconds and a
# gigabyte of RAM on a volume nobody will open.
LUKS_PASSPHRASE="loomtest"

# number|short|size|expected blkid TYPE|filesystem label|payload|maker
#
# Ordering is mountable-first, refusals-last, so the console pane and the S3
# listing read top to bottom as "everything that should work, then everything
# that should be refused".
#
# The filesystem label matters more than it looks: __main__.py feeds
# naming.volume_component the *filesystem* label, not the partition label, so it
# is what lands in the object key. Eleven characters is the FAT and exFAT
# ceiling, and [A-Z0-9] both satisfies ISO9660's d-characters and passes
# naming.sanitize_component unchanged, so no hash suffix is appended.
#
# payload is one of:
#   full   all 67 assets
#   nodq   without the asset whose name starts with a double quote
#   hfs    without the names HFS cannot hold in 31 bytes
#   none   nothing; the volume is a signature, empty, or read-only by design
ROWS=(
    "1|fat32|64M|vfat|LOOM01FAT32|nodq|fat32"
    "2|fat16|32M|vfat|LOOM02FAT16|nodq|fat16"
    "3|exfat|128M|exfat|LOOM03EXFAT|nodq|exfat"
    "4|ntfs|128M|ntfs|LOOM04NTFS|full|ntfs"
    "5|ext2|64M|ext2|LOOM05EXT2|full|ext2"
    "6|ext3|64M|ext3|LOOM06EXT3|full|ext3"
    "7|ext4|64M|ext4|LOOM07EXT4|full|ext4"
    "8|ext4dirty|64M|ext4|LOOM08DIRTY|full|ext4dirty"
    "9|xfs|512M|xfs|LOOM09XFS|full|xfs"
    "10|btrfs|512M|btrfs|LOOM10BTRFS|full|btrfs"
    "11|f2fs|512M|f2fs|LOOM11F2FS|full|f2fs"
    "12|hfs|64M|hfs|LOOM12HFS|hfs|hfs"
    "13|hfsplus|64M|hfsplus|LOOM13HFSP|full|hfsplus"
    "14|iso9660|32M|iso9660|LOOM14ISO|full|iso9660"
    "15|udf|128M|udf|LOOM15UDF|full|udf"
    "16|apfs|64M|apfs|LOOM16APFS|none|apfs"
    "17|squashfs|32M|squashfs||full|squashfs"
    "18|erofs|32M|erofs||full|erofs"
    "19|minix|32M|minix||none|minix"
    "20|luks|64M|crypto_LUKS||none|luks"
    "21|zfs|128M|zfs_member|LOOM21ZFS|none|zfs"
    "22|lvm|32M|LVM2_member||none|lvm"
    "23|mdraid|64M|linux_raid_member||none|mdraid"
    "24|swap|64M|swap|LOOM24SWAP|none|swap"
    "25|bitlocker|16M|BitLocker||none|bitlocker"
    "26|blank|16M|||none|blank"
)

# Filled in by preflight and the format loop.
DEVICE_NODE=""
DEVICE_KERNEL_NAME=""
DEVICE_SERIAL=""
DEVICE_SIZE_BYTES=0
declare -A ROW_STATUS=()
declare -A ROW_DETAIL=()

usage(){
    cat <<'EOF'
Usage: make_ingest_test_stick.sh --device PATH --tools PATH [options]

Writes 26 partitions to a USB stick, one filesystem per partition, each of the
mountable ones carrying a copy of the integration test assets. The result
exercises every branch of nixos/usb-ingest's plan_mount at once.

Required:
  --device PATH             /dev/disk/by-id/usb-* handle for the stick. Kernel
                            names (/dev/sdX) are refused: they move.
  --tools PATH              buildEnv holding the mkfs tools. Supplied by the
                            build-ingest-test-stick devenv script.

Consent:
  --i-know-this-erases SERIAL
                            The stick's own ID_SERIAL_SHORT, which the plan
                            prints. Without it nothing is written and the script
                            only reports what it would do.

Options:
  --assets DIR              Payload directory (default: integrationtest/assets)
  --only N[,N...]           Only build these partition numbers
  --skip N[,N...]           Build everything except these partition numbers
  --keep-work               Keep the scratch directory instead of removing it
  -h, --help                This text

Rebuilding one row does not re-cut the table: --only 16 reformats partition 16
in place. The table is rewritten only when neither --only nor --skip is given.
EOF
}

log(){
    echo "[*] ${*}"
}

warn(){
    echo "[!] ${*}" >&2
}

die(){
    echo "[x] ${*}" >&2
    exit 1
}

# Echoes true or false rather than returning a status, so that callers can use
# it without putting a function in a condition -- which would disable `set -e`
# for everything inside it.
is_selected(){
    local number="${1}"

    if [[ -n "${ONLY}" ]]; then
        if [[ ",${ONLY}," == *",${number},"* ]]; then
            echo true
        else
            echo false
        fi
        return 0
    fi

    if [[ -n "${EXCLUDE}" && ",${EXCLUDE}," == *",${number},"* ]]; then
        echo false
        return 0
    fi

    echo true
    return 0
}

# The by-id path of one partition. Always derived from --device rather than from
# a kernel name, so that a re-enumeration between two steps cannot silently move
# the target.
partition_path(){
    echo "${DEVICE}-part${1}"
}

parse_arguments(){
    while [[ $# -gt 0 ]]; do
        case "${1}" in
            --device)
                DEVICE="${2:-}"
                shift 2
                ;;
            --tools)
                TOOLS="${2:-}"
                shift 2
                ;;
            --assets)
                ASSETS_DIR="${2:-}"
                shift 2
                ;;
            --i-know-this-erases)
                CONSENT="${2:-}"
                shift 2
                ;;
            --only)
                ONLY="${2:-}"
                shift 2
                ;;
            --skip)
                EXCLUDE="${2:-}"
                shift 2
                ;;
            --keep-work)
                KEEP_WORK=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                usage >&2
                die "Unknown argument: ${1}"
                ;;
        esac
    done

    [[ -n "${DEVICE}" ]] || die "--device is required"
    [[ -n "${TOOLS}" ]] || die "--tools is required"

    if [[ -n "${ONLY}" && -n "${EXCLUDE}" ]]; then
        die "--only and --skip are mutually exclusive"
    fi
    return 0
}

# Every binary the run needs, from --tools rather than from the ambient PATH.
# udevadm is the exception: it has to be the running system's, because it talks
# to that system's udevd.
require_tools(){
    [[ -d "${TOOLS}" ]] || die "--tools is not a directory: ${TOOLS}"
    PATH="${TOOLS}/bin:${TOOLS}/sbin:${PATH}"
    export PATH

    local missing=()
    local tool
    for tool in sgdisk partx wipefs blkid blockdev lsblk findmnt flock rsync losetup \
        mkfs.fat mkfs.ext2 mkfs.ext3 mkfs.ext4 debugfs dumpe2fs mkfs.exfat \
        mkntfs mkfs.xfs mkfs.btrfs mkfs.f2fs mkudffs hformat hmount humount \
        hmkdir hcopy mkfs.hfsplus mkapfs mksquashfs mkfs.erofs xorriso \
        mkfs.minix pvcreate mdadm mkswap cryptsetup udevadm; do
        if ! command -v "${tool}" > /dev/null 2>&1; then
            missing+=("${tool}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        die "Missing tools: ${missing[*]}"
    fi
    return 0
}

# Everything below runs before the first write, and every one of them is fatal.
preflight(){
    # The shape of --device is checked before anything else, so that pointing at
    # /dev/sdc says so rather than complaining about privileges first.
    [[ "${DEVICE}" == /dev/disk/by-id/usb-* ]] ||
        die "--device must be a /dev/disk/by-id/usb-* path, not '${DEVICE}'"
    [[ -e "${DEVICE}" ]] || die "No such device: ${DEVICE}"

    [[ ${EUID} -eq 0 ]] || die "This writes partition tables and filesystems; run it under sudo"

    DEVICE_NODE=$(readlink -f "${DEVICE}")
    [[ -b "${DEVICE_NODE}" ]] || die "${DEVICE} does not resolve to a block device"
    DEVICE_KERNEL_NAME=$(basename "${DEVICE_NODE}")

    local node_type
    node_type=$(lsblk --nodeps --noheadings --output TYPE "${DEVICE_NODE}")
    [[ "${node_type}" == "disk" ]] ||
        die "${DEVICE} is a ${node_type}, not a whole disk"

    local bus
    bus=$(udevadm info --query=property --value --property=ID_BUS "${DEVICE_NODE}" || true)
    [[ "${bus}" == "usb" ]] || die "${DEVICE} is not on the USB bus (ID_BUS=${bus:-unset})"

    DEVICE_SERIAL=$(udevadm info --query=property --value --property=ID_SERIAL_SHORT "${DEVICE_NODE}" || true)
    [[ -n "${DEVICE_SERIAL}" ]] || die "${DEVICE} reports no ID_SERIAL_SHORT to confirm against"

    DEVICE_SIZE_BYTES=$(blockdev --getsize64 "${DEVICE_NODE}")
    if [[ "${DEVICE_SIZE_BYTES}" -lt "${MIN_CAPACITY_BYTES}" ]]; then
        die "${DEVICE} holds ${DEVICE_SIZE_BYTES} bytes; the table needs at least ${MIN_CAPACITY_BYTES}"
    fi

    assert_not_system_disk
    assert_nothing_mounted
    assert_not_loom_media
    assert_assets_present
    return 0
}

# Mirrors devices.protected_disks(): the disk carrying the running system is
# never a candidate, however it was named on the command line.
assert_not_system_disk(){
    local mountpoint source parent basename_source
    for mountpoint in / /boot /nix/store; do
        findmnt --target "${mountpoint}" > /dev/null 2>&1 || continue
        source=$(findmnt --noheadings --output SOURCE --target "${mountpoint}" | head -1)
        [[ -b "${source}" ]] || continue

        parent=$(lsblk --noheadings --output PKNAME "${source}" | head -1)
        basename_source=$(basename "${source}")
        if [[ "${parent}" == "${DEVICE_KERNEL_NAME}" || "${basename_source}" == "${DEVICE_KERNEL_NAME}" ]]; then
            die "${DEVICE} carries ${mountpoint}"
        fi
    done

    local holders_dir="/sys/block/${DEVICE_KERNEL_NAME}/holders"
    local holders=""
    if [[ -d "${holders_dir}" ]]; then
        holders=$(ls -A "${holders_dir}")
    fi
    [[ -z "${holders}" ]] ||
        die "${DEVICE} has holders (${holders}); something is stacked on it"
    return 0
}

# Re-run immediately before the first write as well: a desktop auto-mounter can
# attach a partition between the check and the sgdisk.
assert_nothing_mounted(){
    local mounted
    mounted=$(lsblk --noheadings --output MOUNTPOINT "${DEVICE_NODE}" | tr -d '[:space:]')
    [[ -z "${mounted}" ]] || die "Something on ${DEVICE} is mounted; unmount it first"

    if grep -q "^${DEVICE_NODE}" /proc/swaps; then
        die "A partition on ${DEVICE} is in use as swap"
    fi
    return 0
}

assert_not_loom_media(){
    local partlabels loom
    partlabels=$(lsblk --noheadings --output PARTLABEL "${DEVICE_NODE}")
    for loom in "${LOOM_PARTLABELS[@]}"; do
        if grep -qx -- "${loom}" <<< "${partlabels}"; then
            die "${DEVICE} carries the Loom partition label '${loom}'; this is Loom's own media"
        fi
    done

    # A LUKS container is the shape a key stick has, so one is refused -- unless
    # it sits on a partition this script itself labelled. Checking the label
    # rather than merely "is there any LUKS here" is what lets a fixture be
    # rebuilt while still refusing a real key stick, whose partition is called
    # loom-key and is caught above in any case.
    local pairs line label
    pairs=$(lsblk --noheadings --pairs --output PARTLABEL,FSTYPE "${DEVICE_NODE}")
    while IFS= read -r line; do
        [[ "${line}" == *'FSTYPE="crypto_LUKS"'* ]] || continue

        label=${line#PARTLABEL=\"}
        label=${label%%\"*}

        if ! grep -qE -- "${OWN_PARTLABEL_PATTERN}" <<< "${label}"; then
            die "${DEVICE} carries a LUKS container on '${label:-an unlabelled partition}'; refusing in case it is a key stick"
        fi
    done <<< "${pairs}"
    return 0
}

# The assets live in git-lfs. A fresh clone without `git lfs pull` leaves 130
# byte pointer files behind, and a stick built from those would look right and
# index nothing.
assert_assets_present(){
    [[ -d "${ASSETS_DIR}" ]] || die "No such assets directory: ${ASSETS_DIR}"

    local pointers
    pointers=$(grep -rl '^version https://git-lfs' "${ASSETS_DIR}" || true)
    if [[ -n "${pointers}" ]]; then
        warn "These assets are git-lfs pointers, not content:"
        echo "${pointers}" >&2
        die "Run 'git lfs pull' first"
    fi
    return 0
}

report_plan(){
    local total=0 row
    local number short size want label payload maker partlabel pick

    echo
    echo "Device:    ${DEVICE}"
    echo "           ${DEVICE_NODE}, serial ${DEVICE_SERIAL}, ${DEVICE_SIZE_BYTES} bytes"
    echo "Assets:    ${ASSETS_DIR}"
    echo
    printf '%-4s %-22s %-6s %-18s %-12s %s\n' "#" "PARTLABEL" "SIZE" "TYPE" "LABEL" "PAYLOAD"

    for row in "${ROWS[@]}"; do
        IFS='|' read -r number short size want label payload maker <<< "${row}"
        pick=$(is_selected "${number}")
        [[ "${pick}" == true ]] || continue

        printf -v partlabel 'fstest%02d-%s' "${number}" "${short}"
        printf '%-4s %-22s %-6s %-18s %-12s %s\n' \
            "${number}" "${partlabel}" "${size}" "${want:-<none>}" "${label}" "${payload}"
        total=$(( total + ${size%M} ))
    done

    echo
    echo "Total: ${total} MiB of $(( DEVICE_SIZE_BYTES / 1024 / 1024 )) MiB; the remainder stays unallocated."
    echo
    # maker is read but unused here; naming it keeps the read aligned with ROWS.
    : "${maker}"
    return 0
}

# Three payload trees, staged once and reused by every partition, so the
# per-filesystem deviations are decided in exactly one place.
#
# Policy: keep the real name where the filesystem allows it, drop the file where
# it does not, and write nothing onto the stick to explain the difference.
stage_payloads(){
    local full="${WORK_DIR}/payload-full"
    local nodq="${WORK_DIR}/payload-nodq"
    local hfs="${WORK_DIR}/payload-hfs"
    local count_full count_nodq count_hfs

    mkdir -p "${full}" "${nodq}" "${hfs}"
    cp -a "${ASSETS_DIR}/." "${full}/"
    cp -a "${ASSETS_DIR}/." "${nodq}/"
    cp -a "${ASSETS_DIR}/." "${hfs}/"

    # FAT long names and exFAT both reject " * / : < > ? \ | outright. Only one
    # asset is affected, and it is deliberately named that way. NTFS through
    # ntfs-3g accepts it (windows_names is not in use), and ISO9660 with Rock
    # Ridge accepts everything but / and NUL, so neither needs this tree.
    find "${nodq}" -name '*"*' -delete

    # HFS caps a name at 31 bytes. Eight assets are longer.
    local listing="${WORK_DIR}/hfs-candidates"
    local path name
    find "${hfs}" -type f -print0 > "${listing}"
    while IFS= read -r -d '' path; do
        name=$(basename "${path}")
        if [[ ${#name} -gt 31 ]]; then
            rm -f "${path}"
        fi
    done < "${listing}"

    count_full=$(count_files "${full}")
    count_nodq=$(count_files "${nodq}")
    count_hfs=$(count_files "${hfs}")
    log "Staged payloads: full=${count_full} nodq=${count_nodq} hfs=${count_hfs}"
    return 0
}

count_files(){
    find "${1}" -type f | wc -l
}

payload_dir(){
    case "${1}" in
        full) echo "${WORK_DIR}/payload-full" ;;
        nodq) echo "${WORK_DIR}/payload-nodq" ;;
        hfs) echo "${WORK_DIR}/payload-hfs" ;;
        none) echo "" ;;
        *) die "Unknown payload mode: ${1}" ;;
    esac
}

# Phase 1. One batch for the whole table: either it is all there or nothing is,
# because a half-written GPT is the one state worth refusing to continue from.
partition_disk(){
    local row number short size want label payload maker partlabel

    log "Re-checking that nothing mounted itself while we were thinking"
    assert_nothing_mounted

    log "Writing the partition table"
    sgdisk --zap-all "${DEVICE_NODE}" > /dev/null

    local argv=(--set-alignment=2048)
    for row in "${ROWS[@]}"; do
        IFS='|' read -r number short size want label payload maker <<< "${row}"
        printf -v partlabel 'fstest%02d-%s' "${number}" "${short}"
        # Type 0700 throughout on purpose. devices.py never reads the type GUID,
        # so a truthful one buys nothing -- while 8200, 8E00, FD00 and 8309
        # would invite systemd-gpt-auto-generator, lvm2 and mdadm udev rules to
        # act on the stick here on the build host.
        argv+=(
            "--new=${number}:0:+${size}"
            "--typecode=${number}:0700"
            "--change-name=${number}:${partlabel}"
        )
    done
    argv+=("${DEVICE_NODE}")
    sgdisk "${argv[@]}" > /dev/null

    settle_partitions
    return 0
}

settle_partitions(){
    # partx rather than parted: the appliance build dropped parted for exactly
    # this, and util-linux is already in the tool set.
    partx --update "${DEVICE_NODE}" > /dev/null 2>&1 || true
    udevadm settle --timeout=30 || true
    return 0
}

# Phase 2. Every row is independent: a missing mkapfs must cost partition 16 and
# nothing else.
format_rows(){
    local row number short size want label payload maker partlabel pick
    local device logfile status maker_pid tail_output

    for row in "${ROWS[@]}"; do
        IFS='|' read -r number short size want label payload maker <<< "${row}"
        pick=$(is_selected "${number}")
        [[ "${pick}" == true ]] || continue

        printf -v partlabel 'fstest%02d-%s' "${number}" "${short}"
        device=$(partition_path "${number}")
        logfile="${WORK_DIR}/p${number}.log"
        log "Partition ${number} (${partlabel})"

        if [[ ! -e "${device}" ]]; then
            record "${number}" "failed" "no such partition: ${device}"
            continue
        fi

        # wipefs fires a udev event, and whatever re-probes the partition holds
        # it open for a moment. Settling here keeps that out of the maker.
        wipefs --all --force "${device}" > /dev/null 2>&1 || true
        udevadm settle --timeout=30 || true

        # The maker runs as a backgrounded subshell, and this is not a style
        # choice. A function invoked in an `if` condition -- or on either side
        # of || or && -- has `set -e` disabled for its whole body, and bash
        # propagates that even into an explicit `( set -e; ... )`. A maker
        # called that way therefore runs on past its first failed command and
        # still returns 0, so a failing mkfs was reported as a success and only
        # the blkid check below noticed. Backgrounding detaches the subshell
        # from the condition context, so `set -e` applies inside it again, and
        # `wait` reports the status without becoming a condition for it.
        status=0
        ( set -e; "make_${maker}" "${device}" "${label}" "${payload}" "${number}" ) \
            > "${logfile}" 2>&1 &
        maker_pid=$!
        wait "${maker_pid}" || status=$?

        if [[ "${status}" -eq 0 ]]; then
            verify_row "${number}" "${device}" "${want}"
        else
            tail_output=$(tail -3 "${logfile}" | tr '\n' ' ')
            record "${number}" "failed" "${tail_output:-exit status ${status}}"
            blank_partition "${device}"
        fi
    done
    return 0
}

# The one check that stays, because it is part of building the stick rather than
# testing it. A synthetic BitLocker or ZFS signature libblkid declines to name is
# a partition that silently tests nothing, and `mkfs.fat -F 32` on a too-small
# device warns rather than failing, so a FAT32 row can quietly come out FAT16.
verify_row(){
    local number="${1}" device="${2}" want="${3}"
    local got

    blockdev --flushbufs "${device}" > /dev/null 2>&1 || true
    got=$(blkid --probe --output value --match-tag TYPE "${device}" || true)

    if [[ "${got}" == "${want}" ]]; then
        record "${number}" "ok" "${got:-<none>}"
    else
        record "${number}" "failed" "blkid says '${got:-<none>}', expected '${want:-<none>}'"
        blank_partition "${device}"
    fi
    return 0
}

# A mkfs that died half way leaves a partial signature, and blkid then reports
# something that is neither the intended filesystem nor blank -- which would
# corrupt the reading of partition 26 and of the "no recognisable filesystem"
# branch generally. A failed partition has to end up provably blank.
blank_partition(){
    local device="${1}"
    local size_mib

    wipefs --all --force "${device}" > /dev/null 2>&1 || true
    size_mib=$(( $(blockdev --getsize64 "${device}") / 1024 / 1024 ))
    dd if=/dev/zero of="${device}" bs=1M count=1 conv=fsync status=none || true
    dd if=/dev/zero of="${device}" bs=1M count=1 seek=$(( size_mib - 1 )) \
        conv=fsync status=none || true
    return 0
}

record(){
    ROW_STATUS["${1}"]="${2}"
    ROW_DETAIL["${1}"]="${3}"
    return 0
}

# Mount, copy, unmount. Used by every filesystem the kernel can write.
populate_mounted(){
    local device="${1}" fstype="${2}" payload="${3}"
    local source mountpoint
    local status=0

    source=$(payload_dir "${payload}")
    [[ -n "${source}" ]] || return 0

    mountpoint="${WORK_DIR}/mnt"
    mkdir -p "${mountpoint}"
    mount -t "${fstype}" "${device}" "${mountpoint}"

    # Deliberately not --archive. That implies -p -o -g, and vfat, exfat and the
    # other ownerless filesystems have nowhere to put a uid, a gid or a unix
    # mode -- rsync's chown then fails and it exits 23, failing the row. The
    # payload is only directories and regular files, so -r -t copies all of it,
    # and dropping ownership makes every partition carry the same thing rather
    # than something subtly different per filesystem. The appliance overrides
    # ownership at mount time anyway, for exactly these filesystems.
    # The status is captured rather than allowed to propagate, so that the
    # umount below always runs. Letting `set -e` abort here left the volume
    # mounted, and because every row mounts on the same path the next one
    # stacked a second mount on top of it.
    rsync --recursive --times --quiet "${source}/" "${mountpoint}/" || status=$?

    sync
    umount "${mountpoint}"
    return "${status}"
}

# Build an image in the work directory and dd it on. A truncated image is silent
# corruption rather than an error, so the size is asserted before the write; the
# trailing slack is harmless, because each of these records its own extent and
# never reads past it.
write_image(){
    local image="${1}" device="${2}"
    local image_size device_size

    image_size=$(stat -c%s "${image}")
    device_size=$(blockdev --getsize64 "${device}")

    if [[ "${image_size}" -gt "${device_size}" ]]; then
        echo "image is ${image_size} bytes, partition holds ${device_size}" >&2
        return 1
    fi

    dd if="${image}" of="${device}" bs=4M conv=fsync status=none
    blockdev --flushbufs "${device}" > /dev/null 2>&1 || true
    return 0
}

# Every maker takes the same four arguments -- device, filesystem label, payload
# mode, partition number -- so that format_rows can dispatch by name. Several
# ignore some of them.

make_fat32(){
    local device="${1}" label="${2}" payload="${3}"
    local output clusters

    output=$(mkfs.fat -F 32 -s 1 -v -n "${label}" "${device}")
    echo "${output}"

    # -F 32 on a device too small for FAT32_MIN_CLUSTERS is a warning, not an
    # error, and the result is then detected as FAT16. Assert rather than hope.
    clusters=$(sed -n 's/.*provides \([0-9]*\) clusters.*/\1/p' <<< "${output}" | head -1)
    if [[ -z "${clusters}" || "${clusters}" -lt "${FAT32_MIN_CLUSTERS}" ]]; then
        echo "FAT32 needs at least ${FAT32_MIN_CLUSTERS} clusters, got '${clusters:-unknown}'" >&2
        return 1
    fi

    populate_mounted "${device}" vfat "${payload}"
    return 0
}

make_fat16(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.fat -F 16 -s 2 -n "${label}" "${device}"
    populate_mounted "${device}" vfat "${payload}"
    return 0
}

make_exfat(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.exfat -L "${label}" "${device}"
    populate_mounted "${device}" exfat "${payload}"
    return 0
}

# Written through the in-kernel ntfs3 driver, which is only how it gets here.
# The appliance reads it back through ntfs-3g, deliberately: it parses media
# handed over by strangers, and FUSE keeps that parsing in a process that can
# crash without taking the kernel with it.
make_ntfs(){
    local device="${1}" label="${2}" payload="${3}"
    mkntfs --quick --force --label "${label}" "${device}"
    populate_mounted "${device}" ntfs3 "${payload}"
    return 0
}

make_ext2(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.ext2 -F -q -L "${label}" "${device}"
    populate_mounted "${device}" ext2 "${payload}"
    return 0
}

make_ext3(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.ext3 -F -q -L "${label}" "${device}"
    populate_mounted "${device}" ext3 "${payload}"
    return 0
}

make_ext4(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.ext4 -F -q -L "${label}" "${device}"
    populate_mounted "${device}" ext4 "${payload}"
    return 0
}

# The point of this one is that plan_mount's `noload` is doing real work rather
# than being a no-op on every ext4 it ever sees. tune2fs -O needs_recovery is
# rejected outright -- it is not user-settable -- so the flag goes on through
# debugfs' set_super_value, and dumpe2fs confirms it took. A partition that
# claims to be dirty and is not would make `noload` look exercised when it never
# was, so if the flag does not stick the row fails rather than shipping.
make_ext4dirty(){
    local device="${1}" label="${2}" payload="${3}"
    local mask updated features

    mkfs.ext4 -F -q -L "${label}" "${device}"
    populate_mounted "${device}" ext4 "${payload}"

    # tune2fs -O needs_recovery is rejected: it is not user-settable. debugfs'
    # set_super_value can reach it, but only by assigning the whole incompat
    # mask -- there is no "+feature" syntax, and `ssv feature ...` is not a
    # field at all. So read the current mask and OR in
    # EXT4_FEATURE_INCOMPAT_RECOVER (0x4).
    #
    # The mask is s_feature_incompat, a 32-bit little-endian field at offset 96
    # of the superblock, which itself begins 1024 bytes in: 1024 + 96 = 1120.
    # debugfs recomputes the superblock checksum, so metadata_csum survives --
    # e2fsck reports "skipping journal recovery" afterwards rather than a bad
    # superblock.
    mask=$(od --address-radix=n --format=x4 --skip-bytes=1120 --read-bytes=4 "${device}" | tr -d '[:space:]')
    updated=$(printf '0x%x' $(( 0x${mask} | 0x4 )))
    debugfs -w -R "ssv feature_incompat ${updated}" "${device}"

    features=$(dumpe2fs -h "${device}" 2>/dev/null || true)
    if ! grep -q 'needs_recovery' <<< "${features}"; then
        echo "needs_recovery did not stick; refusing to ship a false-dirty ext4" >&2
        return 1
    fi
    return 0
}

make_xfs(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.xfs -q -f -L "${label}" "${device}"
    populate_mounted "${device}" xfs "${payload}"
    return 0
}

make_btrfs(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.btrfs -q -f -L "${label}" "${device}"
    populate_mounted "${device}" btrfs "${payload}"
    return 0
}

make_f2fs(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.f2fs -q -f -l "${label}" "${device}"
    populate_mounted "${device}" f2fs "${payload}"
    return 0
}

# HFS goes through hfsutils rather than a read-write mount: the in-kernel HFS
# write path is ancient, and this needs no kernel driver at all. The tree is
# walked explicitly because hcopy has no recursive mode, and HFS separates path
# components with a colon rather than a slash.
make_hfs(){
    local device="${1}" label="${2}" payload="${3}"
    local source relative hfs_path
    local dirs="${WORK_DIR}/hfs-dirs"
    local files="${WORK_DIR}/hfs-files"

    hformat -l "${label}" "${device}"

    source=$(payload_dir "${payload}")
    [[ -n "${source}" ]] || return 0

    # -printf '%P' prints each path relative to the starting point, which is
    # exactly the relative name HFS wants -- no subshell and no cd.
    find "${source}" -mindepth 1 -type d -printf '%P\n' > "${dirs}"
    find "${source}" -type f -printf '%P\n' > "${files}"

    hmount "${device}"

    while IFS= read -r relative; do
        hfs_path=${relative//\//:}
        hmkdir ":${hfs_path}"
    done < "${dirs}"

    while IFS= read -r relative; do
        hfs_path=${relative//\//:}
        hcopy -r "${source}/${relative}" ":${hfs_path}"
    done < "${files}"

    humount
    return 0
}

# mkfs.hfsplus makes a non-journaled volume, which Linux mounts read-write.
make_hfsplus(){
    local device="${1}" label="${2}" payload="${3}"
    mkfs.hfsplus -v "${label}" "${device}"
    populate_mounted "${device}" hfsplus "${payload}"
    return 0
}

# Rock Ridge is what preserves the 40 character names and the leading double
# quote; plain ISO level 3 would mangle both.
make_iso9660(){
    local device="${1}" label="${2}" payload="${3}" number="${4}"
    local source image="${WORK_DIR}/p${4}.iso"

    source=$(payload_dir "${payload}")
    xorriso -as mkisofs -iso-level 3 -R -J -joliet-long \
        -V "${label}" -o "${image}" "${source}"
    write_image "${image}" "${device}"
    : "${number}"
    return 0
}

# --bootarea=erase matters: for --media-type=hd mkudffs otherwise writes a fake
# MBR into the partition's first sector. The block size is left to detect, which
# picks the device's logical sector size -- 2048 is an optical convention, not a
# UDF requirement, and the kernel probes 512 through 4096 anyway.
make_udf(){
    local device="${1}" label="${2}" payload="${3}"
    mkudffs --media-type=hd --bootarea=erase --udfrev=0x0201 \
        --label="${label}" "${device}"
    populate_mounted "${device}" udf "${payload}"
    return 0
}

# Ships empty, and that is the whole truth available here: there is no APFS
# writer on Linux. mkapfs makes an empty container and apfs-fuse is read-only.
# The row still earns its place, because what plan_mount decides about apfs is
# which helper to reach for, and the signature alone exercises that.
make_apfs(){
    local device="${1}" label="${2}"
    mkapfs -L "${label}" "${device}"
    return 0
}

make_squashfs(){
    local device="${1}" label="${2}" payload="${3}"
    local source image="${WORK_DIR}/p${4}.sqfs"

    source=$(payload_dir "${payload}")
    mksquashfs "${source}" "${image}" -noappend -all-root -no-progress
    write_image "${image}" "${device}"
    : "${label}"
    return 0
}

make_erofs(){
    local device="${1}" label="${2}" payload="${3}"
    local source image="${WORK_DIR}/p${4}.erofs"

    source=$(payload_dir "${payload}")
    mkfs.erofs "${image}" "${source}"
    write_image "${image}" "${device}"
    : "${label}"
    return 0
}

# -3 because v1 and v2 cap a filename at 30 characters. Ships empty: the
# appliance refuses minix either way, so its contents would never be read, and
# what this row tests is that the refusal says the right thing.
make_minix(){
    local device="${1}"
    mkfs.minix -3 "${device}"
    return 0
}

make_luks(){
    local device="${1}"
    printf '%s' "${LUKS_PASSPHRASE}" |
        cryptsetup luksFormat --type luks2 --pbkdf pbkdf2 \
            --pbkdf-force-iterations 1000 --batch-mode "${device}" -
    return 0
}

# A pool cannot be created here: importing one needs the ZFS kernel module, and
# a NixOS host routinely runs a kernel ZFS does not support yet. The fixture is
# 256 KiB captured once from a real vdev label built by `ztest`, which runs
# libzpool entirely in userland. libblkid reads label L0 at offset 16384, which
# is inside those 256 KiB and at a fixed position, so the copy is sufficient on
# its own -- see nixos/README.md for how it was made.
make_zfs(){
    local device="${1}"

    if [[ ! -f "${ZFS_FIXTURE}" ]]; then
        echo "missing ZFS label fixture: ${ZFS_FIXTURE}" >&2
        return 1
    fi

    dd if="${ZFS_FIXTURE}" of="${device}" bs=256K count=1 conv=fsync status=none
    return 0
}

# pvcreate rather than hand-written bytes: probe_lvm2 checks a CRC over the
# label, and writing it by hand means reimplementing lvm2_calc_crc. A physical
# volume in no volume group is inert; nothing will activate it.
make_lvm(){
    local device="${1}"
    pvcreate -ff -y "${device}" > /dev/null
    return 0
}

# Metadata 1.2 deliberately: its superblock sits at a fixed offset 0x1000,
# whereas 1.0 lives at the end of the device and would move if the partition
# were ever resized. --stop afterwards, or mdadm holds the partition open.
make_mdraid(){
    local device="${1}"
    local array="/dev/md/loom-fstest"
    local image="${WORK_DIR}/p23-mdraid.img"
    local size loop status=0

    # mdadm normally autoloads these, but it needs modprobe on PATH to do it and
    # under sudo that is not a given.
    modprobe md_mod > /dev/null 2>&1 || true
    modprobe raid1 > /dev/null 2>&1 || true

    # The superblock is built on a loop device and copied across, rather than
    # mdadm being pointed at the stick. mdadm opens its member O_EXCL, which the
    # mkfs tools do not, and on a USB stick that has just had 26 partitions
    # written to it something is reliably holding this one open -- udev, udisks,
    # whatever the desktop runs -- so the create aborts with "Device or resource
    # busy" however long it waits. A loop device has no such audience.
    #
    # The copy is exact, not an approximation: a 1.2 superblock lives at a fixed
    # offset 4096 with `super_offset` recorded as 8 sectors, and the loop file is
    # created at the partition's own size, so every size field matches the
    # partition it lands on. RAID1 at this size gets no write-intent bitmap, so
    # the first mebibyte covers all of it.
    size=$(blockdev --getsize64 "${device}")
    truncate --size="${size}" "${image}"

    loop=$(losetup --find --show "${image}")

    mdadm --create "${array}" --level=1 --raid-devices=2 --metadata=1.2 \
        --assume-clean --name=LOOM23RAID --run "${loop}" missing || status=$?

    if [[ "${status}" -eq 0 ]]; then
        mdadm --stop "${array}" > /dev/null 2>&1 || true
    fi

    losetup --detach "${loop}" || true

    if [[ "${status}" -ne 0 ]]; then
        echo "mdadm could not create the array on ${loop}" >&2
        return 1
    fi

    dd if="${image}" of="${device}" bs=1M count=1 conv=fsync status=none
    blockdev --flushbufs "${device}" > /dev/null 2>&1 || true
    return 0
}

make_swap(){
    local device="${1}" label="${2}"
    mkswap --label "${label}" "${device}" > /dev/null
    return 0
}

# No Linux tool creates one. libblkid's bitlocker prober reads 11 bytes at
# offset 0 and, for the Vista form, stops there -- no FVE metadata is consulted
# -- so these eleven bytes on an otherwise zeroed partition are the whole
# recipe. The prober runs ahead of vfat and carries BLKID_USAGE_CRYPTO, so
# safeprobe breaks on it immediately and nothing can shadow it.
make_bitlocker(){
    local device="${1}"
    printf '\xeb\x52\x90-FVE-FS-' |
        dd of="${device}" bs=1 seek=0 conv=notrunc,fsync status=none
    return 0
}

# Deliberately signature-free, to exercise plan_mount's "no recognisable
# filesystem" branch.
make_blank(){
    local device="${1}"
    blank_partition "${device}"
    return 0
}

report_result(){
    local row number short size want label payload maker partlabel pick
    local status

    FAILURES=0
    echo
    printf '%-4s %-22s %-8s %s\n' "#" "PARTLABEL" "STATUS" "DETAIL"
    for row in "${ROWS[@]}"; do
        IFS='|' read -r number short size want label payload maker <<< "${row}"
        pick=$(is_selected "${number}")
        [[ "${pick}" == true ]] || continue

        printf -v partlabel 'fstest%02d-%s' "${number}" "${short}"
        status="${ROW_STATUS[${number}]:-skipped}"
        [[ "${status}" == "ok" ]] || FAILURES=$(( FAILURES + 1 ))
        printf '%-4s %-22s %-8s %s\n' \
            "${number}" "${partlabel}" "${status}" "${ROW_DETAIL[${number}]:-}"
    done
    echo

    if [[ "${FAILURES}" -gt 0 ]]; then
        warn "${FAILURES} partition(s) did not come out as intended; they have been blanked."
        warn "Each one's full mkfs output is in ${WORK_DIR}/p<n>.log, kept for that reason."
        warn "Re-run with --only <n> once the cause is fixed."
        return 1
    fi

    log "All partitions written and identified."
    return 0
}

# Taken only once the run is committed to writing, and only after preflight has
# established that we are root: a lock acquired before that is a lock a non-root
# invocation can leave behind.
acquire_lock(){
    local directory
    directory=$(dirname "${LOCK_FILE}")
    if [[ ! -d "${directory}" ]]; then
        LOCK_FILE="${TMPDIR:-/tmp}/loom-ingest-test-stick.lock"
    fi

    exec 9> "${LOCK_FILE}"
    if ! flock --nonblock 9; then
        die "Another build holds ${LOCK_FILE}"
    fi
    return 0
}

# Unmount everything this run is responsible for, however it exits.
#
# Two sources. The script's own mountpoint is a single path reused by every row,
# so a row that died between mount and umount left it mounted and the next row
# stacked another mount on top -- hence the loop rather than one umount. The
# second is the stick's own partitions: creating 26 filesystems makes a desktop
# automounter attach whatever it recognises, and leaving a tray full of them
# behind is not this script's idea of finishing.
release_mounts(){
    local row number path node targets target

    if [[ -n "${WORK_DIR}" && -d "${WORK_DIR}/mnt" ]]; then
        while mountpoint -q "${WORK_DIR}/mnt"; do
            umount "${WORK_DIR}/mnt" > /dev/null 2>&1 ||
                umount --lazy "${WORK_DIR}/mnt" > /dev/null 2>&1 ||
                break
        done
    fi

    [[ -n "${DEVICE}" ]] || return 0

    for row in "${ROWS[@]}"; do
        number=${row%%|*}
        path=$(partition_path "${number}")
        [[ -e "${path}" ]] || continue

        node=$(readlink -f "${path}")
        targets=$(findmnt --noheadings --output TARGET --list --source "${node}" 2>/dev/null || true)
        [[ -n "${targets}" ]] || continue

        while IFS= read -r target; do
            [[ -n "${target}" ]] || continue
            log "Unmounting ${target} (${node})"
            umount "${target}" > /dev/null 2>&1 ||
                umount --lazy "${target}" > /dev/null 2>&1 ||
                warn "Could not unmount ${target}"
        done <<< "${targets}"
    done
    return 0
}

cleanup(){
    release_mounts

    [[ -n "${WORK_DIR}" && -d "${WORK_DIR}" ]] || return 0

    if [[ "${KEEP_WORK}" == true || "${FAILURES}" -gt 0 ]]; then
        log "Work directory kept at ${WORK_DIR}"
        log "Per-partition logs: ${WORK_DIR}/p<n>.log"
    else
        rm -rf "${WORK_DIR}"
    fi
    return 0
}

main(){
    parse_arguments "$@"
    require_tools
    preflight
    report_plan

    if [[ "${CONSENT}" != "${DEVICE_SERIAL}" ]]; then
        if [[ -n "${CONSENT}" ]]; then
            die "--i-know-this-erases says '${CONSENT}', this stick's serial is '${DEVICE_SERIAL}'"
        fi
        log "Nothing written. Pass --i-know-this-erases ${DEVICE_SERIAL} to build it."
        return 0
    fi

    # Armed before anything is mounted, and before the work directory exists, so
    # that an exit anywhere past this point still unmounts what it left behind.
    trap cleanup EXIT

    acquire_lock
    WORK_DIR=$(mktemp -d -t ingest-test-stick.XXXXXX)

    stage_payloads

    if [[ -z "${ONLY}" && -z "${EXCLUDE}" ]]; then
        partition_disk
    else
        log "Keeping the existing partition table (--only/--skip given)"
        settle_partitions
    fi

    format_rows
    report_result
    return 0
}

main "$@"
