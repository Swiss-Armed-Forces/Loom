#!/usr/bin/env bash
# Instantiate the appliance image for every platform, building nothing.
#
# The one appliance check that has to be a shell script: it is nix-instantiate
# plumbing -- a dozen `--arg`s, one of them a JSON list built from vars.sh -- and
# nothing about it is a test. The tests themselves are pytest suites run by
# `appliance-pytest` from devenv.nix, next to every other test runner in this
# repository.
#
# cicd/run_appliance_tests.sh boots real machines: it wants KVM, it needs a host of
# the platform's own architecture, and it costs minutes per target. None of that is
# true here, which is why this is the tier .gitlab-ci.yml runs on every pipeline
# while the VM tests are gated on what the merge request touched.
#
# What it catches: a module that no longer evaluates, an option renamed out from
# under us, a failed assertion, and a typo in a test file that would otherwise
# surface twenty minutes into a VM boot. Evaluation builds nothing, so this is also
# the only thing that covers the Spark from an x86_64 machine.
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)

# As in cicd/run_appliance_tests.sh: both come from devenv's inputs, so
# devenv.lock stays the only pin for either.
NIXPKGS=""
NIXOS_HARDWARE=""

# Every platform by default -- that is the point of a check that builds nothing.
# Must agree with `platformModules` in nixos/default.nix.
KNOWN_PLATFORMS=(spark evo-x2 nuc12)
PLATFORMS=()

# Both resolved in Main, once. HOST_PLATFORM is the platform whose tests are
# evaluated as well as its image; empty on an architecture no platform claims,
# which costs nothing here because evaluation is architecture-independent.
HOST_ARCH=""
HOST_PLATFORM=""

VERBOSE=false

# variables defined in vars.sh, here for shellcheck:
LOOM_HOSTS_FQDN=()
NAMESPACE=""
LOOM_CHAT_MODEL=""

# Built from LOOM_HOSTS_FQDN by resolve_loom_values.
LOOM_HOSTS_JSON=""

# Appended to by instantiate, so one platform failing does not hide the next.
FAILED=()

#
# Helpers
#

check_command(){
    if ! command -v "${1}" > /dev/null; then
        echo >&2 "[!] Error: required command not found: ${1}"
        exit 1
    fi
}

# Must agree with `platform_system` in cicd/run_appliance_tests.sh and
# cicd/build_appliance_image.sh, which mirror `nixSystem` in
# nixos/platforms/<id>.nix. No host-architecture check to go with theirs,
# deliberately: evaluating aarch64 on x86_64 builds nothing, and it is the only
# way the Spark is covered at all outside a Spark.
platform_system(){
    case "${1}" in
        spark)  printf 'aarch64-linux' ;;
        evo-x2) printf 'x86_64-linux'  ;;
        nuc12)  printf 'x86_64-linux'  ;;
        *)      return 1               ;;
    esac
}

#
# Steps
#

validate_environment(){
    local command icon magic store_dir free_gb kvm

    for command in git jq nix-instantiate; do
        check_command "${command}"
    done

    if [[ -z "${NIXPKGS}" ]]; then
        echo >&2 "[!] Error: no nixpkgs given."
        echo >&2 "    Run this through devenv: 'appliance-eval' passes --nixpkgs for you."
        echo >&2 "    To drive the script directly, pass --nixpkgs PATH yourself."
        exit 1
    fi
    if [[ ! -e "${NIXPKGS}/nixos/lib/eval-config.nix" ]]; then
        echo >&2 "[!] Error: not a nixpkgs source: ${NIXPKGS}"
        exit 1
    fi

    if [[ -z "${NIXOS_HARDWARE}" ]]; then
        echo >&2 "[!] Error: no nixos-hardware given."
        echo >&2 "    Run this through devenv: 'appliance-eval' passes --nixos-hardware for you."
        echo >&2 "    To drive the script directly, pass --nixos-hardware PATH yourself."
        exit 1
    fi
    if [[ ! -e "${NIXOS_HARDWARE}/common/pc/ssd/default.nix" ]]; then
        echo >&2 "[!] Error: not a nixos-hardware source: ${NIXOS_HARDWARE}"
        exit 1
    fi

    # Four bytes, and the one thing an evaluation cannot catch: branding.nix
    # embeds this PNG and guards on its magic number at *build* time, so an
    # unmaterialised git-lfs pointer surfaces deep inside a VM test instead of
    # here. The devenv shell runs `git lfs pull` on entry, so this is a
    # fail-fast, not an expected failure.
    icon="${CONTEXT_DIR}/Frontend/public/web-app-manifest-512x512.png"
    magic="$(head --bytes=4 "${icon}" | od --address-radix=n --format=x1 | tr --delete ' \n')"
    if [[ "${magic}" != "89504e47" ]]; then
        echo >&2 "[!] Error: ${icon} is not a PNG."
        echo >&2 "    The git-lfs payloads are not materialised here. Run: git lfs pull"
        exit 1
    fi

    # Printed rather than acted on: this is the cheap job that runs everywhere, so
    # it is the one place a runner says what it can do. Whether the VM tests can use
    # KVM on a given machine is otherwise only discoverable by starting them.
    store_dir="${NIX_STORE_DIR:-/nix/store}"
    free_gb="$(df --block-size=1G --output=avail "${store_dir}" | tail --lines=1 | tr --delete ' ')"
    if [[ -r /dev/kvm && -w /dev/kvm ]]; then
        kvm="usable"
    else
        kvm="not usable"
    fi
    echo "[*] Host: ${HOST_ARCH}, /dev/kvm ${kvm}, ${free_gb} GB free on ${store_dir}"
}

