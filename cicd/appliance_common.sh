#!/usr/bin/env bash
# Helpers the four appliance scripts share.
#
# Sourced, never executed -- the same pattern as cicd/ci_helpers.sh, but bash
# rather than POSIX sh, because everything that sources this is bash already and
# `resolve_loom_values` needs arrays.
#
# What is in here is what was written out four times: build_appliance_image.sh,
# appliance_eval.sh, run_appliance_tests.sh and run_appliance_vm.sh. The one
# that matters is `platform_system` -- it is the platform-to-architecture table,
# so a fourth platform used to mean four identical edits with nothing to catch a
# missed one. The nixSystem assertion in nixos/default.nix catches a *wrong*
# entry at evaluation time; it cannot catch a missing one, which just makes a
# script return 1 and report an unknown platform.
#
# Every caller sets this before sourcing -- it is the repository root, and
# `resolve_loom_values` reads vars.sh out of it. Declared here so the failure is
# a named error rather than a source of "/vars.sh".
: "${CONTEXT_DIR:?appliance_common.sh: set CONTEXT_DIR before sourcing this}"

check_command(){
    if ! command -v "${1}" > /dev/null; then
        echo >&2 "[!] Error: required command not found: ${1}"
        exit 1
    fi
}

# The architecture each platform is. Mirrors `nixSystem` in the matching
# nixos/platforms/<id>.nix, which is the authority -- nixos/default.nix asserts
# that the two agree, so a drift here fails during evaluation rather than on the
# box.
platform_system(){
    case "${1}" in
        spark)  printf 'aarch64-linux' ;;
        evo-x2) printf 'x86_64-linux'  ;;
        nuc12)  printf 'x86_64-linux'  ;;
        *)      return 1               ;;
    esac
}

# The values the appliance is built with, sourced from this checkout -- which is
# also what the image embeds, so the two cannot disagree. vars.sh is the single
# source of truth for all of them; tests/appliance.nix asserts the appliance
# restates them correctly, and passing defaults instead would put a different
# box in a VM from the one on a stick.
#
# Sets LOOM_HOSTS_JSON, plus everything vars.sh itself exports -- NAMESPACE and
# LOOM_CHAT_MODEL above all.
resolve_loom_values(){
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${CONTEXT_DIR}/vars.sh"
    # One jq rather than two through a pipe, so nothing masks an exit status and
    # the quoting is jq's problem rather than the shell's.
    #
    # LOOM_HOSTS_FQDN comes from the vars.sh sourced just above, and
    # LOOM_HOSTS_JSON is read by whichever script sourced this file.
    # shellcheck disable=SC2034,SC2154
    LOOM_HOSTS_JSON="$(
        jq --compact-output --null-input '$ARGS.positional' \
            --args "${LOOM_HOSTS_FQDN[@]}"
    )"
}
