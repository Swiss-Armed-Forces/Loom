#!/usr/bin/env bash
# Reports what a box actually is, next to what Loom was told it is.
#
# Every value in nixos/platforms/<id>.nix is a claim about hardware -- which
# driver claims the wired port, whether the radio can run an access point, how
# much memory the iGPU may pin. Those claims were written from spec sheets and
# other people's write-ups, because the boxes were not in the room. This is how
# they get checked.
#
# It is deliberately plain bash with no Nix dependency, because the box it most
# needs to run on is the one that is NOT yet running Loom: a DGX Spark on DGX
# OS, an EVO-X2 on whatever it shipped with, a NUC booted off a live stick. So
# every probe is guarded -- a missing `lspci` or `iw` costs that section and
# nothing else -- and the output is meant to be read, pasted or photographed.
#
# On the appliance the same script is wrapped by nixos/box.nix, which sets the
# LOOM_PLATFORM_* variables below from the platform's own evaluated
# configuration. That is what turns the report from "here is the hardware" into
# "here is the hardware, and here is where it disagrees with the image". Run
# anywhere else those are simply unset, and the declared column is omitted.
#
# Style note: `command -v` is written out at each use rather than wrapped in a
# `have()` helper, and command substitutions are always assigned to a variable
# before being passed anywhere. Both are to satisfy `shellcheck -x -o all`,
# which the repository's hooks run: a *function* in an `if` condition silently
# disables `set -e` inside it (SC2310), and a substitution used directly as an
# argument throws its exit status away (SC2312).
set -euo pipefail

JSON=false
OUTPUT=""

# Set by nixos/box.nix on the appliance; empty everywhere else.
PLATFORM_ID="${LOOM_PLATFORM_ID:-}"
PLATFORM_DESCRIPTION="${LOOM_PLATFORM_DESCRIPTION:-}"
PLATFORM_NET_MATCH="${LOOM_PLATFORM_NET_MATCH:-}"
PLATFORM_WIFI_MATCH="${LOOM_PLATFORM_WIFI_MATCH:-}"
PLATFORM_GPU_VENDOR="${LOOM_PLATFORM_GPU_VENDOR:-}"

#
# Helpers
#

# Reads a sysfs file that may not exist, without tripping `set -e`.
slurp(){
    if [[ -r "${1}" ]]; then
        tr --delete '\n' < "${1}" 2>/dev/null || true
    fi
}

heading(){
    printf '\n== %s\n' "${1}"
}

field(){
    printf '  %-26s %s\n' "${1}" "${2}"
}

subfield(){
    printf '    %-24s %s\n' "${1}" "${2}"
}

note(){
    printf '  (%s)\n' "${1}"
}

# Bytes -> GiB with one decimal, without bc: integer maths on tenths.
gib(){
    local bytes="${1}" tenths
    if [[ -z "${bytes}" || ! "${bytes}" =~ ^[0-9]+$ ]]; then
        printf 'unknown'
        return 0
    fi
    tenths=$(( bytes * 10 / 1024 / 1024 / 1024 ))
    printf '%d.%d GiB' $(( tenths / 10 )) $(( tenths % 10 ))
}

# The driver bound to a device, from the symlink the kernel maintains. Works
# without udevadm, which a minimal live image may not carry.
device_driver(){
    local dev="${1}" link
    link="$(readlink -f "${dev}/driver" 2>/dev/null || true)"
    if [[ -n "${link}" ]]; then
        basename "${link}"
    else
        printf 'none'
    fi
}

# The stable PCI path, which is what a `netMatch` would be pinned to if the
# driver ever stops being specific enough. udev's name for it, when available.
device_path(){
    local iface="${1}" out
    if command -v udevadm > /dev/null 2>&1; then
        out="$(udevadm info "/sys/class/net/${iface}" 2>/dev/null |
            sed --quiet 's/^E: ID_PATH=//p' || true)"
        if [[ -n "${out}" ]]; then
            printf '%s' "${out}"
            return 0
        fi
    fi
    # -e, not -f: `readlink -f` resolves a path whose last component does not
    # exist, so a virtual interface would report a plausible-looking "device".
    out="$(readlink -e "/sys/class/net/${iface}/device" 2>/dev/null || true)"
    if [[ -n "${out}" ]]; then
        basename "${out}"
    else
        printf 'n/a'
    fi
}

# /sys reports -1 for an interface that has no link, which is noise rather than
# information.
link_speed(){
    local speed
    speed="$(slurp "/sys/class/net/${1}/speed")"
    if [[ -z "${speed}" || "${speed}" = "-1" ]]; then
        printf 'no link'
    else
        printf '%s Mb/s' "${speed}"
    fi
}