# Sourced from this checkout, which is also what the appliance embeds, so the
# two cannot disagree. `box` throws without the host list.
resolve_loom_values(){
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${CONTEXT_DIR}/vars.sh"
    LOOM_HOSTS_JSON="$(printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" |
        jq --raw-input . | jq --slurp --compact-output .)"
}

# One invocation per platform and attribute. The results are thrown away --
# nothing is built, and the .drv paths are not the point.
#
# Takes a variant label and then any extra nix arguments, for the one case that
# needs them: an option that changes which modules are active produces a
# different evaluation, and evaluating only the default would let it rot. See
# the --debug pass in evaluate_platforms.
#
# The label is separate from the arguments rather than derived from them so that
# the progress line stays one readable line -- the --debug pass carries a whole
# SSH public key, which is not something to print twice per platform.
instantiate(){
    local platform="${1}" attribute="${2}" variant="${3}" system label
    shift 3
    system="$(platform_system "${platform}")"

    local args=(
        "${CONTEXT_DIR}/nixos"
        --attr "${attribute}"
        --arg nixpkgs "${NIXPKGS}"
        --arg nixosHardware "${NIXOS_HARDWARE}"
        --argstr system "${system}"
        --argstr platform "${platform}"
        --arg repoSrc "${CONTEXT_DIR}"
        --argstr loomHostsJson "${LOOM_HOSTS_JSON}"
        --argstr loomNamespace "${NAMESPACE}"
        --argstr loomChatModel "${LOOM_CHAT_MODEL}"
        # Nothing is realised, so there is nothing to root -- and a root here
        # would be a gc root on every .drv this touches.
        --no-gc-warning
    )
    args+=("${@}")
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--show-trace)
    fi

    label="${attribute} (${platform}, ${system})${variant:+ ${variant}}"

    echo "[*] Evaluating: ${label}"
    if nix-instantiate "${args[@]}" > /dev/null; then
        return 0
    fi
    FAILED+=("${attribute} (${platform})${variant:+ ${variant}}")
    echo "[!] Failed: ${label}"
}

evaluate_platforms(){
    local platform

    for platform in "${PLATFORMS[@]}"; do
        # installerImage rather than box: installer.nix puts the appliance's own
        # toplevel into the stick's store image, so this covers both, plus the
        # installer and the cross-architecture image assembly.
        instantiate "${platform}" installerImage ''

        # The --debug build, which the pass above does not cover: nixos/debug.nix
        # is a whole module that is inert unless the flag is set, so without
        # this an option renamed under it would evaluate cleanly here and fail
        # the first time somebody actually needed a debug stick -- which is by
        # definition a moment when something is already going wrong.
        #
        # The key is a throwaway with no private half anywhere: this evaluates
        # the module, it does not build anything that could be booted.
        instantiate "${platform}" installerImage '--debug' \
            --arg debugAccess true \
            --argstr debugSshAuthorizedKey \
            'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEvaluationOnlyNotAKeyEvaluationOnlyNotA eval@loom'

        # The tests are evaluated for the platform that could run them. The
        # nodes import the same module list the image does, so evaluating them
        # for another platform re-checks what installerImage just checked; what
        # is wanted here is that tests/*.nix themselves still evaluate.
        if [[ "${platform}" = "${HOST_PLATFORM}" ]]; then
            instantiate "${platform}" tests ''
        fi
    done
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>]"
    echo "  -h|--help                     show this help"
    echo "  -v|--verbose                  pass --show-trace to nix-instantiate"
    echo "  -p|--platform PLATFORM        evaluate only this one: ${KNOWN_PLATFORMS[*]}"
    echo "                                (repeatable; default: all of them)"
    echo "  --nixpkgs NIXPKGS             nixpkgs source ('appliance-eval' passes it)"
    echo "  --nixos-hardware PATH         nixos-hardware source (required the same way)"
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
            case " ${KNOWN_PLATFORMS[*]} " in
                *" ${1?Missing PLATFORM} "*)
                    PLATFORMS+=("${1}")
                ;;
                *)
                    echo >&2 "[!] Error: unknown platform: ${1}"
                    echo >&2 "    Known platforms: ${KNOWN_PLATFORMS[*]}"
                    exit 1
                ;;
            esac
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
        *)
            echo >&2 "[!] Error: unknown argument: ${1}"
            usage
            exit 1
        ;;
    esac
done

if (( ${#PLATFORMS[@]} == 0 )); then
    PLATFORMS=("${KNOWN_PLATFORMS[@]}")
fi

HOST_ARCH="$(uname -m)"
case "${HOST_ARCH}" in
    x86_64)
        # As cicd/run_appliance_tests.sh picks it: nuc12 is the same
        # architecture, and evo-x2 is the one that declares a GPU.
        HOST_PLATFORM="evo-x2"
    ;;
    aarch64|arm64)
        HOST_PLATFORM="spark"
    ;;
    *)
        HOST_PLATFORM=""
    ;;
esac

validate_environment
resolve_loom_values
evaluate_platforms

if (( ${#FAILED[@]} > 0 )); then
    echo >&2 "[!] ${#FAILED[@]} failed to evaluate: ${FAILED[*]}"
    exit 1
fi

echo "[*] All evaluated: ${PLATFORMS[*]}"
