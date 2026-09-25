#!/usr/bin/env bash
# Boots a Loom appliance in a VM, for the testing a human does by hand.
#
# The automated suite under nixos/tests/ answers questions that can be written
# down in advance. This answers the other kind -- what the console session
# actually looks like, whether the installer menu reads the way it should, what
# happens when you pull the key stick -- and it does it on a workstation with no
# appliance hardware anywhere near it.
#
# Two VMs, because there are two different questions:
#
#   box        The appliance closure under nixpkgs' own qemu-vm runner. Boots in
#              about a minute and gives you everything above the disk: the
#              console session, the branding, the units, the banner. Needs no
#              tag and no image build, so it is the loop to iterate in.
#
#              What it cannot show you is everything below the disk. qemu-vm
#              replaces `fileSystems` wholesale and clears
#              `boot.initrd.luks.devices` (both `mkVMOverride`), so the LUKS
#              root, the partlabel mounts, systemd-boot and the boot menu are
#              all out of frame.
#
#   installer  The real stick image, virtually flashed, booted under UEFI
#              against emulated NVMe. This is the one the test suite cannot be:
#              tests/appliance-install.nix says outright that the image "is
#              deliberately not booted. It wants an NVMe the test framework
#              cannot supply". qemu can supply one -- `target_disks`
#              (installer/loom_installer/devices.py) wants /dev/nvmeXn1, non-removable
#              and not the boot disk, and `-device nvme` plus the stick on
#              usb-storage satisfies all three.
#
#              So this boots the stick, runs the real installer onto a real
#              pool, reboots into what it installed, and unlocks it from the key
#              partition on the stick -- persistently, across runs.
#
# Neither VM runs Loom. up.sh wants docker, minikube and ~60 GB of container
# images, and setup mode wants the internet to fetch them; that is an afternoon
# and a very large host, not a manual test. `box --start-loom` leaves the unit
# wanted for the one case where watching it fail is the point.
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)

# As in cicd/run_appliance_tests.sh: the pinned sources come from devenv's
# inputs, so devenv.lock stays the only nixpkgs pin in this repository.
NIXPKGS=""
NIXOS_HARDWARE=""

# The UEFI firmware directory, passed by the devenv script from `pkgs.OVMF.fd`.
# Only the installer rig needs it -- the box VM boots its kernel directly
# through nixpkgs' runner, with no firmware in the picture at all.
FIRMWARE_DIR=""

# Which box to build for. Defaults to whichever platform matches this machine,
# for the same reason the VM tests do: a VM boots a real kernel, so a
# cross-built one cannot run here.
PLATFORM=""
KNOWN_PLATFORMS=(spark evo-x2 nuc12)
NIX_SYSTEM=""
HOST_ARCH=""

MODE=""
KNOWN_MODES=(box installer attach reset)

# Where the qcow2 disks, the flashed stick, the firmware variables and the two
# sockets live. Per platform, and per --serial, because an image built with the
# serial getty is a different image and reusing one pool of disks for both would
# make "which one am I looking at" unanswerable.
STATE_ROOT="${CONTEXT_DIR}/.appliance-vm"
STATE_DIR=""
# Both derived from STATE_DIR in prepare_state_dir, and kept as variables rather
# than computed where they are used: a `$(...)` inside an `echo` masks the
# command's exit status, which shellcheck's `-o all` rightly refuses.
SERIAL_SOCKET=""
MONITOR_SOCKET=""

# Add a getty on ttyS0 to the image the rig boots. Off by default: it is one
# unit more than a real stick carries, and the rig exists to boot the real
# thing. See nixos/vm-serial.nix for why this is a getty and not a `console=`.
#
# The box VM always has it -- nixos/vm.nix imports the same module -- because
# nixpkgs' runner already puts `console=ttyS0 console=tty0` on the command line
# there, so the serial port is not a deviation to begin with.
SERIAL=false

GUI=true

# Generous, because the appliance closure is not small and the installer copies
# all of it. Neither number is load-bearing; both are flags.
MEMORY_MB=8192
CORES=4

# Two disks rather than one, so the run exercises the pooling path -- an
# installer that silently formed a volume group over one disk and left the
# second unused looks, from the console, exactly like a working install
# (tests/appliance-install.nix).
#
# 200 GB each because `check_pool_size` (installer/loom_installer/install.py) wants 250
# GB across the pool and refuses to install below it. It costs nothing: a qcow2
# takes what the guest writes, which for a full install is a few gigabytes.
DISK_COUNT=2
DISK_SIZE="200G"

# An extra USB stick, made from a directory. For watching what usb-ingest.nix
# decides about a filesystem it has never seen.
USB_DIR=""

START_LOOM=false
TAG=""

# Build the box VM with nixos/debug.nix on, generate a keypair for it, and
# forward the guest's 22 to a host port. `box` only: the installer rig boots the
# stick image, and a debug stick is what `build-appliance-image --debug` makes.
#
# This is the cheap way to use the feature -- a minute, no tag, no image build,
# and something an agent can ssh into. It is also the only way to try --debug
# without dedicating a box to it.
DEBUG_ACCESS=false
DEBUG_KEY_DIR=""
# The host port forwarded to the guest's sshd. Must agree with the
# `ssh_config.vm` that cicd/build_appliance_image.sh writes, which names 2222
# for exactly this rig.
DEBUG_SSH_PORT=2222

# The appliance's operator account. Must agree with `loomUser` in
# nixos/default.nix and with LOOM_USER in cicd/build_appliance_image.sh.
LOOM_USER="loom"