# The PCI address behind an interface, plus the vendor:device ids lspci prints
# for it.
#
# `netMatch` is a systemd [Match] section, and `Driver=` is only specific enough
# when one device binds that driver. On a box where several do -- the EVO-X2's
# Realtek pair, and the DGX Spark's ConnectX-7, which presents two 100G MACs per
# QSFP cage on separate PCIe links -- the ids are what tells two otherwise
# identical lines of this report apart.
device_pci(){
    local iface="${1}" link bdf out subsystem
    link="$(readlink -e "/sys/class/net/${iface}/device" 2>/dev/null || true)"
    if [[ -z "${link}" ]]; then
        printf 'n/a'
        return 0
    fi
    bdf="$(basename "${link}")"
    # A USB or platform NIC has a device that is not a PCI function at all, and
    # its directory name is not a BDF. Say which bus it is on rather than
    # printing a bare identifier under a field called "pci", and do not feed
    # lspci something it will reject.
    if [[ ! "${bdf}" =~ ^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]$ ]]; then
        subsystem="$(readlink -f "${link}/subsystem" 2>/dev/null || true)"
        if [[ -n "${subsystem}" ]]; then
            printf '%s %s' "$(basename "${subsystem}")" "${bdf}"
        else
            printf '%s' "${bdf}"
        fi
        return 0
    fi
    if command -v lspci > /dev/null 2>&1; then
        # lspci takes the domainless form; -D makes it print the full one back.
        out="$(lspci -D -nn -s "${bdf}" 2>/dev/null | head --lines=1 || true)"
        if [[ -n "${out}" ]]; then
            printf '%s' "${out}"
            return 0
        fi
    fi
    printf '%s' "${bdf}"
}

# Which physical port of a multi-port NIC this interface is, when the driver
# says. mlx5 and other switchdev-capable drivers expose both; most drivers
# expose neither, and then there is nothing to report.
device_port(){
    local iface="${1}" name switch out=""
    name="$(slurp "/sys/class/net/${iface}/phys_port_name")"
    switch="$(slurp "/sys/class/net/${iface}/phys_switch_id")"
    if [[ -n "${name}" ]]; then
        out="port ${name}"
    fi
    if [[ -n "${switch}" ]]; then
        out="${out:+${out}, }switch ${switch}"
    fi
    printf '%s' "${out}"
}

# udev's path-derived name for an interface -- what the kernel would have called
# it if nothing renamed it, and therefore what `--interface NAME` wants.
device_net_name(){
    local iface="${1}" out
    if command -v udevadm > /dev/null 2>&1; then
        out="$(udevadm info "/sys/class/net/${iface}" 2>/dev/null |
            sed --quiet 's/^E: ID_NET_NAME_PATH=//p' || true)"
        if [[ -n "${out}" ]]; then
            printf '%s' "${out}"
            return 0
        fi
    fi
    printf ''
}

# An EFI variable's value, as space-separated decimal bytes.
#
# efivarfs prepends four bytes of attributes to every variable, so the value
# starts at byte 5 -- for the one-byte booleans read below, that makes the last
# byte the one that matters. `od` is coreutils; efivar(1) and bootctl(1) are not
# on a box that is not running NixOS, which is where this most needs to work.
efivar_bytes(){
    local path="${1}"
    if [[ -r "${path}" ]]; then
        od --address-radix=n --format=u1 "${path}" 2>/dev/null | tr --squeeze-repeats ' ' || true
    fi
}

# A one-byte EFI boolean: "enabled", "disabled", or empty when unreadable.
efivar_flag(){
    local bytes last
    bytes="$(efivar_bytes "${1}")"
    if [[ -z "${bytes}" ]]; then
        return 0
    fi
    last="${bytes##* }"
    case "${last}" in
        1) printf 'enabled'  ;;
        0) printf 'disabled' ;;
        *) printf 'unknown (last byte %s)' "${last}" ;;
    esac
}

# Device-tree strings are NUL-separated and NUL-terminated, which makes them
# unreadable in a terminal and invalid in JSON. There is no DMI on this box --
# section_firmware already says so -- so this is the only name it has.
devicetree_string(){
    local path="${1}"
    if [[ -r "${path}" ]]; then
        tr '\0' ' ' < "${path}" 2>/dev/null | sed 's/[[:space:]]*$//' || true
    fi
}

#
# Sections
#

