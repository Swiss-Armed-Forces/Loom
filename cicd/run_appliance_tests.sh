#!/usr/bin/env bash
# Runs the NixOS VM tests under nixos/tests/.
#
# The tests themselves are plain `nix-build -A tests.<name>` targets and stay
# runnable that way (nixos/README.md spells the invocations out). What this adds
# is the three things that are easy to get wrong by hand:
#
#   * The arguments. Every target needs nixpkgs, a platform, the `*.loom` host
#     list, the namespace and the chat model, and tests/appliance.nix asserts
#     the last three against vars.sh inside the VM -- so passing defaults
#     instead of the real values fails the test for a reason that has nothing to
#     do with the code under test.
#   * The disk. A test run builds a full appliance closure and then writes its
#     VM disk images into the Nix build directory, which is on the same
#     filesystem as the store. `min-free` lets the daemon collect garbage when
#     that runs out instead of failing the build; see nixos/README.md for the
#     permanent settings, NixOS or not.
#   * That a failure in one target does not hide the others. Each runs, and the
#     summary at the end says which ones failed.
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)

# The helpers the appliance scripts share: `check_command`, `platform_system`
# and `resolve_loom_values`. Sourced rather than restated, the same way
# .gitlab-ci.yml sources cicd/ci_helpers.sh -- `platform_system` above all, so
# that adding a platform is one edit rather than four with nothing to catch a
# missed one.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=appliance_common.sh
source "${SCRIPT_DIR}/appliance_common.sh"

# As in cicd/build_appliance_image.sh: nixpkgs comes from devenv's
# `inputs.nixpkgs-stable`, so devenv.lock stays the only nixpkgs pin here.
NIXPKGS=""

# nixos-hardware, by the same route. The platform modules import it, so every
# target here needs it -- including the ones that never look at a GPU.
NIXOS_HARDWARE=""

# Which box to build the nodes for. Defaults to whichever platform matches this
# machine's architecture, because a VM test boots a real kernel: cross-building
# one produces a closure that cannot be run here.
PLATFORM=""
# The platform list and its validation live in cicd/appliance_common.sh --
# see KNOWN_PLATFORMS and require_platform there.
# Both resolved in Main, once, rather than at each use.
NIX_SYSTEM=""
HOST_ARCH=""

# Short names, in the order they are run: cheapest first, so a mistake that
# breaks all of them is reported in a minute rather than in twenty.
#
# `hardware`, `units` and `skills` are first because they are the three that
# never boot anything: they read the evaluated configuration and exit, in
# seconds. A nixos-hardware bump, a nixpkgs change to the unit graph or an
# opencode bump that broke every platform should be reported before the VM
# boots, not after.
KNOWN_TESTS=(hardware units skills install interface-fallback dhcp portal key-store debug wifi mouse usb-ingest appliance)

# Targets that only read the evaluated configuration -- no kernel, no VM, and
# not even the appliance closure. The architecture check and the KVM and disk
# notes below all exist for VM tests and none of them apply to these, so a
# selection made up entirely of them lifts all three. That is what makes
# `appliance-test hardware --platform spark` work on an x86_64 workstation,
# which is exactly what you want to run after a nixos-hardware bump: all three
# platforms checked from one machine, in seconds.
#
# `units` is here for the same reason and one more: it builds the --wifi
# configuration itself, so it is the only coverage that build's unit ordering
# gets on a machine with no KVM or the wrong architecture.
#
# `skills` likewise: what the assistant pane was given to read is a store path
# hanging off the evaluated configuration, and the failures it guards against --
# a skill opencode silently refuses to register, or one naming a command this
# platform has not got -- are all visible without booting anything.
#
# `skills` is nonetheless the one eval-only test that is still bound to the host
# architecture, because a store path has to be *realised*: console.nix builds the
# skills directory and the instructions file from the platform's own nixpkgs, so
# `--platform spark` on an x86_64 machine is a platform mismatch rather than a
# verdict. `hardware` and `units` read values alone and have no such limit.
EVAL_ONLY_TESTS=(hardware units skills)

# Of those, the ones still bound to this machine's architecture -- see the
# `skills` paragraph above. Membership of EVAL_ONLY_TESTS is what lifts the KVM
# and disk requirements; membership here puts the architecture check and the
# `--platform all` refusal back, which that membership had taken away. Without
# it `appliance-test skills --platform all` was accepted and ran `skills` for
# spark and nuc12 on an x86_64 workstation, failing deep inside nix-build --
# "a platform mismatch rather than a verdict", as the paragraph above puts it.
HOST_ARCH_TESTS=(skills)

