# shellcheck shell=bash
#
# The body of `loom-pane`, the supervisor each console pane's TUI runs under:
# restart it when it exits, at once if it had actually been running and on a
# doubling backoff if it died on startup. nixos/console.nix reads this file
# into the writeShellApplication of the same name. It needs no values from
# the module -- the command to supervise arrives as "$@".
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs -- which matters here more
# than most, because two of the comments below are about `set -e`.
set -euo pipefail

# How long a run has to last before it is treated as "it worked, the
# operator just quit". Both TUIs here take well under a second to draw,
# so anything above a few seconds means it really did run.
settled=5
# First wait, and the ceiling it doubles up to. 30s is short enough that
# a box recovering from a transient failure comes back on its own, and
# long enough that a permanently broken command is not a busy loop.
delay=1
max_delay=30

# The program's own name, for the notice below: the full argument is a
# store path and would wrap the pane on its own.
name=$(basename "${1}")

while true; do
    started=${SECONDS}
    # Deliberately not `exec`: this loop has to outlive the program. And
    # `|| true` because writeShellApplication sets `set -e`, under which a
    # TUI exiting non-zero would take the supervisor with it.
    "$@" || true
    ran=$((SECONDS - started))

    if [[ "${ran}" -ge "${settled}" ]]; then
        # It ran, so whatever ended it was a decision rather than a fault.
        # Start again at once, and from a clean backoff.
        delay=1
        printf '\n  [%s exited after %ss -- restarting]\n' "${name}" "${ran}"
    else
        printf '\n  [%s exited after %ss -- restarting in %ss]\n' \
            "${name}" "${ran}" "${delay}"
    fi

    sleep "${delay}"

    # Grow the wait only for runs that did not settle. Written as an `if`
    # rather than `[ ... ] && delay=...`, because a false test there is a
    # non-zero exit status, and under `set -e` that would end the loop at
    # the ceiling instead of staying on it.
    if [[ "${ran}" -lt "${settled}" ]]; then
        delay=$((delay * 2))
        if [[ "${delay}" -gt "${max_delay}" ]]; then
            delay=${max_delay}
        fi
    fi
done