section_system(){
    local host kernel arch os cmdline

    heading "System"
    host="$(uname --nodename)"
    kernel="$(uname --release)"
    arch="$(uname --machine)"
    cmdline="$(slurp /proc/cmdline)"
    field "hostname" "${host}"
    field "kernel" "${kernel} (${arch})"
    if [[ -r /etc/os-release ]]; then
        os="$(sed --quiet 's/^PRETTY_NAME="\?\([^"]*\)"\?$/\1/p' /etc/os-release |
            head --lines=1 || true)"
        field "os" "${os}"
    fi
    field "cmdline" "${cmdline}"
}

section_platform(){
    heading "Loom platform (declared)"
    if [[ -z "${PLATFORM_ID}" ]]; then
        note "not running a Loom appliance image -- nothing was declared, so every"
        note "section below reports the hardware only"
        return 0
    fi
    field "id" "${PLATFORM_ID}"
    field "description" "${PLATFORM_DESCRIPTION}"
    field "netMatch" "${PLATFORM_NET_MATCH:-<unset>}"
    field "wifiMatch" "${PLATFORM_WIFI_MATCH:-<unset>}"
    field "gpuVendor" "${PLATFORM_GPU_VENDOR:-<none: CPU-only>}"
}

section_cpu_memory(){
    local model cores mem_kb mem_human governor scaling_driver cppc

    heading "CPU and memory"
    model="$(sed --quiet 's/^model name[[:space:]]*: //p' /proc/cpuinfo 2>/dev/null |
        head --lines=1 || true)"
    if [[ -z "${model}" ]]; then
        # aarch64 has no "model name"; this is the best that is always there.
        model="$(sed --quiet 's/^CPU implementer[[:space:]]*: //p' /proc/cpuinfo 2>/dev/null |
            head --lines=1 || true)"
        model="implementer ${model:-unknown}"
    fi
    cores="$(grep --count '^processor' /proc/cpuinfo 2>/dev/null || printf '?')"
    field "model" "${model}"
    field "logical cpus" "${cores}"

    mem_kb="$(sed --quiet 's/^MemTotal:[[:space:]]*\([0-9]*\) kB$/\1/p' /proc/meminfo 2>/dev/null || true)"
    mem_human="$(gib $(( ${mem_kb:-0} * 1024 )))"
    field "MemTotal" "${mem_human}"
    note "what Linux sees -- on an APU the firmware's VRAM carve-out is already gone"

    # Which cpufreq driver bound, and -- on the DGX Spark -- whether autonomous
    # CPPC was asked for.
    #
    # The GB10's memory fabric only enters autonomous performance management
    # when `cppc_cpufreq.auto_sel_mode=1` is set, and without it single-thread
    # memory bandwidth is reported at roughly a third of stock DGX OS. The
    # parameter needs a cppc_cpufreq that carries the autonomous-mode series,
    # which the stock kernel does not -- so on our image this is expected to
    # read "not requested", and that is a known cost rather than a fault. See
    # the GPU section of Documentation/appliance.md.
    scaling_driver="$(slurp /sys/devices/system/cpu/cpufreq/policy0/scaling_driver)"
    governor="$(slurp /sys/devices/system/cpu/cpufreq/policy0/scaling_governor)"
    if [[ -n "${scaling_driver}" ]]; then
        field "cpufreq driver" "${scaling_driver}"
        field "cpufreq governor" "${governor:-unknown}"
    else
        note "no cpufreq policy0 -- frequency scaling is firmware-managed or absent"
    fi
    cppc="$(tr ' ' '\n' < /proc/cmdline 2>/dev/null |
        grep --extended-regexp '^cppc_cpufreq\.auto_sel_mode=' || true)"
    field "CPPC autonomous mode" "${cppc:-not requested}"
}