FORCE=false
VERBOSE=false

# As run_appliance_tests.sh: let the daemon collect garbage rather than fail the
# build when the store fills up. See the disk budget section in nixos/README.md.
MIN_FREE_GB=25
MAX_FREE_GB=100

# variables defined in vars.sh, here for shellcheck:
LOOM_HOSTS_FQDN=()
NAMESPACE=""
LOOM_CHAT_MODEL=""

LOOM_HOSTS_JSON=""

# Resolved in validate_environment, once.
USE_KVM=false

#
# Helpers
#

check_command(){
    if ! command -v "${1}" > /dev/null; then
        echo >&2 "[!] Error: required command not found: ${1}"
        exit 1
    fi
}

# Must agree with `platform_system` in cicd/build_appliance_image.sh and with
# `nixSystem` in nixos/platforms/<id>.nix. nixos/default.nix asserts the last
# pair, so a drift here fails during evaluation rather than on the box.
platform_system(){
    case "${1}" in
        spark)  printf 'aarch64-linux' ;;
        evo-x2) printf 'x86_64-linux'  ;;
        nuc12)  printf 'x86_64-linux'  ;;
        *)      return 1               ;;
    esac
}

qemu_binary(){
    case "${1}" in
        aarch64-linux) printf 'qemu-system-aarch64' ;;
        x86_64-linux)  printf 'qemu-system-x86_64'  ;;
        *)             return 1                     ;;
    esac
}

qemu_machine(){
    case "${1}" in
        aarch64-linux) printf 'virt' ;;
        x86_64-linux)  printf 'q35'  ;;
        *)             return 1      ;;
    esac
}

#
# Steps
#

validate_environment(){
    local command free_gb store_dir

    for command in git nix-build jq; do
        check_command "${command}"
    done

    if [[ -z "${NIXPKGS}" ]]; then
        echo >&2 "[!] Error: no nixpkgs given."
        echo >&2 "    Run this through devenv: 'appliance-vm' passes --nixpkgs for you."
        exit 1
    fi
    if [[ ! -e "${NIXPKGS}/nixos/lib/eval-config.nix" ]]; then
        echo >&2 "[!] Error: not a nixpkgs source: ${NIXPKGS}"
        exit 1
    fi

    if [[ -z "${NIXOS_HARDWARE}" ]]; then
        echo >&2 "[!] Error: no nixos-hardware given."
        echo >&2 "    Run this through devenv: 'appliance-vm' passes --nixos-hardware for you."
        exit 1
    fi
    if [[ ! -e "${NIXOS_HARDWARE}/common/pc/ssd/default.nix" ]]; then
        echo >&2 "[!] Error: not a nixos-hardware source: ${NIXOS_HARDWARE}"
        exit 1
    fi

    # No --allow-cross to go with build-appliance-image's, and for the reason
    # run_appliance_tests.sh gives: an image can be built under emulation and
    # flashed, but a VM has to boot the kernel it built.
    if [[ "${NIX_SYSTEM}" != "${HOST_ARCH}-linux" ]]; then
        echo >&2 "[!] Error: platform '${PLATFORM}' is ${NIX_SYSTEM}, but this host is ${HOST_ARCH}."
        echo >&2 "    A VM boots a real kernel, so it cannot be cross-built. Run this on a"
        echo >&2 "    ${NIX_SYSTEM} host, or pass --platform for one that matches this machine."
        exit 1
    fi

    # Read *and* write, because that is what qemu needs to open the device.
    # Unlike the test suite this is only a note: qemu is started with
    # `accel=kvm:tcg` below, so it falls back to emulation on its own.
    if [[ -r /dev/kvm && -w /dev/kvm ]]; then
        USE_KVM=true
    else
        USE_KVM=false
        echo "[!] Note: /dev/kvm is not usable here, so qemu falls back to software"
        echo "[!] emulation. Expect a boot to take minutes rather than seconds."
    fi

    store_dir="${NIX_STORE_DIR:-/nix/store}"
    free_gb="$(df --block-size=1G --output=avail "${store_dir}" | tail --lines=1 | tr --delete ' ')"
    if (( free_gb < 15 )); then
        echo "[!] Note: ${free_gb} GB free on the filesystem holding ${store_dir}. A run builds"
        echo "[!] a ~3.5 GB appliance closure, and the installer rig copies the image beside it."
        echo "[!] 'nix-collect-garbage -d' and 'nix store optimise' free what earlier runs left."
    fi
}

# Sourced from this checkout, which is also what the VM embeds, so the two
# cannot disagree. Same three values run_appliance_tests.sh resolves, for the
# same reason: box.nix restates them and tests/appliance.nix asserts it did so
# correctly, and passing defaults here would put a different box in the VM from
# the one on the stick.
resolve_loom_values(){
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${CONTEXT_DIR}/vars.sh"
    LOOM_HOSTS_JSON="$(printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" |
        jq --raw-input . | jq --slurp --compact-output .)"
}

