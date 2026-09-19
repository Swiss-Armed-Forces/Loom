#!/usr/bin/env bash
# The appliance checks that boot nothing.
#
# cicd/run_appliance_tests.sh boots real machines: it wants KVM, it needs a host
# of the platform's own architecture, and it costs minutes per target. None of
# that is true here, which is why this is the tier .gitlab-ci.yml runs on every
# pipeline while the VM tests are gated on what the merge request touched.
#
# Three checks, each catching a different class of mistake:
#
#   * `eval` instantiates the stick -- and with it the appliance, which
#     installer.nix puts inside the stick's store image -- for *every* platform,
#     plus the tests for this one. Evaluation builds nothing, so this is the
#     only thing that covers the Spark from an x86_64 machine. It catches a
#     module that no longer evaluates, an option renamed out from under us, a
#     failed assertion, and a typo in a test file that would otherwise surface
#     twenty minutes into a VM boot.
#   * `bats` runs nixos/installer-scripts/tests. `auto_install_decision` decides
#     whether a disk is destroyed with nobody watching; the stick's own
#     derivation runs this suite, but building the stick costs a closure and
#     this costs a second.
#   * `pytest` runs nixos/usb-ingest/tests, for the same reason: the package's
#     checkPhase runs them, and running them here needs no package built.
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

# Short names, in the order they are run: the evaluation first, because it is
# the one that fails when nixos/ does not evaluate at all.
KNOWN_CHECKS=(eval bats pytest)
CHECKS=()

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

# Appended to by the check_* functions, so each may record its own failure and
# the rest still run.
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

    for command in git jq; do
        check_command "${command}"
    done

    case " ${CHECKS[*]} " in
        *" eval "*)
            check_command nix-instantiate

            if [[ -z "${NIXPKGS}" ]]; then
                echo >&2 "[!] Error: no nixpkgs given."
                echo >&2 "    Run this through devenv: 'appliance-check' passes --nixpkgs for you."
                echo >&2 "    To drive the script directly, pass --nixpkgs PATH yourself."
                exit 1
            fi
            if [[ ! -e "${NIXPKGS}/nixos/lib/eval-config.nix" ]]; then
                echo >&2 "[!] Error: not a nixpkgs source: ${NIXPKGS}"
                exit 1
            fi

            if [[ -z "${NIXOS_HARDWARE}" ]]; then
                echo >&2 "[!] Error: no nixos-hardware given."
                echo >&2 "    Run this through devenv: 'appliance-check' passes --nixos-hardware for you."
                echo >&2 "    To drive the script directly, pass --nixos-hardware PATH yourself."
                exit 1
            fi
            if [[ ! -e "${NIXOS_HARDWARE}/common/pc/ssd/default.nix" ]]; then
                echo >&2 "[!] Error: not a nixos-hardware source: ${NIXOS_HARDWARE}"
                exit 1
            fi
        ;;
        *)
            :
        ;;
    esac

    case " ${CHECKS[*]} " in
        *" bats "*)   check_command bats   ;;
        *)            :                    ;;
    esac
    case " ${CHECKS[*]} " in
        *" pytest "*) check_command python ;;
        *)            :                    ;;
    esac

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

    # Printed rather than acted on: this is the cheap job that runs everywhere,
    # so it is the one place a runner says what it can do. Whether the VM tests
    # can use KVM on a given machine is otherwise only discoverable by starting
    # them.
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
instantiate(){
    local platform="${1}" attribute="${2}" system
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
    if [[ "${VERBOSE}" = true ]]; then
        args+=(--show-trace)
    fi

    echo "[*] Evaluating: ${attribute} (${platform}, ${system})"
    if nix-instantiate "${args[@]}" > /dev/null; then
        return 0
    fi
    FAILED+=("eval: ${attribute} (${platform})")
    echo "[!] Failed: eval: ${attribute} (${platform})"
}

check_eval(){
    local platform

    for platform in "${PLATFORMS[@]}"; do
        # installerImage rather than box: installer.nix puts the appliance's own
        # toplevel into the stick's store image, so this covers both, plus the
        # installer and the cross-architecture image assembly.
        instantiate "${platform}" installerImage

        # The tests are evaluated for the platform that could run them. The
        # nodes import the same module list the image does, so evaluating them
        # for another platform re-checks what installerImage just checked; what
        # is wanted here is that tests/*.nix themselves still evaluate.
        if [[ "${platform}" = "${HOST_PLATFORM}" ]]; then
            instantiate "${platform}" tests
        fi
    done
}

check_bats(){
    echo "[*] Running: bats (nixos/installer-scripts/tests)"
    if bats "${CONTEXT_DIR}/nixos/installer-scripts/tests"; then
        return 0
    fi
    FAILED+=(bats)
    echo "[!] Failed: bats"
}

check_pytest(){
    echo "[*] Running: pytest (nixos/usb-ingest/tests)"
    # PYTHONPATH rather than an install: the package is built by
    # nixos/usb-ingest.nix for the appliance and is not in the devenv's
    # virtualenv, but its tests import it by name. Run from the repository root
    # so that pytest.ini applies -- above all `--basetemp=.pytest_tmp`, which is
    # what keeps the scratch out of RAM.
    if (
        cd "${CONTEXT_DIR}"
        PYTHONPATH="${CONTEXT_DIR}/nixos/usb-ingest" python -m pytest nixos/usb-ingest/tests
    ); then
        return 0
    fi
    FAILED+=(pytest)
    echo "[!] Failed: pytest"
}

# Called rather than dispatched through a condition, which would switch `set -e`
# off for everything the check runs.
run_check(){
    case "${1}" in
        eval)
            check_eval
        ;;
        bats)
            check_bats
        ;;
        pytest)
            check_pytest
        ;;
        *)
            echo >&2 "[!] Error: unknown check: ${1}"
            exit 1
        ;;
    esac
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>] [<check>...]"
    echo "  checks: ${KNOWN_CHECKS[*]} (default: all of them, in that order)"
    echo "  -h|--help                     show this help"
    echo "  -v|--verbose                  pass --show-trace to nix-instantiate"
    echo "  -p|--platform PLATFORM        evaluate only this one: ${KNOWN_PLATFORMS[*]}"
    echo "                                (repeatable; default: all of them)"
    echo "  --nixpkgs NIXPKGS             nixpkgs source (required for 'eval';"
    echo "                                'appliance-check' passes it)"
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
        -*)
            echo >&2 "[!] Error: unknown option: ${1}"
            usage
            exit 1
        ;;
        *)
            # Matched against the list rather than by calling run_check, which in
            # a condition would silently disable `set -e` inside it -- the same
            # reason --platform matches KNOWN_PLATFORMS above.
            case " ${KNOWN_CHECKS[*]} " in
                *" ${1} "*)
                    CHECKS+=("${1}")
                ;;
                *)
                    echo >&2 "[!] Error: unknown check: ${1}"
                    echo >&2 "    Known checks: ${KNOWN_CHECKS[*]}"
                    exit 1
                ;;
            esac
            shift
        ;;
    esac
done

if (( ${#CHECKS[@]} == 0 )); then
    CHECKS=("${KNOWN_CHECKS[@]}")
fi
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

for check in "${CHECKS[@]}"; do
    run_check "${check}"
done

if (( ${#FAILED[@]} > 0 )); then
    echo >&2 "[!] ${#FAILED[@]} failed: ${FAILED[*]}"
    exit 1
fi

echo "[*] All passed: ${CHECKS[*]}"
