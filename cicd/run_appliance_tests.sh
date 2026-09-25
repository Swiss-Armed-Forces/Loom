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
KNOWN_PLATFORMS=(spark evo-x2 nuc12)
# Both resolved in Main, once, rather than at each use.
NIX_SYSTEM=""
HOST_ARCH=""

# Short names, in the order they are run: cheapest first, so a mistake that
# breaks all of them is reported in a minute rather than in twenty.
#
# `hardware` is first because it is the only one that never boots anything: it
# reads the evaluated configuration and exits, in seconds. A nixos-hardware bump
# that broke every platform should be reported before the VM boots, not after.
KNOWN_TESTS=(hardware install interface-fallback key-store debug wifi mouse usb-ingest appliance)

# Targets that only read the evaluated configuration -- no kernel, no VM, and
# not even the appliance closure. The architecture check and the KVM and disk
# notes below all exist for VM tests and none of them apply to these, so a
# selection made up entirely of them lifts all three. That is what makes
# `appliance-test hardware --platform spark` work on an x86_64 workstation,
# which is exactly what you want to run after a nixos-hardware bump: all three
# platforms checked from one machine, in seconds.
EVAL_ONLY_TESTS=(hardware)
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

check_command(){
    if ! command -v "${1}" > /dev/null; then
        echo >&2 "[!] Error: required command not found: ${1}"
        exit 1
    fi
}

# Must agree with `platform_system` in cicd/build_appliance_image.sh, which in
# turn mirrors `nixSystem` in nixos/platforms/<id>.nix.
platform_system(){
    case "${1}" in
        spark)  printf 'aarch64-linux' ;;
        evo-x2) printf 'x86_64-linux'  ;;
        nuc12)  printf 'x86_64-linux'  ;;
        *)      return 1               ;;
    esac
}

# The attribute in nixos/default.nix behind each short name.
test_attribute(){
    case "${1}" in
        appliance)          printf 'tests.appliance'                  ;;
        hardware)           printf 'tests.applianceHardware'          ;;
        install)            printf 'tests.applianceInstall'           ;;
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

    # Everything from here down is about booting a VM. An eval-only selection
    # does none of that -- see EVAL_ONLY_TESTS -- so it skips the lot.
    if [[ "${SELECTION_NEEDS_VM}" = false ]]; then
        return 0
    fi

    # No --allow-cross to go with build-appliance-image's: an image can be built
    # under emulation and flashed, but a test has to boot the kernel it built.
    if [[ "${NIX_SYSTEM}" != "${HOST_ARCH}-linux" ]]; then
        echo >&2 "[!] Error: platform '${PLATFORM}' is ${NIX_SYSTEM}, but this host is ${HOST_ARCH}."
        echo >&2 "    The tests boot a VM, so they cannot be cross-built. Run them on a"
        echo >&2 "    ${NIX_SYSTEM} host, or pass --platform for one that matches this machine."
        echo >&2 "    'appliance-test hardware --platform ${PLATFORM}' needs no VM and runs here."
        exit 1
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

# Sourced from this checkout, which is also what the tests embed, so the two
# cannot disagree. vars.sh is the single source of truth for all three values;
# tests/appliance.nix asserts the appliance restates them correctly.
resolve_loom_values(){
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${CONTEXT_DIR}/vars.sh"
    LOOM_HOSTS_JSON="$(printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" |
        jq --raw-input . | jq --slurp --compact-output .)"
}

# Records its own failure rather than being called in a condition, which would
# switch `set -e` off for everything it runs.
run_test(){
    local name="${1}" platform="${2}" attribute nix_system label
    attribute="$(test_attribute "${name}")"
    nix_system="$(platform_system "${platform}")"

    local args=(
        "${CONTEXT_DIR}/nixos"
        --attr "${attribute}"
        --arg nixpkgs "${NIXPKGS}"
        --arg nixosHardware "${NIXOS_HARDWARE}"
        --argstr system "${nix_system}"
        --argstr platform "${platform}"
        # The working tree, filtered by `loomSrc` in nixos/default.nix -- which
        # is what makes passing it cheap. Unfiltered it would copy every
        # .pytest_tmp and node_modules in the checkout into the store, once per
        # run.
        --arg repoSrc "${CONTEXT_DIR}"
        --argstr loomHostsJson "${LOOM_HOSTS_JSON}"
        --argstr loomNamespace "${NAMESPACE}"
        --argstr loomChatModel "${LOOM_CHAT_MODEL}"
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
    echo "                                every platform, for the targets that boot nothing:"
    echo "                                ${EVAL_ONLY_TESTS[*]}"
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
    case "${HOST_ARCH}" in
        x86_64)
            # nuc12 is the same architecture; evo-x2 is the platform that
            # declares a GPU, so it exercises the toolchain assertions the
            # other two cannot.
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

if (( ${#TESTS[@]} == 0 )); then
    TESTS=("${KNOWN_TESTS[@]}")
fi

# True as soon as one selected test boots something. Computed here rather than
# in a condition inside validate_environment, for the `set -e` reason above.
SELECTION_NEEDS_VM=false
for test in "${TESTS[@]}"; do
    case " ${EVAL_ONLY_TESTS[*]} " in
        *" ${test} "*)
            :
        ;;
        *)
            SELECTION_NEEDS_VM=true
        ;;
    esac
done

# `all` is for the eval-only targets: nothing is built for a machine, so the
# three platforms are reachable from whichever one you have. A VM test is not,
# and refusing here says so before the first of them boots.
PLATFORMS=("${PLATFORM}")
if [[ "${PLATFORM}" = all ]]; then
    if [[ "${SELECTION_NEEDS_VM}" = true ]]; then
        echo >&2 "[!] Error: --platform all covers the targets that boot nothing: ${EVAL_ONLY_TESTS[*]}."
        echo >&2 "    The rest build a kernel for one machine and run it here, so each needs a"
        echo >&2 "    host of its own architecture. Name a platform, or select only those."
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
