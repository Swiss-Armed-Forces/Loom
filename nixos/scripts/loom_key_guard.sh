# shellcheck shell=bash
#
# The body of `loom-key-guard`, the poller that powers the box off when the USB
# key stops being present. nixos/key-guard.nix reads this file into the
# writeShellApplication of the same name, behind a prologue of `LOOM_*`
# assignments carrying the values from the module.
#
# A file rather than a string in that module, because a string is linted by
# nothing: the repository runs `shellcheck -x -o all` over its .sh files and
# cannot see into a .nix one. Five hundred lines of control flow around a
# poweroff is the last place in this tree that should be taking that trade.
#
# No shebang and no executable bit, deliberately. This is not a program anybody
# runs from the checkout -- the prologue above it is what makes it one, and the
# `shell=bash` directive on the first line is what tells the hook so.
#
# `set -euo pipefail` restates what writeShellApplication already applies
# (bashOptions defaults to errexit, nounset and pipefail). Without it the
# linter would read a different program from the one that runs, and SC2310 --
# a function in an `if` condition silently disabling `set -e` -- would never
# fire. The same argument nixos/key-store.nix's own check has always made.
set -euo pipefail

#
# What the prologue hands over
#
# Read through `:?` rather than used bare: an unset or empty value stops the
# guard at its first use instead of acting on "", which here would mean
# fingerprinting nothing and powering the box off. It is also what makes the
# names visible to the linter -- read bare, every one of them is SC2154.
#
readonly STATE_DIR="${LOOM_STATE_DIR:?nixos/key-guard.nix must set this}"
readonly KEY_DEVICE="${LOOM_KEY_DEVICE:?nixos/key-guard.nix must set this}"
readonly ROOT_DEVICE="${LOOM_ROOT_DEVICE:?nixos/key-guard.nix must set this}"
readonly KEY_BYTES="${LOOM_KEY_BYTES:?nixos/key-guard.nix must set this}"
readonly INTERVAL="${LOOM_INTERVAL:?nixos/key-guard.nix must set this}"
readonly GRACE_TICKS="${LOOM_GRACE_TICKS:?nixos/key-guard.nix must set this}"
readonly GRACE_SECONDS="${LOOM_GRACE_SECONDS:?nixos/key-guard.nix must set this}"
readonly KEY_ORACLE="${LOOM_KEY_ORACLE:?nixos/key-guard.nix must set this}"
readonly ACTION="${LOOM_ACTION:?nixos/key-guard.nix must set this}"
readonly SOCKET="${LOOM_SOCKET:?nixos/key-guard.nix must set this}"
readonly WITNESS_FILE="${LOOM_WITNESS_FILE:?nixos/key-guard.nix must set this}"
readonly ARM_DEADLINE="${LOOM_ARM_DEADLINE:?nixos/key-guard.nix must set this}"
readonly SETTLE_TICKS="${LOOM_SETTLE_TICKS:?nixos/key-guard.nix must set this}"
readonly BANNER_REFRESH="${LOOM_BANNER_REFRESH:?nixos/key-guard.nix must set this}"

# Derived from the state directory, and shell's business rather than Nix's.
readonly STATE_FILE="${STATE_DIR}/state"
readonly DEVICE_FILE="${STATE_DIR}/device"
readonly FINGERPRINT_FILE="${STATE_DIR}/fingerprint"
readonly DISARM_FILE="${STATE_DIR}/disarmed"
readonly DEADLINE_FILE="${STATE_DIR}/deadline"

# Why the last arm attempt failed, and the last reason logged, so a box
# stuck on one cause says so once and a flapping one stays visible.
ARM_REASON=""
REPORTED_REASON=""
# The smallest countdown notice already given, 0 for none yet, and
# whether the deadline is settled for this boot.
NOTIFIED=0
DEADLINE_RETIRED=0

main() {
    local command="${1:-watch}"

    case "${command}" in
    watch)
        require_root
        ensure_state_dir
        watch
        ;;
    status)
        status
        ;;
    arm)
        require_root
        ensure_state_dir
        # Deliberately does not arm here: the watcher owns the state
        # files, and a second writer would race it. Clearing the flag is
        # enough -- the next tick picks the key up.
        rm --force "${DISARM_FILE}"
        printf 'Key guard re-enabled; it arms within %ss if the key is present.\n' \
            "${INTERVAL}"
        ;;
    disarm)
        require_root
        ensure_state_dir
        : >"${DISARM_FILE}"
        printf 'Key guard disarmed until the next boot. The USB key can be removed.\n'
        ;;
    *)
        printf >&2 'usage: loom-key-guard [watch|status|arm|disarm]\n'
        exit 1
        ;;
    esac
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        printf >&2 'loom-key-guard: must run as root.\n'
        exit 1
    fi
}