prepare_state_dir(){
    if [[ "${SERIAL}" = true ]]; then
        STATE_DIR="${STATE_ROOT}/${PLATFORM}-serial"
    else
        STATE_DIR="${STATE_ROOT}/${PLATFORM}"
    fi

    SERIAL_SOCKET="${STATE_DIR}/serial.sock"
    MONITOR_SOCKET="${STATE_DIR}/monitor.sock"

    # A unix socket path lives in `sockaddr_un.sun_path`, which is 108 bytes on
    # Linux and is not negotiable. qemu's own message for this names the limit
    # but not the way out, and the way out is not obvious: the offending path is
    # one this script chose, inside a checkout whose depth the operator picked
    # long ago. Say so here, before a VM has been built for it.
    if (( ${#MONITOR_SOCKET} >= 108 )); then
        echo >&2 "[!] Error: the socket path is ${#MONITOR_SOCKET} bytes, and a unix socket allows 107:"
        echo >&2 "      ${MONITOR_SOCKET}"
        echo >&2 "    This checkout is too deep for the state directory to live inside it."
        echo >&2 "    Point --state-root somewhere shorter, e.g. --state-root /tmp/loom-vm."
        exit 1
    fi

    # `attach` and `reset` only ever look at a directory somebody else made.
    # Creating one for them would have `reset` report on, and then delete, a
    # directory it had just created itself.
    if [[ "${MODE}" = attach || "${MODE}" = reset ]]; then
        return 0
    fi
    mkdir --parents "${STATE_DIR}"
}

#
# box
#

# The key this VM's sshd accepts, kept in the state directory rather than in a
# fresh temp dir per run.
#
# That is the one real difference from cicd/build_appliance_image.sh's step of
# the same name, and it is deliberate: a stick is built once and debugged from
# whatever the build printed, while this rig gets re-run a dozen times in an
# afternoon. A key that changed every run would invalidate the ssh_config path
# the operator -- or the agent -- had already been given, and would leave a
# directory in /tmp behind each time. Here it is reused, and `appliance-vm
# reset` deletes it along with the disks, which is what an operator already
# expects that subcommand to mean.
resolve_debug_key(){
    if [[ "${DEBUG_ACCESS}" != true ]]; then
        return
    fi

    check_command ssh-keygen

    DEBUG_KEY_DIR="${STATE_DIR}/debug"
    mkdir --parents "${DEBUG_KEY_DIR}"
    chmod 0700 "${DEBUG_KEY_DIR}"

    if [[ ! -f "${DEBUG_KEY_DIR}/id_ed25519" ]]; then
        echo "[*] Generating a debug keypair for this VM: ${DEBUG_KEY_DIR}"
        ssh-keygen -t ed25519 -N '' -q \
            -C "loom-appliance-debug vm ${PLATFORM}" \
            -f "${DEBUG_KEY_DIR}/id_ed25519"
    fi

    # Rewritten every run rather than only alongside the key: the port and the
    # paths in it depend on this script's variables, and a stale config that
    # names a port nothing is listening on is worse than none.
    #
    # `accept-new` with a known_hosts of its own, for the reasons
    # cicd/build_appliance_image.sh gives at greater length. On this rig it also
    # covers the case that makes localhost forwarding annoying: the guest gets a
    # new host key whenever the closure changes, and a shared known_hosts would
    # refuse the connection with a warning about a man in the middle.
    : > "${DEBUG_KEY_DIR}/known_hosts"
    chmod 0600 "${DEBUG_KEY_DIR}/known_hosts"

    cat > "${DEBUG_KEY_DIR}/ssh_config" <<EOF
# Generated by cicd/run_appliance_vm.sh for the ${PLATFORM} box VM.
#
# Use it with:  ssh -F ${DEBUG_KEY_DIR}/ssh_config loom-appliance
# Deleted by:   appliance-vm reset --platform ${PLATFORM}
Host loom-appliance
    HostName localhost
    Port ${DEBUG_SSH_PORT}
    User ${LOOM_USER}
    IdentityFile ${DEBUG_KEY_DIR}/id_ed25519
    IdentitiesOnly yes
    UserKnownHostsFile ${DEBUG_KEY_DIR}/known_hosts
    StrictHostKeyChecking accept-new
EOF
    chmod 0600 "${DEBUG_KEY_DIR}/ssh_config"
}

build_box_vm(){
    local debug_key=''
    if [[ "${DEBUG_ACCESS}" = true ]]; then
        debug_key="$(cat "${DEBUG_KEY_DIR}/id_ed25519.pub")"
    fi

    local args=(
        "${CONTEXT_DIR}/nixos"
        --attr boxVm
        --arg nixpkgs "${NIXPKGS}"
        --arg nixosHardware "${NIXOS_HARDWARE}"
        --argstr system "${NIX_SYSTEM}"
        --argstr platform "${PLATFORM}"
        # The working tree, filtered by `loomSrc` in nixos/default.nix. No
        # tagged clone: this VM never starts Loom, so nothing in it runs the
        # `git describe --exact-match --tags HEAD` that up.sh's offline mode
        # needs. That is what lets `box` run on an untagged branch.
        --arg repoSrc "${CONTEXT_DIR}"
        --argstr tag "${TAG:-dev}"
        --argstr loomHostsJson "${LOOM_HOSTS_JSON}"
        --argstr loomNamespace "${NAMESPACE}"
        --argstr loomChatModel "${LOOM_CHAT_MODEL}"
        --arg startLoom "${START_LOOM}"
        --arg debugAccess "${DEBUG_ACCESS}"
        --argstr debugSshAuthorizedKey "${debug_key}"
        --out-link "${STATE_DIR}/boxvm"
    )
    if (( MIN_FREE_GB > 0 )); then
        args+=(
            --option min-free "$(( MIN_FREE_GB * 1024 * 1024 * 1024 ))"
            --option max-free "$(( MAX_FREE_GB * 1024 * 1024 * 1024 ))"
        )
    fi
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--show-trace)
    fi

    echo "[*] Building the ${PLATFORM} (${NIX_SYSTEM}) box VM"
    nix-build "${args[@]}"
}

run_box_vm(){
    local runner qemu_opts qemu_net_opts=''

    # nixpkgs' runner builds its own `-netdev user,id=user.0,${QEMU_NET_OPTS}`,
    # so a forward goes in through that variable rather than through QEMU_OPTS
    # below -- a second `-netdev` would be a second NIC, not a forward on the
    # one that exists.
    #
    # Only with --debug. An unconditional forward would bind a host port on
    # every `appliance-vm box` run, including the ones with no sshd behind it,
    # and a second VM started alongside would then fail on the bind rather than
    # on anything to do with the appliance.
    if [[ "${DEBUG_ACCESS}" = true ]]; then
        qemu_net_opts="hostfwd=tcp::${DEBUG_SSH_PORT}-:22"
    fi

    runner="$(find -L "${STATE_DIR}/boxvm/bin" -name 'run-*-vm' -type f | head --lines=1)"
    if [[ -z "${runner}" ]]; then
        echo >&2 "[!] Error: no runner script under ${STATE_DIR}/boxvm/bin."
        exit 1
    fi

    # nixpkgs' runner passes no -serial of its own when graphics are on, so this
    # becomes ttyS0 -- which is exactly where vm-serial.nix put its getty, and
    # where `virtualisation.qemu.consoles` is already copying the boot log.
    qemu_opts="-serial unix:${SERIAL_SOCKET},server=on,wait=off"
    qemu_opts+=" -monitor unix:${MONITOR_SOCKET},server=on,wait=off"
    if [[ "${GUI}" = false ]]; then
        qemu_opts+=" -display none"
    fi

    # A RELATIVE mouse, because the appliance's pointer cannot use the absolute
    # one nixpkgs gives it.
    #
    # nixpkgs' qemu-vm module adds `-usb -device usb-tablet` on x86
    # unconditionally, and a tablet reports absolute positions. gpm reads
    # /dev/input/mice, where the kernel's mousedev has already converted those
    # into relative deltas against a fixed 1024x768 grid
    # (CONFIG_INPUT_MOUSEDEV_SCREEN_X/Y) -- and gpm then integrates the deltas
    # back into an absolute position of its own, with acceleration applied on
    # top. The two accumulators drift apart as soon as anything is dropped or
    # clamped at an edge, and the symptom is a pointer that tracks roughly but
    # cannot be driven into the corners.
    #
    # The tablet cannot be removed from here -- it comes from a list inside the
    # closure -- so a relative device is added beside it. qemu routes motion to
    # the tablet while the pointer is free and to this one while the window
    # holds a grab, so `Ctrl-Alt-G` is what selects it. `appliance-vm` prints
    # that below, because nothing about it is guessable.
    qemu_opts+=" -device usb-mouse,bus=usb-bus.0,id=loommouse"

    report_endpoints

    # NIX_DISK_IMAGE is what makes the VM survive a reboot: without it the
    # runner writes its root into $TMPDIR and throws it away on exit.
    NIX_DISK_IMAGE="${STATE_DIR}/box.qcow2" \
    QEMU_NET_OPTS="${qemu_net_opts}" \
    QEMU_OPTS="${qemu_opts}" \
        exec "${runner}"
}

#
# installer
#

build_installer_image(){
    local args=(
        --nixpkgs "${NIXPKGS}"
        --nixos-hardware "${NIXOS_HARDWARE}"
        --platform "${PLATFORM}"
        --output "${STATE_DIR}/build"
        # The rig is not a stick and never asks which tag to use interactively:
        # it is re-run constantly, and a prompt in the middle of that is noise.
        --yes
    )
    if [[ -n "${TAG}" ]]; then
        args+=(--tag "${TAG}")
    fi
    if [[ "${SERIAL}" = true ]]; then
        args+=(--vm-serial)
    fi
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--verbose)
    fi

    "${CONTEXT_DIR}/cicd/build_appliance_image.sh" "${args[@]}"
}

image_file(){
    # -L: the out-link is a symlink into the store, and find does not follow
    # symlinks by default. Same helper build_appliance_image.sh uses.
    find -L "${STATE_DIR}/build/appliance-image" -name '*.raw' -type f | head --lines=1
}

# The flash, onto a file.
#
# Exactly the two steps build_appliance_image.sh performs on a real stick --
# write the image, then write 4096 bytes of key into the `loom-key` partition --
# and neither needs root here, because `sfdisk --json` reads a partition table
# out of an ordinary file and `dd seek=` writes back into one. The result is
# structurally identical to a flashed stick, which is what makes the key guard
# and stage 1 behave in here the way they behave on the box.
virtual_flash(){
    local image stick offset sectors

    stick="${STATE_DIR}/stick.raw"
    if [[ -e "${stick}" && "${FORCE}" = false ]]; then
        echo "[*] Keeping the stick already in ${STATE_DIR} (--force reflashes it)"
        return 0
    fi

    image="$(image_file)"
    if [[ -z "${image}" ]]; then
        echo >&2 "[!] Error: no image under ${STATE_DIR}/build/appliance-image."
        exit 1
    fi

    echo "[*] Flashing $(basename "${image}") onto ${stick}"
    # --reflink=auto is free on btrfs and xfs and a plain copy everywhere else.
    cp --reflink=auto --force "${image}" "${stick}"
    # The store is read-only and cp preserves that.
    chmod u+w "${stick}"

    # `start` is in 512-byte sectors, which is also what the key size has to be
    # expressed in: 4096 bytes is 8 of them. KEY_BYTES in
    # build_appliance_image.sh and `boot.initrd.luks.devices.*.keyFileSize` in
    # box-hardware.nix are the same number.
    offset="$(sfdisk --json "${stick}" |
        jq --raw-output '.partitiontable.partitions[] | select(.name == "loom-key") | .start')"
    if [[ -z "${offset}" || "${offset}" = "null" ]]; then
        echo >&2 "[!] Error: no 'loom-key' partition in ${stick}."
        echo >&2 "    The image is not a Loom appliance stick, or installer.nix stopped making one."
        exit 1
    fi
    sectors=8

    echo "[*] Writing the LUKS key at sector ${offset}"
    dd if=/dev/urandom of="${stick}" bs=512 seek="${offset}" count="${sectors}" \
        conv=notrunc,fsync status=none

    # Not backed up anywhere, deliberately, and unlike a real stick that is
    # fine: this key unlocks a qcow2 in a scratch directory. `--reset` throws
    # the pair away together.
}