section_network(){
    local entry iface driver state speed mac path pci port netname matched=0 found=0

    heading "Wired network interfaces"
    note "physical ports only; bridges, docker0 and tunnels are omitted"
    for entry in /sys/class/net/*; do
        [[ -e "${entry}" ]] || continue
        iface="$(basename "${entry}")"
        [[ "${iface}" = "lo" ]] && continue
        # Radios get their own section.
        [[ -d "${entry}/wireless" ]] && continue
        # Physical ports have a device behind them; bridges, docker0, tun/tap
        # and the appliance's own `br-loom` do not. Only a physical port can be
        # what a platform's `netMatch` selects, and a report listing nine
        # virtual devices is a report nobody reads to the end.
        [[ -e "${entry}/device" ]] || continue
        found=$(( found + 1 ))

        driver="$(device_driver "${entry}/device")"
        state="$(slurp "${entry}/operstate")"
        speed="$(link_speed "${iface}")"
        mac="$(slurp "${entry}/address")"
        path="$(device_path "${iface}")"
        pci="$(device_pci "${iface}")"
        port="$(device_port "${iface}")"
        netname="$(device_net_name "${iface}")"

        printf '  %s\n' "${iface}"
        subfield "driver" "${driver}"
        subfield "state" "${state:-unknown}"
        subfield "speed" "${speed}"
        subfield "mac" "${mac}"
        subfield "path" "${path}"
        subfield "pci" "${pci}"
        # Only on a driver that knows -- see device_port. An empty line here
        # would be noise on the three ports out of four that never set it.
        if [[ -n "${port}" ]]; then
            subfield "port" "${port}"
        fi
        # The name to hand --interface. Suppressed when it is what the interface
        # is already called, which is the ordinary case and says nothing.
        if [[ -n "${netname}" && "${netname}" != "${iface}" ]]; then
            subfield "udev name" "${netname}"
        fi

        if [[ -n "${PLATFORM_NET_MATCH}" && "${PLATFORM_NET_MATCH}" == *"${driver}"* ]]; then
            subfield "->" "matches the declared netMatch"
            matched=$(( matched + 1 ))
        fi
    done

    if (( found == 0 )); then
        note "no physical wired port found at all"
    fi

    if [[ -n "${PLATFORM_NET_MATCH}" ]]; then
        printf '\n'
        field "declared netMatch" "${PLATFORM_NET_MATCH}"
        field "interfaces matching it" "${matched}"
        case "${matched}" in
            0)
                note "NOTHING MATCHED. There is no loom0 from the .link file; the box is"
                note "relying on loom-interface-fallback, or has no appliance network at all."
            ;;
            1)
                : # The intended case.
            ;;
            *)
                note "more than one matched: udev picks, and the others keep kernel names."
                note "Pin one with --interface <name>, using the name shown above."
            ;;
        esac
    fi

    if [[ -e /sys/class/net/loom0 ]]; then
        field "loom0" "present"
    else
        field "loom0" "ABSENT"
    fi
}

section_radios(){
    local wireless iface driver phy ap found=0

    heading "Radios"
    # A plain glob with an existence test, not `compgen -G`: that builtin does
    # not expand this pattern consistently across bash versions -- the bash in
    # the appliance's own closure reported no radio on a machine that has one --
    # and this script has to behave the same on whatever bash the box it is
    # diagnosing happens to ship.
    for wireless in /sys/class/net/*/wireless; do
        [[ -e "${wireless}" ]] || continue
        found=$(( found + 1 ))
        iface="$(dirname "${wireless}")"
        iface="$(basename "${iface}")"
        driver="$(device_driver "/sys/class/net/${iface}/device")"
        printf '  %s\n' "${iface}"
        subfield "driver" "${driver}"

        # AP mode is the question wifi.nix cares about: without it hostapd never
        # starts and --wifi produces a box with no access point.
        if command -v iw > /dev/null 2>&1; then
            phy="$(slurp "/sys/class/net/${iface}/phy80211/name")"
            ap="$(iw phy "${phy}" info 2>/dev/null |
                sed --quiet '/Supported interface modes/,/^[[:space:]]*[A-Z]/p' |
                grep --count '\* AP$' || true)"
            if [[ "${ap:-0}" -gt 0 ]]; then
                subfield "AP mode" "supported"
            else
                subfield "AP mode" "NOT ADVERTISED -- --wifi will not work here"
            fi
        else
            subfield "AP mode" "unknown (iw not installed)"
        fi
    done

    if (( found == 0 )); then
        note "no wireless interface present (or the radio is disabled in firmware)"
        return 0
    fi

    if [[ -n "${PLATFORM_WIFI_MATCH}" ]]; then
        field "declared wifiMatch" "${PLATFORM_WIFI_MATCH}"
        note "a Type=wlan match is broad on purpose; pin the driver above once confirmed"
    fi
}