ensure_state_dir() {
    mkdir --parents "${STATE_DIR}"
    chmod 0755 "${STATE_DIR}"
}

# ---------------------------------------------------------------------
# State
#
# `state` is world-readable because box.nix's login banner reads it as the
# operator; `fingerprint` is not, and is the only file here worth hiding.
# Both are written through a temporary file, so a banner rendered while
# the guard is mid-write can never read half a word.
# ---------------------------------------------------------------------
put() {
    local path="${1}" mode="${2}" content="${3}"
    printf '%s\n' "${content}" >"${path}.tmp"
    chmod "${mode}" "${path}.tmp"
    mv "${path}.tmp" "${path}"
}

current_state() {
    cat "${STATE_FILE}" 2>/dev/null || printf 'idle'
}

set_state() {
    put "${STATE_FILE}" 0644 "${1}"
    # The banner is the only thing an operator who never logs in ever
    # sees, so it has to follow the guard. Rewriting the issue file is
    # half of that: agetty paints it once and then blocks on a keypress,
    # so tty1 has to be redrawn as well, which is what this command does
    # (box.nix). It exits 1 when it declined to redraw over a session.
    "${BANNER_REFRESH}" >/dev/null 2>&1 || true
}

# ---------------------------------------------------------------------
# Reading the key
# ---------------------------------------------------------------------
read_fingerprint() {
    local device="${1}" digest
    # iflag=direct is not a micro-optimisation. Without O_DIRECT the page
    # cache happily hands the same 4096 bytes back long after the stick
    # has physically left, and the guard never fires at all.
    # Errors are swallowed because the caller reports them: a read that
    # keeps failing is named once, by `ARM_REASON`, rather than every
    # two seconds for the life of the box.
    if ! digest="$(dd if="${device}" bs="${KEY_BYTES}" count=1 \
        iflag=direct status=none 2>/dev/null | sha256sum)"; then
        # Not every USB bridge accepts O_DIRECT, and a guard that quietly
        # never armed would be worse than the cache it is avoiding.
        # BLKFLSBUF invalidates this device's buffer cache, which buys the
        # same guarantee the long way round.
        blockdev --flushbufs "${device}" 2>/dev/null || return 1
        digest="$(dd if="${device}" bs="${KEY_BYTES}" count=1 \
            status=none 2>/dev/null | sha256sum)" || return 1
    fi
    printf '%s' "${digest%% *}"
}

zero_fingerprint() {
    local digest
    digest="$(head --bytes="${KEY_BYTES}" /dev/zero | sha256sum)"
    printf '%s' "${digest%% *}"
}

# True while the key recorded at arm time is still readable somewhere.
#
# The *bytes* are the identity, not the path. A stick that is pulled and
# put back inside the grace window can come back on a different /dev node,
# so the node seen at arm time is only a fast path -- what the label
# resolves to right now is tried as well, and either answer is accepted
# only if it hashes to what was recorded. That is also what makes
# /dev/disk/by-partlabel safe to consult here at all: it is not unique,
# and with a second Loom stick attached it resolves to whichever one udev
# linked last (installer/loom_installer/constants.py).
key_present() {
    local expected pinned resolved node fingerprint
    expected="$(cat "${FINGERPRINT_FILE}" 2>/dev/null)" || return 1
    pinned="$(cat "${DEVICE_FILE}" 2>/dev/null || true)"
    resolved="$(readlink --canonicalize "${KEY_DEVICE}" 2>/dev/null || true)"

    for node in "${pinned}" "${resolved}"; do
        [[ -b "${node}" ]] || continue
        fingerprint="$(read_fingerprint "${node}")" || continue
        [[ "${fingerprint}" == "${expected}" ]] || continue
        if [[ "${node}" != "${pinned}" ]]; then
            put "${DEVICE_FILE}" 0644 "${node}"
        fi
        return 0
    done
    return 1
}