create_disks(){
    local index disk

    for (( index = 0; index < DISK_COUNT; index++ )); do
        disk="${STATE_DIR}/nvme${index}.qcow2"
        if [[ -e "${disk}" ]]; then
            continue
        fi
        echo "[*] Creating ${disk} (${DISK_SIZE}, sparse)"
        qemu-img create -f qcow2 "${disk}" "${DISK_SIZE}" > /dev/null
    done
}

# A vfat stick built from a directory, without root and without mounting
# anything: mkfs.vfat makes the filesystem in a file and mcopy writes into it.
create_usb_stick(){
    local image size_kb

    if [[ -z "${USB_DIR}" ]]; then
        return 0
    fi
    if [[ ! -d "${USB_DIR}" ]]; then
        echo >&2 "[!] Error: not a directory: ${USB_DIR}"
        exit 1
    fi

    image="${STATE_DIR}/usb.img"
    # The payload plus 64 MB of slack, which covers the FAT itself and keeps a
    # small directory from producing a filesystem mkfs.vfat refuses to make.
    size_kb="$(du --summarize --block-size=1K "${USB_DIR}" | cut --fields=1)"
    size_kb=$(( size_kb + 65536 ))

    echo "[*] Building ${image} from ${USB_DIR}"
    rm --force "${image}"
    truncate --size="${size_kb}K" "${image}"
    mkfs.vfat -n LOOMDATA "${image}" > /dev/null
    # `::` is mtools for the root of the image. The glob is deliberate: mcopy
    # cannot copy a directory onto itself as the root.
    mcopy -s -i "${image}" "${USB_DIR}"/* :: 2>/dev/null || true
}

prepare_firmware(){
    local code vars

    if [[ -z "${FIRMWARE_DIR}" ]]; then
        echo >&2 "[!] Error: no UEFI firmware given."
        echo >&2 "    Run this through devenv: 'appliance-vm' passes --firmware for you."
        exit 1
    fi

    # nixpkgs names these per architecture. Probe rather than map, so a rename
    # upstream produces a list of what is actually there.
    for code in OVMF_CODE.fd AAVMF_CODE.fd; do
        if [[ -e "${FIRMWARE_DIR}/${code}" ]]; then
            FIRMWARE_CODE="${FIRMWARE_DIR}/${code}"
        fi
    done
    for vars in OVMF_VARS.fd AAVMF_VARS.fd; do
        if [[ -e "${FIRMWARE_DIR}/${vars}" ]]; then
            FIRMWARE_VARS_SRC="${FIRMWARE_DIR}/${vars}"
        fi
    done

    if [[ -z "${FIRMWARE_CODE:-}" || -z "${FIRMWARE_VARS_SRC:-}" ]]; then
        echo >&2 "[!] Error: no UEFI firmware in ${FIRMWARE_DIR}. Found:"
        ls >&2 "${FIRMWARE_DIR}"
        exit 1
    fi

    # A writable copy per state directory, and the reason the rig can test
    # anything about booting at all: `fix_boot_order` (the installer's
    # install.py) writes a `Loom appliance` entry into EFI variables, and a
    # firmware whose variables were thrown away between runs would lose it
    # every time.
    FIRMWARE_VARS="${STATE_DIR}/efi-vars.fd"
    if [[ ! -e "${FIRMWARE_VARS}" ]]; then
        cp "${FIRMWARE_VARS_SRC}" "${FIRMWARE_VARS}"
        chmod u+w "${FIRMWARE_VARS}"
    fi
}

run_installer_vm(){
    local binary machine accel index
    local args=()

    binary="$(qemu_binary "${NIX_SYSTEM}")"
    machine="$(qemu_machine "${NIX_SYSTEM}")"
    check_command "${binary}"

    # kvm:tcg rather than one or the other, which is what nixpkgs' own test
    # driver does: qemu takes the first accelerator it can open and falls back
    # to emulation by itself.
    accel="kvm:tcg"

    args+=(-machine "${machine},accel=${accel}")
    if [[ "${USE_KVM}" = true ]]; then
        args+=(-cpu host)
    else
        args+=(-cpu max)
    fi
    args+=(-smp "${CORES}" -m "${MEMORY_MB}")

    # readonly=on on the code half, writable on the variables half. Splitting
    # them is what lets the firmware keep its boot entries without the build
    # ever writing into the store.
    args+=(
        -drive "if=pflash,format=raw,unit=0,readonly=on,file=${FIRMWARE_CODE}"
        -drive "if=pflash,format=raw,unit=1,file=${FIRMWARE_VARS}"
    )

    # The stick, on USB, because that is what the installer looks for: it
    # installs onto every internal NVMe that is not the disk it booted from, and
    # `boot_disk` resolves through the medium it is running on.
    args+=(
        -device "qemu-xhci,id=xhci"
        -drive "if=none,id=stick,format=raw,file=${STATE_DIR}/stick.raw"
        -device "usb-storage,bus=xhci.0,drive=stick,id=loomstick"
    )

    # A mouse, so the console session can be driven the way it is meant to be.
    #
    # usb-mouse rather than usb-tablet, and the difference matters here: a
    # tablet reports absolute coordinates against a screen the guest cannot
    # see, while gpm reads /dev/input/mice and tracks a position from relative
    # motion. The `box` target inherits a tablet from nixpkgs' qemu-vm module
    # and is the worse of the two to aim with for exactly that reason.
    args+=(
        -device "usb-mouse,bus=xhci.0,id=loommouse"
    )

    # No bootindex anywhere, on purpose. Setting one writes a boot order into
    # fw_cfg, which OVMF re-applies on every boot and which would therefore
    # overrule the NVRAM entry `fix_boot_order` creates at install time -- the
    # one thing about booting this rig is here to check. OVMF finds the stick on
    # its own while it is the only bootable thing attached, and honours the
    # installed entry afterwards. Press ESC at the splash for the firmware's own
    # boot menu if it ever picks wrong.
    for (( index = 0; index < DISK_COUNT; index++ )); do
        args+=(
            -drive "if=none,id=nvme${index},format=qcow2,file=${STATE_DIR}/nvme${index}.qcow2"
            -device "nvme,drive=nvme${index},serial=loomnvme${index}"
        )
    done

    if [[ -n "${USB_DIR}" ]]; then
        args+=(
            -drive "if=none,id=usbdata,format=raw,file=${STATE_DIR}/usb.img"
            -device "usb-storage,bus=xhci.0,drive=usbdata,id=loomdata"
        )
    fi

    # User-mode networking. The appliance serves DHCP and wildcard *.loom on
    # loom0 itself, so this NIC is for the host's benefit rather than the box's:
    # it is what the port forwards below hang off.
    args+=(
        -netdev "user,id=net0,hostfwd=tcp::8443-:443,hostfwd=tcp::8080-:80"
        -device "virtio-net-pci,netdev=net0"
    )

    # The monitor is how the key stick gets pulled without touching the host's
    # USB ports. See report_endpoints.
    args+=(-monitor "unix:${MONITOR_SOCKET},server=on,wait=off")

    if [[ "${SERIAL}" = true ]]; then
        args+=(-serial "unix:${SERIAL_SOCKET},server=on,wait=off")
    fi

    if [[ "${GUI}" = true ]]; then
        args+=(-display "gtk")
    else
        args+=(-display "none")
    fi

    report_endpoints
    exec "${binary}" "${args[@]}"
}

#
# attach / reset
#

attach_serial(){
    local socket
    socket="${SERIAL_SOCKET}"

    check_command socat

    if [[ ! -S "${socket}" ]]; then
        echo >&2 "[!] Error: no serial socket at ${socket}."
        echo >&2 "    Nothing is running for platform '${PLATFORM}', or it was started"
        echo >&2 "    without a serial port. The installer rig needs --serial for one."
        exit 1
    fi

    echo "[*] Attaching to ${socket}. Ctrl-] to leave the terminal alone again;"
    echo "[*] inside the console session, Ctrl-b d detaches tmux and hands tty1 back."
    # raw + echo=0, or the line discipline on both ends would double every
    # keystroke and eat the control characters tmux needs.
    exec socat -,raw,echo=0,escape=0x1d "UNIX-CONNECT:${socket}"
}

reset_state(){
    local answer

    if [[ ! -d "${STATE_DIR}" ]]; then
        echo "[*] Nothing to reset: ${STATE_DIR} does not exist."
        return 0
    fi

    echo "[!] This deletes the installed box, its disks and its key stick:"
    du --summarize --human-readable "${STATE_DIR}"
    if [[ "${FORCE}" != true ]]; then
        read -r -p "[?] Delete ${STATE_DIR}? [y/N] " answer
        if [[ "${answer}" != "y" && "${answer}" != "Y" ]]; then
            echo >&2 "[!] Aborted."
            exit 1
        fi
    fi
    rm --recursive --force "${STATE_DIR}"
    echo "[*] Deleted ${STATE_DIR}"
}

#
# Reporting
#

report_endpoints(){
    local attach_args

    echo
    echo "[*] Booting the ${PLATFORM} (${NIX_SYSTEM}) ${MODE} VM"
    echo "      state     : ${STATE_DIR}"
    echo "      kvm       : ${USE_KVM}"
    echo "      display   : ${GUI}"
    if [[ "${MODE}" = installer ]]; then
        echo "      disks     : ${DISK_COUNT} x ${DISK_SIZE} (sparse)"
        echo "      forwards  : https://localhost:8443  http://localhost:8080"
    fi
    if [[ "${SERIAL}" = true || "${MODE}" = box ]]; then
        attach_args="--platform ${PLATFORM}"
        if [[ "${SERIAL}" = true ]]; then
            attach_args+=" --serial"
        fi
        echo "      serial    : ${SERIAL_SOCKET}"
        echo "      attach    : appliance-vm attach ${attach_args}"
    fi
    echo "      monitor   : ${MONITOR_SOCKET}"
    if [[ "${DEBUG_ACCESS}" = true ]]; then
        echo "      debug ssh : ssh -F ${DEBUG_KEY_DIR}/ssh_config loom-appliance"
        echo "      bundle    : ssh -F ${DEBUG_KEY_DIR}/ssh_config loom-appliance loom-debug-bundle"
        echo
        echo "[!] Built with --debug: this box runs an SSH server and the key above is"
        echo "[!] root on it. Fine for a VM on your own machine, and never the way to"
        echo "[!] build a stick for anybody else -- see 'build-appliance-image --debug'."
    fi
    if [[ "${GUI}" = true ]]; then
        echo
        echo "[*] To drive the console with the mouse, grab the pointer first:"
        echo "      Ctrl-Alt-G  (and again to release)"
        echo "[*] Ungrabbed, qemu feeds an absolute tablet whose motion the"
        echo "[*] appliance's pointer cannot follow accurately -- it tracks, but"
        echo "[*] drifts and will not reach the corners. That is the emulated"
        echo "[*] tablet, not the appliance: real hardware sends relative motion."
    fi
    if [[ "${MODE}" = installer ]]; then
        echo
        echo "[*] Pull the key stick to watch the key guard fire:"
        echo "      socat - UNIX-CONNECT:${MONITOR_SOCKET}"
        echo "      (qemu) device_del loomstick"
        echo "[*] Put it back with:"
        echo "      (qemu) device_add usb-storage,bus=xhci.0,drive=stick,id=loomstick"
    fi
    if [[ "${SERIAL}" = true ]]; then
        echo
        echo "[!] This image carries a getty on ttyS0 that a flashed stick does not."
        echo "[!] It is for copy and paste, and it is one unit of difference from the"
        echo "[!] real thing. Do not judge the shipped image by this one."
    fi
    echo
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>] <${KNOWN_MODES[0]}|${KNOWN_MODES[1]}|${KNOWN_MODES[2]}|${KNOWN_MODES[3]}>"
    echo
    echo "  box         the appliance closure under nixpkgs' qemu-vm runner. Fast, needs no"
    echo "              tag, shows everything above the disk and nothing below it."
    echo "  installer   the real stick image, virtually flashed, booted under UEFI against"
    echo "              emulated NVMe. Installs, reboots and persists across runs."
    echo "  attach      connect to a running VM's serial port (copy and paste live here)"
    echo "  reset       delete this platform's disks, stick and firmware variables"
    echo
    echo "  -h|--help                     show this help"
    echo "  -v|--verbose                  pass --show-trace to nix-build"
    echo "  -p|--platform PLATFORM        box to build for: ${KNOWN_PLATFORMS[*]}"
    echo "                                (default: the one matching this machine)"
    echo "  -t|--tag TAG                  Loom tag to embed (installer only; default: newest)"
    echo "  --serial                      installer: add a getty on ttyS0 to the image, so the"
    echo "                                VM can be driven from a terminal that copies and"
    echo "                                pastes. One unit more than a real stick carries."
    echo "                                'box' always has it and ignores this."
    echo "  --no-gui                      do not open a window. With no --serial there is then"
    echo "                                no way into the VM at all, which is only useful for"
    echo "                                checking that it boots."
    echo "  --memory MB                   guest memory (default: ${MEMORY_MB})"
    echo "  --cores N                     guest cores (default: ${CORES})"
    echo "  --disks N                     emulated NVMe count, installer only (default: ${DISK_COUNT})"
    echo "  --disk-size SIZE              each disk's apparent size (default: ${DISK_SIZE}). The"
    echo "                                pool must reach 250 GB or the installer refuses."
    echo "  --usb DIR                     attach a second USB stick made from DIR, for watching"
    echo "                                what usb-ingest makes of it"
    echo "  --start-loom                  box: leave loom.service wanted. It cannot come up --"
    echo "                                no cluster, no images -- so this is for watching it"
    echo "                                fail with the arguments modes.nix chose."
    echo "  --debug                       box: build with nixos/debug.nix on and forward"
    echo "                                localhost:${DEBUG_SSH_PORT} to the guest's sshd. Generates a keypair"
    echo "                                in the state directory, reused across runs and deleted"
    echo "                                by 'reset'. The cheapest way to try --debug, and the"
    echo "                                way to point an agent at an appliance with no box."
    echo "  --force                       reflash the stick even if one exists; do not ask"
    echo "                                before deleting on 'reset'"
    echo "  --state-root DIR              where per-platform VM state lives (default:"
    echo "                                .appliance-vm in the checkout). A unix socket path is"
    echo "                                capped at 107 bytes, so a deep checkout needs this."
    echo "  --min-free GB                 free space nix should collect garbage to keep"
    echo "                                during the build, 0 to not ask (default: ${MIN_FREE_GB})"
    echo "  --max-free GB                 how far a collection goes once it starts (default: ${MAX_FREE_GB})"
    echo "  --nixpkgs NIXPKGS             nixpkgs source (required; 'appliance-vm' passes it)"
    echo "  --nixos-hardware PATH         nixos-hardware source (required; passed the same way)"
    echo "  --firmware DIR                UEFI firmware directory (installer only; passed the"
    echo "                                same way)"
}

#
# Main
#

while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            usage
            exit 0
        ;;
        -v|--verbose)
            VERBOSE=true
            shift
        ;;
        -p|--platform)
            shift
            PLATFORM="${1?Missing PLATFORM}"
            # Matched against the list rather than by calling platform_system,
            # which in a condition would disable `set -e` inside it.
            case " ${KNOWN_PLATFORMS[*]} " in
                *" ${PLATFORM} "*)
                    :
                ;;
                *)
                    echo >&2 "[!] Error: unknown platform: ${PLATFORM}"
                    echo >&2 "    Known platforms: ${KNOWN_PLATFORMS[*]}"
                    exit 1
                ;;
            esac
            shift
        ;;
        -t|--tag)
            shift
            TAG="${1?Missing TAG}"
            shift
        ;;
        --serial)
            SERIAL=true
            shift
        ;;
        --no-gui)
            GUI=false
            shift
        ;;
        --memory)
            shift
            MEMORY_MB="${1?Missing MB}"
            shift
        ;;
        --cores)
            shift
            CORES="${1?Missing N}"
            shift
        ;;
        --disks)
            shift
            DISK_COUNT="${1?Missing N}"
            shift
        ;;
        --disk-size)
            shift
            DISK_SIZE="${1?Missing SIZE}"
            shift
        ;;
        --usb)
            shift
            USB_DIR="${1?Missing DIR}"
            shift
        ;;
        --start-loom)
            START_LOOM=true
            shift
        ;;
        --debug)
            DEBUG_ACCESS=true
            shift
        ;;
        --force)
            FORCE=true
            shift
        ;;
        --min-free)
            shift
            MIN_FREE_GB="${1?Missing GB}"
            shift
        ;;
        --max-free)
            shift
            MAX_FREE_GB="${1?Missing GB}"
            shift
        ;;
        --nixpkgs)
            shift
            NIXPKGS="${1?Missing NIXPKGS}"
            shift
        ;;
        --nixos-hardware)
            shift
            NIXOS_HARDWARE="${1?Missing NIXOS_HARDWARE}"
            shift
        ;;
        --firmware)
            shift
            FIRMWARE_DIR="${1?Missing DIR}"
            shift
        ;;
        --state-root)
            shift
            STATE_ROOT="${1?Missing DIR}"
            shift
        ;;
        -*)
            echo >&2 "[!] Error: unknown option: ${1}"
            usage
            exit 1
        ;;
        *)
            if [[ -n "${MODE}" ]]; then
                echo >&2 "[!] Error: more than one mode given: ${MODE} and ${1}"
                exit 1
            fi
            case " ${KNOWN_MODES[*]} " in
                *" ${1} "*)
                    MODE="${1}"
                ;;
                *)
                    echo >&2 "[!] Error: unknown mode: ${1}"
                    echo >&2 "    Known modes: ${KNOWN_MODES[*]}"
                    exit 1
                ;;
            esac
            shift
        ;;
    esac
done

if [[ -z "${MODE}" ]]; then
    echo >&2 "[!] Error: no mode given."
    usage
    exit 1
fi

# Same reasoning as --wifi-* without --wifi in cicd/build_appliance_image.sh: a
# flag that silently does nothing is worse than an error, and on this one the
# silence would be somebody waiting on an ssh that was never going to answer.
if [[ "${DEBUG_ACCESS}" = true && "${MODE}" != box ]]; then
    echo >&2 "[!] Error: --debug applies to 'box' only, not '${MODE}'."
    echo >&2 "    The installer rig boots the stick image, and a debug stick is what"
    echo >&2 "    'build-appliance-image --debug' produces -- it carries its own key."
    exit 1
fi

HOST_ARCH="$(uname -m)"

if [[ -z "${PLATFORM}" ]]; then
    case "${HOST_ARCH}" in
        x86_64)
            # As run_appliance_tests.sh: nuc12 is the same architecture, but
            # evo-x2 is the one that declares a GPU and so exercises the
            # toolchain the other two do not.
            PLATFORM="evo-x2"
        ;;
        aarch64)
            PLATFORM="spark"
        ;;
        *)
            echo >&2 "[!] Error: no platform for architecture ${HOST_ARCH}; pass --platform."
            echo >&2 "    Known platforms: ${KNOWN_PLATFORMS[*]}"
            exit 1
        ;;
    esac
fi

NIX_SYSTEM="$(platform_system "${PLATFORM}")"

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

# A window or a serial port -- with neither there is no way to interact with the
# VM at all, and the run can only tell you whether it got as far as booting.
if [[ "${GUI}" = false && "${SERIAL}" = false && "${MODE}" = installer ]]; then
    echo "[!] Note: --no-gui without --serial leaves no way into this VM."
    echo "[!] Pass --serial to drive it from this terminal."
fi

prepare_state_dir

case "${MODE}" in
    box)
        validate_environment
        resolve_loom_values
        resolve_debug_key
        build_box_vm
        run_box_vm
    ;;
    installer)
        validate_environment
        prepare_firmware
        build_installer_image
        virtual_flash
        create_disks
        create_usb_stick
        run_installer_vm
    ;;
    attach)
        attach_serial
    ;;
    reset)
        reset_state
    ;;
    *)
        # Unreachable: the mode was matched against KNOWN_MODES above. Here
        # because shellcheck's `add-default-case` asks for it, and because an
        # unreachable branch that says so is cheaper than finding out.
        echo >&2 "[!] Error: unhandled mode: ${MODE}"
        exit 1
    ;;
esac