section_gpu(){
    local card name driver vram vis_vram gtt requested requested_line
    local nvidia_version nvidia_modules nvidia_nodes node

    heading "GPU"
    if command -v lspci > /dev/null 2>&1; then
        lspci -nnk 2>/dev/null |
            grep --after-context=2 --extended-regexp \
                'VGA compatible controller|3D controller|Display controller' |
            sed 's/^/  /' || note "no display controller reported by lspci"
    else
        note "lspci not installed; reading sysfs only"
    fi

    for card in /sys/class/drm/card*; do
        name="$(basename "${card}")"
        # The glob also matches connectors -- card1-DP-1, card1-HDMI-A-1 -- and
        # each of those has a `device` symlink pointing back at its card, so
        # without this every output port is reported as if it were a GPU.
        [[ "${name}" =~ ^card[0-9]+$ ]] || continue
        [[ -e "${card}/device" ]] || continue

        driver="$(device_driver "${card}/device")"
        printf '\n  %s\n' "${name}"
        subfield "driver" "${driver}"

        # The three numbers that decide whether Ollama has anything to work
        # with on an APU. vram is the firmware carve-out; gtt is the pool the
        # kernel parameters in platforms/evo-x2.nix size.
        vram="$(slurp "${card}/device/mem_info_vram_total")"
        vis_vram="$(slurp "${card}/device/mem_info_vis_vram_total")"
        gtt="$(slurp "${card}/device/mem_info_gtt_total")"
        if [[ -n "${vram}${gtt}" ]]; then
            vram="$(gib "${vram}")"
            vis_vram="$(gib "${vis_vram}")"
            gtt="$(gib "${gtt}")"
            subfield "VRAM (firmware carve-out)" "${vram}"
            subfield "visible VRAM" "${vis_vram}"
            subfield "GTT (system memory pool)" "${gtt}"
        fi
    done

    # The ceiling the image asked for, so the number above can be compared
    # against the intent rather than against a guess.
    requested="$(tr ' ' '\n' < /proc/cmdline 2>/dev/null |
        grep --extended-regexp '^(amdgpu\.gttsize|ttm\.pages_limit|amd_iommu)=' || true)"
    if [[ -n "${requested}" ]]; then
        requested_line="$(printf '%s' "${requested}" | tr '\n' ' ')"
        printf '\n'
        field "kernel asked for" "${requested_line}"
        note "GTT above should be at or near this ceiling; if it is far below, the"
        note "parameter did not take effect -- report both numbers"
    fi

    if command -v rocm-smi > /dev/null 2>&1; then
        printf '\n  rocm-smi:\n'
        rocm-smi --showproductname --showmeminfo vram 2>/dev/null | sed 's/^/    /' || true
    fi
    if command -v nvidia-smi > /dev/null 2>&1; then
        printf '\n  nvidia-smi:\n'
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null |
            sed 's/^/    /' || true
        # -L names the board rather than describing it, which is how "GB10"
        # gets confirmed rather than inferred from the box it is in.
        nvidia-smi -L 2>/dev/null | sed 's/^/    /' || true
    fi

    # The driver's own account of itself, which exists whether or not nvidia-smi
    # was installed -- and on a box where the GPU claim is wrong, the absence of
    # this file is the first thing worth knowing.
    nvidia_version="$(slurp /proc/driver/nvidia/version)"
    if [[ -n "${nvidia_version}" ]]; then
        printf '\n'
        field "nvidia driver" "${nvidia_version}"
    fi
    nvidia_modules="$(sed --quiet 's/^\(nvidia[a-z_]*\) .*/\1/p' /proc/modules 2>/dev/null |
        sort | tr '\n' ' ' || true)"
    if [[ -n "${nvidia_modules}" ]]; then
        field "nvidia modules" "${nvidia_modules}"
    fi
    # A glob rather than `find`: findutils is not in loom-platform-info's
    # runtimeInputs, and writeShellApplication gives the script no PATH beyond
    # them -- so a `find` here would work when run by hand and fail on the
    # appliance, which is the one place it matters.
    nvidia_nodes=""
    for node in /dev/nvidia*; do
        [[ -e "${node}" ]] || continue
        nvidia_nodes="${nvidia_nodes}$(basename "${node}") "
    done
    if [[ -n "${nvidia_nodes}" ]]; then
        field "/dev nodes" "${nvidia_nodes}"
    fi

    if [[ -e /dev/kfd ]]; then
        field "/dev/kfd" "present (ROCm compute is reachable)"
    elif [[ "${PLATFORM_GPU_VENDOR}" = "amd" ]]; then
        field "/dev/kfd" "ABSENT -- up.sh will not find a GPU"
    fi

    # The nvidia mirror of the /dev/kfd check above. up.sh counts GPUs with
    # `nvidia-smi --list-gpus` and hard-exits below LOOM_MIN_GPU, so on a box
    # declaring this vendor an absent control device means the appliance serves
    # nothing at all -- and the way back is a stick rebuilt with --no-gpu.
    if [[ -e /dev/nvidiactl ]]; then
        field "/dev/nvidiactl" "present (NVIDIA compute is reachable)"
    elif [[ "${PLATFORM_GPU_VENDOR}" = "nvidia" ]]; then
        field "/dev/nvidiactl" "ABSENT -- up.sh will not find a GPU"
        note "rebuild the stick with --no-gpu to get a working CPU-only box"
    fi
}