# Every node that might be the key stick.
#
# `KEY_DEVICE` is a by-partlabel symlink and that path is not unique -- the
# same reasoning `key_present` above already applies: with a second stick
# carrying a GPT partition named loom-key (a backup key, another
# appliance's) udev points it at whichever it linked last, and udev gives
# the loser a suffixed name rather than nothing. Resolving the one symlink
# and giving up was how a healthy box powered itself off 180 seconds after
# boot: the guard could never arm, published `idle`, and `countdown` acted
# on a witness file stage 1 had legitimately written.
key_candidates() {
    local link node
    local -a seen=()
    for link in "${KEY_DEVICE}" "${KEY_DEVICE}"[0-9]* "${KEY_DEVICE}"-*; do
        [[ -e "${link}" ]] || continue
        node="$(readlink --canonicalize "${link}" 2>/dev/null || true)"
        [[ -b "${node}" ]] || continue
        if [[ " ${seen[*]-} " == *" ${node} "* ]]; then
            continue
        fi
        seen+=("${node}")
        printf '%s\n' "${node}"
    done
}

arm_once() {
    local node
    local tried=0

    while read -r node; do
        [[ -n "${node}" ]] || continue
        tried=1
        if arm_on_node "${node}"; then
            return 0
        fi
    done < <(key_candidates)

    if [[ "${tried}" -eq 0 ]]; then
        ARM_REASON="no block device at ${KEY_DEVICE}"
    fi
    return 1
}

# The oracle, for one candidate. ARM_REASON carries why it was not the one.
arm_on_node() {
    local node="${1}" fingerprint

    if ! fingerprint="$(read_fingerprint "${node}")"; then
        ARM_REASON="${node} could not be read"
        return 1
    fi

    # A wiped key partition is a missing key. Same rule the installer
    # applies before it will install at all (common.sh `key_state`).
    if [[ "${fingerprint}" == "$(zero_fingerprint)" ]]; then
        ARM_REASON="${node} is blank"
        return 1
    fi

    if [[ "${KEY_ORACLE}" = true ]]; then
        # The LUKS header is the oracle: this proves the stick still
        # unlocks *this* disk. It is why no copy of the key has to be kept
        # anywhere, and why a foreign stick carrying a partition named
        # loom-key cannot keep the box alive. Cheap -- the installer
        # formats with pbkdf2 at 1000 iterations.
        if ! cryptsetup luksOpen --test-passphrase \
            --key-file "${node}" \
            --keyfile-size "${KEY_BYTES}" \
            "${ROOT_DEVICE}" >/dev/null 2>&1; then
            ARM_REASON="the key on ${node} does not open ${ROOT_DEVICE}"
            return 1
        fi
    else
        # --lock-key: the bytes on the stick are a LUKS2 container, not the
        # key, so the oracle above has nothing to authenticate with and the
        # guard has no plaintext copy to authenticate with either -- by
        # design, since holding one for the life of the box is the thing
        # the flag exists to avoid.
        #
        # Losing it costs less than it looks. The oracle proves "this stick
        # unlocks this disk", and under --lock-key stage 1 proved exactly
        # that a few seconds ago: the box is running, so the container on
        # this stick yielded the key this root was formatted with. What is
        # left to establish here is that the thing plugged in is a key
        # stick at all, and the fingerprint below carries the rest -- a
        # different container has a different header, so a foreign stick
        # still cannot keep the box alive.
        #
        # `--type luks2` rather than a bare isLuks, matching
        # installer/loom_installer/devices.py `is_key_container`: LUKS1
        # would answer yes, and nothing in Loom writes a LUKS1 container,
        # so one here is a stick from somewhere else.
        if ! cryptsetup isLuks --type luks2 "${node}" >/dev/null 2>&1; then
            ARM_REASON="${node} carries no LUKS2 key store"
            return 1
        fi
    fi

    put "${DEVICE_FILE}" 0644 "${node}"
    put "${FINGERPRINT_FILE}" 0600 "${fingerprint}"
    set_state armed
    printf '[loom] Key guard armed on %s; removing the key %s.\n' \
        "${node}" "$(action_phrase)"
}

