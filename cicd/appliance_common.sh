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
# `common_nix_args` is the same argument made about nixos/default.nix's own
# top-level arguments, which were also written out four times; `image_file` and
# `write_debug_ssh_config` about two smaller ones.
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

# The boxes this repository builds appliance images for.
#
# One list, here, beside `platform_system` -- which is already bash-with-arrays
# by its own docstring. It used to be written out in all four scripts that use
# it, along with the identical validating `case`, and the header above claims to
# have ended exactly that: a fifth platform meant four identical edits with
# nothing to catch a missed one. A stale copy is not silent (the script refuses
# the new platform by name) but it is four discoveries, one per script, each the
# first time somebody runs it.
KNOWN_PLATFORMS=(spark evo-x2 nuc12)

# Refuse anything that is not one of them, with the list in the message.
#
# `case` rather than a call to `platform_system`: that returns 1 for an unknown
# platform, and calling it inside a condition disables `set -e` for its whole
# body.
require_platform(){
    local platform="${1}"
    case " ${KNOWN_PLATFORMS[*]} " in
        *" ${platform} "*)
            return 0
        ;;
        *)
            echo >&2 "[!] Error: unknown platform: ${platform}"
            echo >&2 "    Known platforms: ${KNOWN_PLATFORMS[*]}"
            exit 1
        ;;
    esac
}

# The platform to use when none was named: the one matching this machine.
#
# Every caller that has a default has the same one, and for the same reason --
# the VM tests boot a real kernel, so a cross-architecture default would only
# ever be wrong.
default_platform_for_arch(){
    local arch
    arch="$(uname -m)"
    case "${arch}" in
        aarch64) printf 'spark'  ;;
        x86_64)  printf 'evo-x2' ;;
        *)
            echo >&2 "[!] Error: no appliance platform for this architecture: ${arch}"
            exit 1
        ;;
    esac
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

# The nix arguments every entry point into nixos/default.nix passes, in an array
# the caller then appends its own to -- --out-link, --no-out-link,
# --no-gc-warning, --show-trace, and whatever else is that script's business.
#
# Written out four times before this existed, which is the thing the header of
# this file says it is here to stop: adding a top-level argument to
# nixos/default.nix meant four identical edits with nothing to catch a missed
# one.
#
# `system` is a parameter rather than derived from `platform`, because
# build_appliance_image.sh's `--system` can override it -- the cross-build case.
# Callers that have no such flag pass `platform_system "${platform}"`.
#
# Set as a global rather than printed, so that nothing has to be re-split: these
# values contain spaces (LOOM_CHAT_MODEL above all) and a round trip through word
# splitting is exactly how that breaks.
#
# NIXPKGS, NIXOS_HARDWARE, NAMESPACE and LOOM_CHAT_MODEL all come from whichever
# script sourced this file -- the last two by way of `resolve_loom_values` above.
# shellcheck disable=SC2034
NIX_COMMON_ARGS=()
# shellcheck disable=SC2034,SC2154
common_nix_args(){
    local platform="${1}" system="${2}" attribute="${3}" repo_src="${4}"

    NIX_COMMON_ARGS=(
        "${CONTEXT_DIR}/nixos"
        --attr "${attribute}"
        --arg nixpkgs "${NIXPKGS}"
        --arg nixosHardware "${NIXOS_HARDWARE}"
        --argstr system "${system}"
        --argstr platform "${platform}"
        # The working tree, filtered by `loomSrc` in nixos/default.nix -- which
        # is what makes passing it cheap. Unfiltered it would copy every
        # .pytest_tmp and node_modules in the checkout into the store, once per
        # run. build_appliance_image.sh passes its tagged clone here instead.
        --arg repoSrc "${repo_src}"
        --argstr loomHostsJson "${LOOM_HOSTS_JSON}"
        --argstr loomNamespace "${NAMESPACE}"
        --argstr loomChatModel "${LOOM_CHAT_MODEL}"
    )
}

