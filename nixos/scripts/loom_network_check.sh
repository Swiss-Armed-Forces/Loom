# shellcheck shell=bash
#
# The body of `loom-network-check`, which puts a line about the appliance's
# wired port on the login screen: missing entirely, claimed automatically by
# the interface fallback, or matched properly and so worth saying nothing
# about. nixos/network.nix reads this file into the unit of the same name,
# behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, because a unit `script` string
# is linted by nothing at all -- not even the build-time pass a
# writeShellApplication gets. The repository runs `shellcheck -x -o all` over
# its .sh files, and this is how that reaches a systemd unit.
#
# `set -e` and nothing more, which is exactly what nixpkgs' makeJobScript
# wraps a unit `script` in (nixos/lib/systemd-lib.nix). Restated here so the
# linter reads the program that actually runs; adding `nounset` or `pipefail`
# would be a behaviour change rather than an extraction, and this unit sources
# a state file whose fields an older image may not have written.
set -e

readonly APPLIANCE_INTERFACE="${LOOM_APPLIANCE_INTERFACE:?nixos/network.nix must set this}"
readonly FALLBACK_RECORD="${LOOM_FALLBACK_RECORD:?nixos/network.nix must set this}"

# `60` sorts after box.nix's 50-loom.issue, so this lands under the banner
# and above agetty's press-ENTER prompt. loom-issue-fragment owns the rest:
# the indent, the rule, the atomic rename a getty respawning mid-write
# needs, the copy to the journal, and the rule that no backslash reaches
# an issue file.
fragment=/run/issue.d/60-loom-network.issue

if [[ ! -e "/sys/class/net/${APPLIANCE_INTERFACE}" ]]; then
    # With the fallback in place this no longer means "the match missed"
    # -- it means there was no wired port to claim either.
    lines=(
        --warn "${APPLIANCE_INTERFACE} does not exist -- no address, no DHCP, no *.loom."
        --warn "No wired interface was found to claim. Present instead:"
    )
    for candidate in /sys/class/net/*; do
        name="$(basename "${candidate}")"
        if [[ "${name}" == lo ]]; then
            continue
        fi
        lines+=(--warn "  ${name}")
    done
    lines+=(--warn "If one of those is in fact wired, rebuild with --interface <name>.")
    loom-issue-fragment 60-loom-network "${lines[@]}"
    exit 0
fi

if [[ -e "${FALLBACK_RECORD}" ]]; then
    # shellcheck source=/dev/null
    . "${FALLBACK_RECORD}"

    # Read through `:-` rather than bare. Identical under the `set -e` this
    # runs with, and honest about where the values come from: the record is
    # written by loom-interface-fallback, so a box installed from an older
    # image can be missing any of these fields.
    reason="${LOOM_FALLBACK_REASON:-}"
    interface="${LOOM_FALLBACK_INTERFACE:-}"
    alternatives="${LOOM_FALLBACK_ALTERNATIVES:-}"

    # An explicit --interface did what it was told; that is not news for
    # the login screen, and the journal already has it.
    if [[ "${reason}" == override ]]; then
        rm --force "${fragment}"
        exit 0
    fi

    # A notice rather than a problem: the box works, it simply claimed the
    # port itself. In red it would read as a fault that needs fixing.
    lines=(
        --note "${APPLIANCE_INTERFACE} is ${interface}, claimed automatically:"
        --note "this image has no platform match for the NIC in this box."
    )
    if [[ -n "${alternatives}" ]]; then
        lines+=(
            --note "Other wired ports: ${alternatives}"
            --note "If nothing reaches the box, move the cable to one of those."
        )
    fi
    lines+=(
        --note "To pin it, rebuild with --interface ${interface},"
        --note "or add a platform for this machine."
    )
    loom-issue-fragment 60-loom-network "${lines[@]}"
    exit 0
fi

# Matched properly. Clear anything an earlier boot left behind.
rm --force "${fragment}"
exit 0