# ---------------------------------------------------------------------
# Telling whoever is standing at the box
#
# The unit logs to the journal only, like every other Loom unit, so that
# nothing paints over the operator's screen. `wall` and tmux are what
# actually reach a human, and both are best-effort: there may be no
# session and no terminal at all.
# ---------------------------------------------------------------------
announce() {
    printf '%s\n' "${1}"
    wall --nobanner "${1}" 2>/dev/null || true
    # `-l`: display-message expands its argument as a tmux *format*. Every
    # message this unit sends is a literal of its own, so nothing here is
    # exploitable -- but loom-usb-ingest reaches the same call with text that
    # came off a stranger's stick, and the two should not differ about it.
    tmux -S "${SOCKET}" display-message -l "${1}" 2>/dev/null || true
}

alarm() {
    tmux -S "${SOCKET}" set-option -g status-style "bg=colour124,fg=white" \
        2>/dev/null || true
}

clear_alarm() {
    # The value console.nix's tmux.conf sets. Restated rather than shared
    # because a tmux option can only be restored by naming it again.
    tmux -S "${SOCKET}" set-option -g status-style "bg=colour24,fg=white" \
        2>/dev/null || true
}

action_phrase() {
    case "${ACTION}" in
    poweroff) printf 'powers this box off after %ss' "${GRACE_SECONDS}" ;;
    *) printf 'only warns (this --debug image does not power off)' ;;
    esac
}

# ---------------------------------------------------------------------
# The arm deadline
#
# A box that cannot arm is a box running an unlocked dm-crypt mapping
# with nothing watching the key, so it does not get to run indefinitely.
#
# It applies only where stage 1 left `WITNESS_FILE` behind, which says
# the key partition was present when the root was unlocked
# (box-hardware.nix). A box booted on the recovery passphrase has no
# stick, never arms by design, and is left up for repairs -- the console
# is the only way into it.
# ---------------------------------------------------------------------
deadline_applies() {
    [[ "${DEADLINE_RETIRED}" -eq 0 ]] || return 1
    [[ "${ARM_DEADLINE}" -gt 0 ]] || return 1
    # Same exception as `trip`: a --debug image warns rather than acts.
    [[ "${ACTION}" == "poweroff" ]] || return 1
    [[ -e "${WITNESS_FILE}" ]] || return 1
}

# Settled for this boot, by arming or by an operator saying the key may
# be absent. Neither is reopened by anything short of a reboot.
retire_deadline() {
    DEADLINE_RETIRED=1
    rm --force "${DEADLINE_FILE}"
}

countdown() {
    local now expires left boundary
    deadline_applies || return 0

    now="$(date +%s)"
    # Absolute, and written once: a guard that systemd restarted must not
    # hand the box a fresh window. It is also what `status` reads.
    if [[ ! -e "${DEADLINE_FILE}" ]]; then
        put "${DEADLINE_FILE}" 0644 "$((now + ARM_DEADLINE))"
        # The login screen carries "powers off ...s after boot" for
        # exactly as long as this file exists, and its appearance is not
        # a state change -- the guard goes on reporting `idle` either
        # side of it -- so `set_state`'s refresh never covers this. The
        # file is created once per boot, so is this.
        #
        # Retiring it needs no counterpart: both callers of
        # `retire_deadline` change the state in the same breath, and that
        # redraw takes the line back off the screen.
        "${BANNER_REFRESH}" >/dev/null 2>&1 || true
    fi
    expires="$(cat "${DEADLINE_FILE}")"
    left=$((expires - now))

    if [[ "${left}" -le 0 ]]; then
        power_off_now \
            "[loom] No usable USB key ${ARM_DEADLINE}s after boot. Powering off now."
    fi

    # Loud, and rarely: nobody is watching the screen for the first
    # minute of a boot, and the notice has to arrive while there is
    # still time to act on it.
    for boundary in 120 60 30 10; do
        if [[ "${left}" -le "${boundary}" ]] &&
            [[ "${NOTIFIED}" -eq 0 || "${boundary}" -lt "${NOTIFIED}" ]]; then
            NOTIFIED="${boundary}"
            alarm
            announce "[loom] No usable USB key -- this box powers off in ${left}s. Plug the key in, or run 'loom-key-guard disarm'."
            break
        fi
    done
}