# What `--platform all` is for: eval-only *and* architecture-free. Spelled out
# rather than computed, because the usage text prints it.
ARCH_FREE_TESTS=(hardware units)
# Resolved in Main beside SELECTION_NEEDS_VM, and for the same reason.
SELECTION_NEEDS_HOST_ARCH=false
# Resolved in Main, once, like NIX_SYSTEM -- not computed inside a condition,
# which would switch `set -e` off for the duration.
SELECTION_NEEDS_VM=true

# Whether to ask for the `kvm` system feature. "auto" is resolved in
# validate_environment by probing /dev/kvm; --kvm and --no-kvm state it instead.
# Without the feature, nixpkgs starts qemu with `-machine accel=kvm:tcg`, so it
# falls back to software emulation by itself -- correct, and five to ten times
# slower. See `requireKvm` in nixos/default.nix.
USE_KVM=auto

# Free space, in GiB, that nix should collect garbage to maintain during the
# build. 0 does not pass the options at all. Nix only honours them from the
# command line for a trusted user -- an untrusted one gets a warning and the
# daemon's own settings, which is why nixos/README.md documents the permanent
# form as well.
MIN_FREE_GB=25
MAX_FREE_GB=100

# Collect garbage once the tests are done, for the case where the space they
# needed was borrowed rather than spare.
COLLECT_GARBAGE=false

VERBOSE=false

# variables defined in vars.sh, here for shellcheck:
LOOM_HOSTS_FQDN=()
NAMESPACE=""
LOOM_CHAT_MODEL=""

# Built from LOOM_HOSTS_FQDN by resolve_loom_values.
LOOM_HOSTS_JSON=""

#
# Helpers
#

