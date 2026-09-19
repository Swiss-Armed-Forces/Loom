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
    local model cores mem_kb mem_human

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
}

section_network(){
    local entry iface driver state speed mac path matched=0 found=0

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

        printf '  %s\n' "${iface}"
        subfield "driver" "${driver}"
        subfield "state" "${state:-unknown}"
        subfield "speed" "${speed}"
        subfield "mac" "${mac}"
        subfield "path" "${path}"

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
    fi
    if [[ -e /dev/kfd ]]; then
        field "/dev/kfd" "present (ROCm compute is reachable)"
    elif [[ "${PLATFORM_GPU_VENDOR}" = "amd" ]]; then
        field "/dev/kfd" "ABSENT -- up.sh will not find a GPU"
    fi
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
    local bios_version bios_date board product

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
    if [[ -d /sys/firmware/efi ]]; then
        field "boot mode" "UEFI"
    else
        field "boot mode" "not UEFI -- the appliance image will not boot here"
    fi
}

#
# JSON
#
# Built with jq rather than by hand, because hand-rolled JSON from shell is how
# reports arrive unparsable. jq is in the appliance's toolchain already (up.sh
# needs it); elsewhere the text report is the fallback and says so.
#

emit_json(){
    local interfaces entry iface driver path state wireless
    local kernel arch cmdline mem_kb vram gtt

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
            --argjson wireless "${wireless}" \
            '. + [{name: $name, driver: $driver, path: $path, state: $state, wireless: $wireless}]')"
    done

    kernel="$(uname --release)"
    arch="$(uname --machine)"
    cmdline="$(slurp /proc/cmdline)"
    mem_kb="$(sed --quiet 's/^MemTotal:[[:space:]]*\([0-9]*\) kB$/\1/p' /proc/meminfo 2>/dev/null || true)"
    vram="$(slurp /sys/class/drm/card0/device/mem_info_vram_total)"
    gtt="$(slurp /sys/class/drm/card0/device/mem_info_gtt_total)"

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
        --argjson interfaces "${interfaces}" \
        '{
          declared: {
            platform: $platformId, netMatch: $netMatch,
            wifiMatch: $wifiMatch, gpuVendor: $gpuVendor
          },
          kernel: $kernel, arch: $arch, cmdline: $cmdline,
          memTotalKb: $memTotalKb,
          gpu: { vramTotal: $vram, gttTotal: $gtt },
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