# ---------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------
watch() {
    local misses=0 failures=0

    trap 'exit 0' TERM INT

    while :; do
        # A reboot or poweroff the operator asked for stops this unit as
        # part of the same transaction that tears the rest of the box
        # down. Without this the guard would race it and act on a box
        # that was already on its way down.
        if [[ "$(systemctl is-system-running 2>/dev/null || true)" == "stopping" ]]; then
            exit 0
        fi

        if [[ -e "${DISARM_FILE}" ]]; then
            if [[ "$(current_state)" != "disarmed" ]]; then
                misses=0
                clear_alarm
                retire_deadline
                set_state disarmed
                announce "[loom] Key guard disarmed. Removing the USB key will not power this box off."
            fi
        elif [[ "$(current_state)" != "armed" ]]; then
            if arm_once; then
                misses=0
                failures=0
                REPORTED_REASON=""
                retire_deadline
            else
                failures=$((failures + 1))
                # Not on the first failure: the key device is still
                # enumerating for the first seconds after a switch-root,
                # and publishing `idle` redraws the login screen with it.
                if [[ "${failures}" -eq "${SETTLE_TICKS}" ]]; then
                    REPORTED_REASON="${ARM_REASON}"
                    set_state idle
                    # Once, not every two seconds for the life of the
                    # box. This is the ordinary state of a box booted
                    # with the recovery passphrase, and it is not an
                    # error.
                    printf '[loom] No usable key at %s; the guard stays idle (%s).\n' \
                        "${KEY_DEVICE}" "${ARM_REASON}"
                elif [[ "${failures}" -gt "${SETTLE_TICKS}" && "${ARM_REASON}" != "${REPORTED_REASON}" ]]; then
                    REPORTED_REASON="${ARM_REASON}"
                    printf '[loom] Key guard still cannot arm: %s.\n' "${ARM_REASON}"
                fi
                countdown
            fi
        elif key_present; then
            if [[ "${misses}" -gt 0 ]]; then
                misses=0
                clear_alarm
                announce "[loom] USB key is back. Shutdown cancelled."
            fi
        else
            misses=$((misses + 1))
            if [[ "${misses}" -ge "${GRACE_TICKS}" ]]; then
                trip
                misses=0
                failures=0
            else
                alarm
                announce "[loom] USB KEY REMOVED -- $(((GRACE_TICKS - misses) * INTERVAL))s left. Plug it back in to cancel."
            fi
        fi

        sleep "${INTERVAL}"
    done
}

trip() {
    clear_alarm

    if [[ "${ACTION}" != "poweroff" ]]; then
        # Warn-only, which only a `--debug` image gets: that image has
        # already traded the appliance's guarantees for hands-on access,
        # and a box being driven by hand is one where a pulled stick is
        # usually the operator's own doing.
        set_state idle
        announce "[loom] USB key gone for ${GRACE_SECONDS}s. This --debug image only warns; the box stays up."
        return 0
    fi

    power_off_now "[loom] USB key gone for ${GRACE_SECONDS}s. Powering off now."
}

power_off_now() {
    announce "${1}"
    # A clean poweroff, not a forced one: unit teardown is bounded by
    # DefaultTimeoutStopSec, and the indexed data is worth more than the
    # seconds a sysrq would save.
    #
    # Checked, and the state is only set once it was accepted. A refused or
    # lost transaction -- a conflicting job already queued, logind not
    # answering -- used to be ignored: the guard set `tripped`, exited 0,
    # and `Restart = "on-failure"` did not bring it back. The box then went
    # on running with an unlocked dm-crypt mapping, no key present and
    # nothing watching, while the banner and `loom-key-guard status` both
    # said `tripped`, which reads as "it worked". Exiting non-zero instead
    # restarts the watcher, which tries again.
    if ! systemctl poweroff; then
        announce "[loom] Poweroff was refused. The key is still gone -- retrying."
        set_state armed
        exit 1
    fi
    set_state tripped
    exit 0
}

status() {
    local state device expires left
    state="$(current_state)"
    device="$(cat "${DEVICE_FILE}" 2>/dev/null || true)"

    printf 'loom-key-guard: %s\n' "${state}"
    printf '  key device:  %s\n' "${KEY_DEVICE}"
    if [[ -n "${device}" ]]; then
        printf '  resolved to: %s\n' "${device}"
    fi
    printf '  on removal:  %s after %ss\n' "${ACTION}" "${GRACE_SECONDS}"
    if [[ -e "${DEADLINE_FILE}" ]]; then
        expires="$(cat "${DEADLINE_FILE}")"
        left=$((expires - $(date +%s)))
        [[ "${left}" -ge 0 ]] || left=0
        printf '  arm deadline: powers off in %ss unless the key arms\n' "${left}"
    fi
}

main "${@}"