# The attribute in nixos/default.nix behind each short name.
test_attribute(){
    case "${1}" in
        appliance)          printf 'tests.appliance'                  ;;
        hardware)           printf 'tests.applianceHardware'          ;;
        units)              printf 'tests.applianceUnits'             ;;
        skills)             printf 'tests.applianceSkills'            ;;
        install)            printf 'tests.applianceInstall'           ;;
        dhcp)               printf 'tests.applianceDhcp'              ;;
        portal)             printf 'tests.appliancePortal'            ;;
        wifi)               printf 'tests.applianceWifi'              ;;
        mouse)              printf 'tests.applianceMouse'             ;;
        usb-ingest)         printf 'tests.applianceUsbIngest'         ;;
        interface-fallback) printf 'tests.applianceInterfaceFallback' ;;
        key-store)          printf 'tests.applianceKeyStore'          ;;
        debug)              printf 'tests.applianceDebug'             ;;
        *)                  return 1                                  ;;
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
        echo >&2 "    Run this through devenv: 'appliance-test' passes --nixpkgs for you."
        echo >&2 "    To drive the script directly, pass --nixpkgs PATH yourself."
        exit 1
    fi
    if [[ ! -e "${NIXPKGS}/nixos/lib/eval-config.nix" ]]; then
        echo >&2 "[!] Error: not a nixpkgs source: ${NIXPKGS}"
        exit 1
    fi

    if [[ -z "${NIXOS_HARDWARE}" ]]; then
        echo >&2 "[!] Error: no nixos-hardware given."
        echo >&2 "    Run this through devenv: 'appliance-test' passes --nixos-hardware for you."
        echo >&2 "    To drive the script directly, pass --nixos-hardware PATH yourself."
        exit 1
    fi
    if [[ ! -e "${NIXOS_HARDWARE}/common/pc/ssd/default.nix" ]]; then
        echo >&2 "[!] Error: not a nixos-hardware source: ${NIXOS_HARDWARE}"
        exit 1
    fi

    # Everything from here down is about booting a VM, except the architecture
    # check: an eval-only selection skips the KVM and disk requirements, and a
    # HOST_ARCH_TESTS selection still has to run on a matching machine.
    if [[ "${SELECTION_NEEDS_VM}" = false && "${SELECTION_NEEDS_HOST_ARCH}" = false ]]; then
        return 0
    fi

    # No --allow-cross to go with build-appliance-image's: an image can be built
    # under emulation and flashed, but a test has to boot the kernel it built --
    # and `skills` has to realise a store path built from the platform's own
    # nixpkgs.
    if [[ "${NIX_SYSTEM}" != "${HOST_ARCH}-linux" ]]; then
        echo >&2 "[!] Error: platform '${PLATFORM}' is ${NIX_SYSTEM}, but this host is ${HOST_ARCH}."
        echo >&2 "    These tests cannot be cross-built. Run them on a ${NIX_SYSTEM} host,"
        echo >&2 "    or pass --platform for one that matches this machine."
        echo >&2 "    'appliance-test hardware units --platform ${PLATFORM}' reads values"
        echo >&2 "    alone and runs here."
        exit 1
    fi

    if [[ "${SELECTION_NEEDS_VM}" = false ]]; then
        return 0
    fi

    # Read *and* write, because that is the test nix itself applies before it
    # advertises the `kvm` feature, and qemu opens the device read-write. A
    # readable-only /dev/kvm would have us ask for a feature this daemon does
    # not have, and the build would fail before it started.
    if [[ "${USE_KVM}" = auto ]]; then
        if [[ -r /dev/kvm && -w /dev/kvm ]]; then
            USE_KVM=true
        else
            USE_KVM=false
        fi
    fi

    if [[ "${USE_KVM}" = true ]]; then
        if [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then
            echo >&2 "[!] Error: --kvm was given, but /dev/kvm is not readable and writable here."
            echo >&2 "    Drop --kvm to let qemu fall back to software emulation, or run this on"
            echo >&2 "    a host with nested virtualisation enabled."
            exit 1
        fi
    else
        if [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then
            echo "[!] Note: /dev/kvm is not usable here -- present, readable and writable is"
            echo "[!] what counts."
        fi
        echo "[!] Note: building without the 'kvm' system feature; qemu falls back to software"
        echo "[!] emulation. Expect five to ten times the runtime of a KVM host."
        echo "[!] Pass --kvm to fail instead of taking the slow path."
    fi

    # The store, not this checkout: the closure is built there and the VM disks
    # are written to the build directory beside it, and the two are routinely on
    # different filesystems. A note rather than an error -- min-free below may
    # well make the room -- but it is worth saying before the twenty minutes
    # rather than after them.
    store_dir="${NIX_STORE_DIR:-/nix/store}"
    free_gb="$(df --block-size=1G --output=avail "${store_dir}" | tail --lines=1 | tr --delete ' ')"
    if (( free_gb < 15 )); then
        echo "[!] Note: ${free_gb} GB free on the filesystem holding ${store_dir}. A run builds"
        echo "[!] a ~3.5 GB appliance closure and writes its VM disks beside it."
        echo "[!] 'nix-collect-garbage -d' and 'nix store optimise' free what earlier runs left."
    fi
}

# Records its own failure rather than being called in a condition, which would
# switch `set -e` off for everything it runs.
run_test(){
    local name="${1}" platform="${2}" attribute nix_system label
    attribute="$(test_attribute "${name}")"
    nix_system="$(platform_system "${platform}")"

    common_nix_args "${platform}" "${nix_system}" "${attribute}" "${CONTEXT_DIR}"
    local args=(
        "${NIX_COMMON_ARGS[@]}"
        # A test result is a log, not something to keep: an out-link would root
        # the whole closure and defeat the garbage collection above.
        --no-out-link
    )
    if (( MIN_FREE_GB > 0 )); then
        args+=(
            --option min-free "$(( MIN_FREE_GB * 1024 * 1024 * 1024 ))"
            --option max-free "$(( MAX_FREE_GB * 1024 * 1024 * 1024 ))"
        )
    fi
    # Passed only when the feature is being dropped, so an ordinary KVM run
    # produces exactly the arguments nixos/README.md documents.
    if [[ "${USE_KVM}" = false ]]; then
        args+=(--arg requireKvm false)
    fi
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--show-trace)
    fi

    # The platform is in the label as well as the header because a --platform
    # all run reports several results for the same short name.
    label="${name} (${platform})"

    if [[ "${SELECTION_NEEDS_VM}" = true ]]; then
        echo "[*] Running: ${name} (${attribute}, ${platform}, kvm=${USE_KVM})"
    else
        echo "[*] Running: ${name} (${attribute}, ${platform})"
    fi
    if nix-build "${args[@]}"; then
        return 0
    fi
    FAILED+=("${label}")
    echo "[!] Failed: ${label}"
}

collect_garbage(){
    if [[ "${COLLECT_GARBAGE}" = false ]]; then
        return 0
    fi
    echo "[*] Collecting garbage"
    # Without --delete-old: profile generations are the user's, not this
    # script's, business.
    nix-collect-garbage
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>] [<test>...]"
    echo "  tests: ${KNOWN_TESTS[*]} (default: all of them, in that order)"
    echo "  -h|--help                     show this help"
    echo "  -v|--verbose                  pass --show-trace to nix-build"
    echo "  -p|--platform PLATFORM        box to build the nodes for: ${KNOWN_PLATFORMS[*]}"
    echo "                                (default: the one matching this machine). 'all' runs"
    echo "                                every platform, for the targets that need neither a"
    echo "                                VM nor this machine's architecture:"
    echo "                                ${ARCH_FREE_TESTS[*]}"
    echo "                                ('skills' boots nothing either, but realises a store"
    echo "                                path from the platform's own nixpkgs, so it needs a"
    echo "                                matching host.)"
    echo "  --kvm                         fail unless /dev/kvm is usable (default: detect)"
    echo "  --no-kvm                      build without the 'kvm' system feature, so qemu falls"
    echo "                                back to software emulation -- correct, and much slower"
    echo "  --min-free GB                 free space nix should collect garbage to keep"
    echo "                                during the build, 0 to not ask (default: ${MIN_FREE_GB})"
    echo "  --max-free GB                 how far a collection goes once it starts (default: ${MAX_FREE_GB})"
    echo "  --gc                          collect garbage after the tests have run"
    echo "  --nixpkgs NIXPKGS             nixpkgs source (required; 'appliance-test' passes it)"
    echo "  --nixos-hardware PATH         nixos-hardware source (required; passed the same way)"
}