# Say so when --min-free cannot do anything.
#
# `min-free` and `max-free` are restricted settings: nix discards them from a
# caller outside `trusted-users`, and unlike a substituter there is no
# allow-list that lets one through. So `--min-free 50` on a machine whose
# developer is not a trusted user is accepted, printed in the help, and has no
# effect whatsoever.
#
# The warning is deliberately tied to the *outcome* rather than to the dropped
# flag. A machine that sets min-free in /etc/nix/nix.conf -- which is where it
# belongs, and what cicd/setup_devenv.py offers -- is already protected, and
# warning there would be noise nobody can act on. What matters is the case
# where nothing collects garbage at all: nix defaults min-free to 0, and a
# build that fills the disk takes the whole run with it.
warn_if_disk_budget_inert(){
    local requested_gb="${1}" info configured
    (( requested_gb > 0 )) || return 0

    # `"trusted":false` -- a JSON boolean, not the 0/1 the human-readable form
    # prints. Matched with bash's own regex rather than piped through sed
    # because the field is optional:
    # anything other than an explicit false means nix could not tell, which is
    # not the same as "untrusted" and must not warn.
    info="$(nix store info --json 2>/dev/null || true)"
    [[ "${info}" =~ \"trusted\"[[:space:]]*:[[:space:]]*false ]] || return 0

    # What the configuration files say, rather than what this invocation asked
    # for. Both the daemon and this client read /etc/nix/nix.conf, so a value
    # there is one the daemon will honour. NIX_CONFIG is emptied because inside
    # the devenv shell it carries settings that an untrusted caller has
    # discarded anyway. A min-free in the *user's* ~/.config/nix/nix.conf is
    # read here and ignored by the daemon, so this can stay quiet when it
    # should not -- erring towards silence, which is the harmless direction.
    configured="$(NIX_CONFIG='' nix config show min-free 2>/dev/null || true)"
    [[ "${configured}" = "0" || -z "${configured}" ]] || return 0

    echo "[!] --min-free ${requested_gb} will be ignored: it is a restricted" >&2
    echo "[!] setting and this account is not in nix's trusted-users. Nothing" >&2
    echo "[!] will collect garbage during this build, so a long run can fill" >&2
    echo "[!] the disk and take itself down with it." >&2
    echo "[!] Put it in /etc/nix/nix.conf instead, where the daemon reads it:" >&2
    echo "[!]     min-free = $(( requested_gb * 1024 * 1024 * 1024 ))" >&2
    echo "[!] See the disk budget section in nixos/README.md." >&2
}

# The image inside a `nix-build` out-link.
#
# -L is required: the out-link is a symlink into the Nix store, and find does
# not follow symlinks by default.
image_file(){
    local found
    found="$(find -L "${1}" -name '*.raw' -type f)"
    printf '%s\n' "${found%%$'\n'*}"
}

# One ready-to-use ssh_config, so that reaching a --debug box needs no knowledge
# the build did not already have.
#
# `accept-new` rather than a baked host key. It is already non-interactive,
# which is what an agent needs, and it keeps a second secret out of /nix/store:
# a host private key passed through Nix would be world-readable on the stick,
# and the WiFi passphrase is quite enough of that.
#
# `IdentitiesOnly` because a developer's ssh-agent will otherwise offer its own
# keys first and the box -- which knows exactly one -- refuses the lot until
# MaxAuthTries runs out, which reads as "the key did not work".
#
# Shared because the two callers write the identical seven directives and the
# same chmod: build_appliance_image.sh for a stick and for the same image under
# `appliance-vm box --debug`, and run_appliance_vm.sh for its own persistent
# VM. Only `host` and `port` differ, which is what those parameters are for.
# The key directory itself is not shared -- one is an ephemeral mktemp, the
# other lives in the VM's state directory -- so the caller sets DEBUG_KEY_DIR,
# as it sets LOOM_USER.
# shellcheck disable=SC2154
write_debug_ssh_config(){
    local file="${1}" host="${2}" port="${3}" generator="${4}" note="${5}"
    local cleanup="${6}"

    cat > "${file}" <<EOF
# Generated by ${generator}
# ${note}
#
# Use it with:  ssh -F ${file} loom-appliance
# ${cleanup}
Host loom-appliance
    HostName ${host}
    Port ${port}
    User ${LOOM_USER}
    IdentityFile ${DEBUG_KEY_DIR}/id_ed25519
    IdentitiesOnly yes
    UserKnownHostsFile ${DEBUG_KEY_DIR}/known_hosts
    StrictHostKeyChecking accept-new
EOF
    chmod 0600 "${file}"
}
