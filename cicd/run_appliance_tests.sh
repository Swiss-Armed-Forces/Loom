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
KNOWN_TESTS=(install interface-fallback wifi usb-ingest appliance)

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
        install)            printf 'tests.applianceInstall'           ;;
        wifi)               printf 'tests.applianceWifi'              ;;
        usb-ingest)         printf 'tests.applianceUsbIngest'         ;;
        interface-fallback) printf 'tests.applianceInterfaceFallback' ;;
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

    # No --allow-cross to go with build-appliance-image's: an image can be built
    # under emulation and flashed, but a test has to boot the kernel it built.
    if [[ "${NIX_SYSTEM}" != "${HOST_ARCH}-linux" ]]; then
        echo >&2 "[!] Error: platform '${PLATFORM}' is ${NIX_SYSTEM}, but this host is ${HOST_ARCH}."
        echo >&2 "    The tests boot a VM, so they cannot be cross-built. Run them on a"
        echo >&2 "    ${NIX_SYSTEM} host, or pass --platform for one that matches this machine."
        exit 1
    fi

    # Not fatal: qemu falls back to software emulation, which works and is slow.
    # nixos/README.md says how to drop the requiredSystemFeatures for that.
    if [[ ! -r /dev/kvm ]]; then
        echo "[!] Note: /dev/kvm is not readable. Without KVM these tests are very slow,"
        echo "[!] and the 'nixos-test' system feature they ask for may not be available."
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
    local name="${1}" attribute
    attribute="$(test_attribute "${name}")"

    local args=(
        "${CONTEXT_DIR}/nixos"
        --attr "${attribute}"
        --arg nixpkgs "${NIXPKGS}"
        --argstr system "${NIX_SYSTEM}"
        --argstr platform "${PLATFORM}"
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
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--show-trace)
    fi

    echo "[*] Running: ${name} (${attribute}, ${PLATFORM})"
    if nix-build "${args[@]}"; then
        return 0
    fi
    FAILED+=("${name}")
    echo "[!] Failed: ${name}"
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
    echo "                                (default: the one matching this machine)"
    echo "  --min-free GB                 free space nix should collect garbage to keep"
    echo "                                during the build, 0 to not ask (default: ${MIN_FREE_GB})"
    echo "  --max-free GB                 how far a collection goes once it starts (default: ${MAX_FREE_GB})"
    echo "  --gc                          collect garbage after the tests have run"
    echo "  --nixpkgs NIXPKGS             nixpkgs source (required; 'appliance-test' passes it)"
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

NIX_SYSTEM="$(platform_system "${PLATFORM}")"

if (( ${#TESTS[@]} == 0 )); then
    TESTS=("${KNOWN_TESTS[@]}")
fi

validate_environment
resolve_loom_values

FAILED=()
for test in "${TESTS[@]}"; do
    run_test "${test}"
done

collect_garbage

if (( ${#FAILED[@]} > 0 )); then
    echo >&2 "[!] ${#FAILED[@]} of ${#TESTS[@]} failed: ${FAILED[*]}"
    exit 1
fi

echo "[*] All ${#TESTS[@]} passed: ${TESTS[*]}"