# Whether the GPU reaches a container, which is the question that actually
# decides whether Ollama can be offloaded.
#
# `nvidia-smi` on the host says the driver is up; it says nothing about whether
# the minikube node container can see the device. That path runs through CDI --
# nvidia-ctk generates a spec, docker reads it, and minikube's device plugin
# advertises nvidia.com/gpu to the cluster -- and any link in it can be missing
# while the host looks perfectly healthy.
section_container_gpu(){
    local dir spec specs runtimes found=0

    heading "GPU in containers"

    for dir in /var/run/cdi /etc/cdi /run/cdi; do
        [[ -d "${dir}" ]] || continue
        found=$(( found + 1 ))
        # Globs rather than `find`, for the same reason as the /dev/nvidia*
        # loop above: findutils is not on this script's PATH on the appliance.
        specs=""
        for spec in "${dir}"/*; do
            [[ -f "${spec}" ]] || continue
            specs="${specs}$(basename "${spec}") "
        done
        field "${dir}" "${specs:-empty}"
    done
    if (( found == 0 )); then
        note "no CDI spec directory -- nothing has generated a device spec"
    fi

    if command -v nvidia-ctk > /dev/null 2>&1; then
        field "nvidia-ctk" "present"
    else
        field "nvidia-ctk" "absent"
    fi
    if command -v nvidia-container-runtime > /dev/null 2>&1; then
        field "nvidia-container-runtime" "present"
    else
        field "nvidia-container-runtime" "absent"
    fi

    # Guarded twice: docker may not be installed, and on the appliance it is
    # installed but not running until loom.service has started it.
    if command -v docker > /dev/null 2>&1; then
        # Read the two lines out of `docker info`'s ordinary output rather than
        # asking for a --format template. `{{.Runtimes}}` prints each runtime's
        # entire OCI feature matrix -- thousands of characters of seccomp and
        # capability lists per entry -- which buries the rest of this report,
        # and ranging over the keys instead needs Go template variables that
        # look enough like shell ones to trip shellcheck. The plain output
        # already has exactly the two lines wanted, and needs no jq, which the
        # text report is meant to do without.
        runtimes="$(timeout 15 docker info 2>/dev/null |
            sed --quiet 's/^ \(Runtimes\|Default Runtime\): /\1: /p' |
            tr '\n' ' ' || true)"
        if [[ -n "${runtimes}" ]]; then
            field "docker runtimes" "${runtimes}"
        else
            note "docker is installed but not answering -- start it, or run this later"
        fi
    else
        note "docker not installed"
    fi

    # Deliberately not run: it needs an image, which an air-gapped box may not
    # have and which this report must never go and fetch.
    note "to confirm end to end, run by hand:"
    note "  docker run --rm --gpus all <an image with nvidia-smi> nvidia-smi"
}

section_storage(){
    heading "Storage"
    if command -v lsblk > /dev/null 2>&1; then
        lsblk --nodeps --output NAME,SIZE,MODEL,TRAN 2>/dev/null | sed 's/^/  /' || true
    else
        note "lsblk not installed"
    fi
}

section_firmware(){
    local bios_version bios_date board product dt_model dt_compatible
    local secure_boot setup_mode versions upgrades

    heading "Firmware"
    if [[ -r /sys/class/dmi/id/bios_version ]]; then
        bios_version="$(slurp /sys/class/dmi/id/bios_version)"
        bios_date="$(slurp /sys/class/dmi/id/bios_date)"
        board="$(slurp /sys/class/dmi/id/board_name)"
        product="$(slurp /sys/class/dmi/id/product_name)"
        field "BIOS version" "${bios_version}"
        field "BIOS date" "${bios_date}"
        field "board" "${board}"
        field "product" "${product}"
    else
        note "no DMI data (common on aarch64)"
    fi

    # Where an aarch64 box says what it is. On a DGX Spark this is the only
    # place the model name appears at all.
    dt_model="$(devicetree_string /sys/firmware/devicetree/base/model)"
    dt_compatible="$(devicetree_string /sys/firmware/devicetree/base/compatible)"
    if [[ -n "${dt_model}" ]]; then
        field "device-tree model" "${dt_model}"
    fi
    if [[ -n "${dt_compatible}" ]]; then
        field "device-tree compatible" "${dt_compatible}"
    fi

    if [[ -d /sys/firmware/efi ]]; then
        field "boot mode" "UEFI"
    else
        field "boot mode" "not UEFI -- the appliance image will not boot here"
    fi

    # Secure Boot has to be OFF. The appliance stick is not signed by anything
    # the firmware's key database knows, so with Secure Boot on the box refuses
    # to boot it -- and on a machine whose whole user interface is the console,
    # that looks like a dead stick rather than a policy decision.
    #
    # The GUIDs are fixed by the UEFI specification: SecureBoot and SetupMode
    # both live under the global variable GUID.
    secure_boot="$(efivar_flag \
        /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c)"
    setup_mode="$(efivar_flag \
        /sys/firmware/efi/efivars/SetupMode-8be4df61-93ca-11d2-aa0d-00e098032b8c)"
    if [[ -z "${secure_boot}" ]] && command -v bootctl > /dev/null 2>&1; then
        secure_boot="$(bootctl status 2>/dev/null |
            sed --quiet 's/^[[:space:]]*Secure Boot:[[:space:]]*//p' |
            head --lines=1 || true)"
    fi
    if [[ -z "${secure_boot}" ]]; then
        field "Secure Boot" "unknown (no efivars, no bootctl)"
    elif [[ "${secure_boot}" = "disabled" ]]; then
        field "Secure Boot" "disabled"
    else
        field "Secure Boot" "${secure_boot} -- MUST BE DISABLED"
        note "the appliance stick is unsigned; with Secure Boot on the box will"
        note "not boot it. Turn it off in the firmware setup first."
    fi
    if [[ -n "${setup_mode}" ]]; then
        field "Setup Mode" "${setup_mode}"
    fi

    # The DGX Spark ships with firmware only DGX OS can boot from: NixOS will
    # not come up until it has been updated, and the update has to be applied
    # from DGX OS while the box can still reach LVFS. That makes this the one
    # check that has to happen BEFORE a stick is ever flashed.
    if command -v fwupdmgr > /dev/null 2>&1; then
        printf '\n  fwupd:\n'
        # Every fwupdmgr call is wrapped in a timeout. These talk to a D-Bus
        # daemon that may not be running, and `get-upgrades` consults metadata
        # that on an air-gapped box was last refreshed from a network that is no
        # longer there. A diagnostic report must not be the thing that hangs.
        if command -v jq > /dev/null 2>&1; then
            versions="$(timeout 15 fwupdmgr get-devices --json 2>/dev/null |
                jq --raw-output '
                    [.. | objects | select(has("Name") and has("Version"))
                        | "\(.Name): \(.Version)"] | unique | .[]' \
                2>/dev/null || true)"
        else
            versions="$(timeout 15 fwupdmgr get-devices 2>/dev/null || true)"
        fi
        if [[ -n "${versions}" ]]; then
            printf '%s\n' "${versions}" | sed 's/^/    /'
        else
            note "fwupdmgr reported no devices"
        fi
        # Non-zero when there is nothing to do, which is the good case.
        upgrades="$(timeout 15 fwupdmgr get-upgrades 2>/dev/null || true)"
        if [[ -n "${upgrades}" ]]; then
            printf '\n  fwupd updates available:\n'
            printf '%s\n' "${upgrades}" | sed 's/^/    /'
            note "on a DGX Spark, apply these from DGX OS before installing the"
            note "appliance: only DGX OS boots from the factory firmware"
        else
            field "firmware updates" "none pending (or LVFS unreachable)"
        fi
    else
        note "fwupdmgr not installed -- firmware version and pending updates unknown"
    fi
}