#
# Main
#

TESTS=()
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
            case " ${KNOWN_PLATFORMS[*]} all " in
                *" ${PLATFORM} "*)
                    :
                ;;
                *)
                    echo >&2 "[!] Error: unknown platform: ${PLATFORM}"
                    echo >&2 "    Known platforms: ${KNOWN_PLATFORMS[*]} (or 'all')"
                    exit 1
                ;;
            esac
            shift
        ;;
        --kvm)
            USE_KVM=true
            shift
        ;;
        --no-kvm)
            USE_KVM=false
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
        --gc)
            COLLECT_GARBAGE=true
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
        -*)
            echo >&2 "[!] Error: unknown option: ${1}"
            usage
            exit 1
        ;;
        *)
            # Matched against the list rather than by calling test_attribute,
            # which in a condition would silently disable `set -e` inside it --
            # the same reason --platform matches KNOWN_PLATFORMS below.
            case " ${KNOWN_TESTS[*]} " in
                *" ${1} "*)
                    TESTS+=("${1}")
                ;;
                *)
                    echo >&2 "[!] Error: unknown test: ${1}"
                    echo >&2 "    Known tests: ${KNOWN_TESTS[*]}"
                    exit 1
                ;;
            esac
            shift
        ;;
    esac
done

HOST_ARCH="$(uname -m)"

if [[ -z "${PLATFORM}" ]]; then
    # The platform matching this machine -- see `default_platform_for_arch` in
    # cicd/appliance_common.sh, which is the one copy of this rule.
    PLATFORM="$(default_platform_for_arch)"
fi

if (( ${#TESTS[@]} == 0 )); then
    TESTS=("${KNOWN_TESTS[@]}")
fi

# True as soon as one selected test boots something. Computed here rather than
# in a condition inside validate_environment, for the `set -e` reason above.
SELECTION_NEEDS_VM=false
SELECTION_NEEDS_HOST_ARCH=false
for test in "${TESTS[@]}"; do
    case " ${EVAL_ONLY_TESTS[*]} " in
        *" ${test} "*)
            :
        ;;
        *)
            SELECTION_NEEDS_VM=true
        ;;
    esac
    case " ${HOST_ARCH_TESTS[*]} " in
        *" ${test} "*)
            SELECTION_NEEDS_HOST_ARCH=true
        ;;
        *)
            :
        ;;
    esac
done

# `all` is for the eval-only targets: nothing is built for a machine, so the
# three platforms are reachable from whichever one you have. A VM test is not,
# and refusing here says so before the first of them boots.
PLATFORMS=("${PLATFORM}")
if [[ "${PLATFORM}" = all ]]; then
    if [[ "${SELECTION_NEEDS_VM}" = true || "${SELECTION_NEEDS_HOST_ARCH}" = true ]]; then
        echo >&2 "[!] Error: --platform all covers the targets that need neither a VM nor"
        echo >&2 "    this machine's architecture: ${ARCH_FREE_TESTS[*]}."
        echo >&2 "    The rest build something for one machine -- a kernel, or a store path"
        echo >&2 "    from the platform's own nixpkgs -- so each needs a host of its own"
        echo >&2 "    architecture. Name a platform, or select only those."
        exit 1
    fi
    PLATFORMS=("${KNOWN_PLATFORMS[@]}")
fi

# The architecture check in validate_environment asks about one platform, and
# only a VM selection reaches it -- which is exactly when there is one.
NIX_SYSTEM="$(platform_system "${PLATFORMS[0]}")"

validate_environment
resolve_loom_values

FAILED=()
RAN=0
for platform in "${PLATFORMS[@]}"; do
    for test in "${TESTS[@]}"; do
        run_test "${test}" "${platform}"
        RAN=$(( RAN + 1 ))
    done
done

collect_garbage

if (( ${#FAILED[@]} > 0 )); then
    echo >&2 "[!] ${#FAILED[@]} of ${RAN} failed: ${FAILED[*]}"
    exit 1
fi

echo "[*] All ${RAN} passed: ${TESTS[*]} (${PLATFORMS[*]})"