#
# JSON
#
# Built with jq rather than by hand, because hand-rolled JSON from shell is how
# reports arrive unparsable. jq is in the appliance's toolchain already (up.sh
# needs it); elsewhere the text report is the fallback and says so.
#
# Deliberately not mirrored here: the fwupd block. Everything else in this
# function reads a file or a symlink, so --json is fast and cannot block; fwupd
# shells out to a D-Bus daemon that may be absent, stopped or waiting on
# metadata from a network an air-gapped box no longer has. It stays in the text
# report, where the timeouts around it are visible and a slow section is
# obvious. Run without --json for firmware versions.
#

emit_json(){
    local interfaces entry iface driver path state wireless pci port netname
    local kernel arch cmdline mem_kb vram gtt
    local scaling_driver cppc dt_model secure_boot setup_mode
    local nvidia_version nvidia_modules nvidia_nodes node cdi_dir cdi_spec cdi_specs
    local has_nvidia_ctk has_nvidiactl

    if ! command -v jq > /dev/null 2>&1; then
        echo >&2 "[!] --json needs jq, which is not installed."
        echo >&2 "    Run without --json for the text report, which needs nothing."
        exit 1
    fi

    interfaces="[]"
    for entry in /sys/class/net/*; do
        [[ -e "${entry}" ]] || continue
        iface="$(basename "${entry}")"
        [[ "${iface}" = "lo" ]] && continue
        [[ -e "${entry}/device" ]] || continue

        driver="$(device_driver "${entry}/device")"
        path="$(device_path "${iface}")"
        state="$(slurp "${entry}/operstate")"
        pci="$(device_pci "${iface}")"
        port="$(device_port "${iface}")"
        netname="$(device_net_name "${iface}")"
        if [[ -d "${entry}/wireless" ]]; then
            wireless=true
        else
            wireless=false
        fi

        interfaces="$(printf '%s' "${interfaces}" | jq \
            --arg name "${iface}" \
            --arg driver "${driver}" \
            --arg path "${path}" \
            --arg state "${state}" \
            --arg pci "${pci}" \
            --arg port "${port}" \
            --arg udevName "${netname}" \
            --argjson wireless "${wireless}" \
            '. + [{
                name: $name, driver: $driver, path: $path, state: $state,
                pci: $pci, port: $port, udevName: $udevName, wireless: $wireless
            }]')"
    done

    kernel="$(uname --release)"
    arch="$(uname --machine)"
    cmdline="$(slurp /proc/cmdline)"
    mem_kb="$(sed --quiet 's/^MemTotal:[[:space:]]*\([0-9]*\) kB$/\1/p' /proc/meminfo 2>/dev/null || true)"
    vram="$(slurp /sys/class/drm/card0/device/mem_info_vram_total)"
    gtt="$(slurp /sys/class/drm/card0/device/mem_info_gtt_total)"

    scaling_driver="$(slurp /sys/devices/system/cpu/cpufreq/policy0/scaling_driver)"
    cppc="$(tr ' ' '\n' < /proc/cmdline 2>/dev/null |
        grep --extended-regexp '^cppc_cpufreq\.auto_sel_mode=' || true)"
    dt_model="$(devicetree_string /sys/firmware/devicetree/base/model)"
    secure_boot="$(efivar_flag \
        /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c)"
    setup_mode="$(efivar_flag \
        /sys/firmware/efi/efivars/SetupMode-8be4df61-93ca-11d2-aa0d-00e098032b8c)"

    nvidia_version="$(slurp /proc/driver/nvidia/version)"
    nvidia_modules="$(sed --quiet 's/^\(nvidia[a-z_]*\) .*/\1/p' /proc/modules 2>/dev/null |
        sort | tr '\n' ' ' || true)"
    nvidia_nodes=""
    for node in /dev/nvidia*; do
        [[ -e "${node}" ]] || continue
        nvidia_nodes="${nvidia_nodes}$(basename "${node}") "
    done

    cdi_specs=""
    for cdi_dir in /var/run/cdi /etc/cdi /run/cdi; do
        [[ -d "${cdi_dir}" ]] || continue
        for cdi_spec in "${cdi_dir}"/*; do
            [[ -f "${cdi_spec}" ]] || continue
            cdi_specs="${cdi_specs}${cdi_spec} "
        done
    done
    if command -v nvidia-ctk > /dev/null 2>&1; then
        has_nvidia_ctk=true
    else
        has_nvidia_ctk=false
    fi
    if [[ -e /dev/nvidiactl ]]; then
        has_nvidiactl=true
    else
        has_nvidiactl=false
    fi

    jq --null-input \
        --arg platformId "${PLATFORM_ID}" \
        --arg netMatch "${PLATFORM_NET_MATCH}" \
        --arg wifiMatch "${PLATFORM_WIFI_MATCH}" \
        --arg gpuVendor "${PLATFORM_GPU_VENDOR}" \
        --arg kernel "${kernel}" \
        --arg arch "${arch}" \
        --arg cmdline "${cmdline}" \
        --arg memTotalKb "${mem_kb}" \
        --arg vram "${vram}" \
        --arg gtt "${gtt}" \
        --arg scalingDriver "${scaling_driver}" \
        --arg cppcAutonomous "${cppc}" \
        --arg dtModel "${dt_model}" \
        --arg secureBoot "${secure_boot}" \
        --arg setupMode "${setup_mode}" \
        --arg nvidiaDriver "${nvidia_version}" \
        --arg nvidiaModules "${nvidia_modules}" \
        --arg nvidiaNodes "${nvidia_nodes}" \
        --arg cdiSpecs "${cdi_specs}" \
        --argjson hasNvidiaCtk "${has_nvidia_ctk}" \
        --argjson hasNvidiactl "${has_nvidiactl}" \
        --argjson interfaces "${interfaces}" \
        '{
          declared: {
            platform: $platformId, netMatch: $netMatch,
            wifiMatch: $wifiMatch, gpuVendor: $gpuVendor
          },
          kernel: $kernel, arch: $arch, cmdline: $cmdline,
          memTotalKb: $memTotalKb,
          cpu: { scalingDriver: $scalingDriver, cppcAutonomous: $cppcAutonomous },
          firmware: {
            deviceTreeModel: $dtModel,
            secureBoot: $secureBoot,
            setupMode: $setupMode
          },
          gpu: {
            vramTotal: $vram, gttTotal: $gtt,
            nvidia: {
              driver: $nvidiaDriver, modules: $nvidiaModules,
              devNodes: $nvidiaNodes, controlDevice: $hasNvidiactl
            }
          },
          containerGpu: { cdiSpecs: $cdiSpecs, nvidiaCtk: $hasNvidiaCtk },
          interfaces: $interfaces
        }'
}

emit_text(){
    echo "Loom platform report"
    echo "Paste this whole thing -- the sections are short on purpose."
    section_system
    section_platform
    section_cpu_memory
    section_network
    section_radios
    section_gpu
    section_container_gpu
    section_storage
    section_firmware
    printf '\n'
}

#
# Usage
#

usage(){
    echo "usage: $0 [--json] [--output FILE]"
    echo "  Reports this box's hardware, and how it compares with what the Loom"
    echo "  appliance image was told to expect."
    echo "  -h|--help        show this help"
    echo "  --json           machine-readable output (needs jq)"
    echo "  -o|--output FILE write to FILE instead of stdout"
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
        --json)
            JSON=true
            shift
        ;;
        -o|--output)
            shift
            OUTPUT="${1?Missing FILE}"
            shift
        ;;
        *)
            echo >&2 "[!] Error: unknown option: ${1}"
            usage
            exit 1
        ;;
    esac
done

if [[ -n "${OUTPUT}" ]]; then
    exec > "${OUTPUT}"
fi

if [[ "${JSON}" = true ]]; then
    emit_json
else
    emit_text
fi
