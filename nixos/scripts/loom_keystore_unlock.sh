# shellcheck shell=bash
#
# The body of the stage-1 unit that unlocks the key store on a `--lock-key`
# stick: ask for the word passphrase, open the LUKS2 container on the key
# partition, copy the plaintext key bytes onto a ramfs for
# systemd-cryptsetup, and close the mapping again. nixos/key-store.nix reads
# this file into `boot.initrd.systemd.services.loom-keystore.script`, behind
# a prologue of `LOOM_*` assignments.
#
# This is the one part of the appliance no test can reach -- nixpkgs' qemu-vm
# module replaces the bootloader and the root device, so nothing under
# nixos/tests/ ever runs an initrd of ours. Shellcheck is the whole of the
# checking it gets, and the repository's own hook is what runs it, at commit
# time rather than at image-build time.
#
# `set -e` and nothing more, which is what nixpkgs' makeJobScript wraps a
# unit `script` in (nixos/lib/systemd-lib.nix) -- and `set -e` is what most
# of the control flow below is written around. Adding `nounset` or
# `pipefail` here would be a behaviour change in the one place on this box
# where a mistake means an appliance that does not boot and cannot be
# reached.
set -e

readonly KEY_DIRECTORY="${LOOM_KEY_DIRECTORY:?nixos/key-store.nix must set this}"
readonly KEY_DEVICE="${LOOM_KEY_DEVICE:?nixos/key-store.nix must set this}"
readonly MAPPING="${LOOM_MAPPING:?nixos/key-store.nix must set this}"
readonly PLAIN_KEY_FILE="${LOOM_PLAIN_KEY_FILE:?nixos/key-store.nix must set this}"
readonly KEY_BYTES="${LOOM_KEY_BYTES:?nixos/key-store.nix must set this}"
readonly ATTEMPTS="${LOOM_ATTEMPTS:?nixos/key-store.nix must set this}"
readonly KEYBOARD="${LOOM_KEYBOARD:?nixos/key-store.nix must set this}"

mkdir --parents "${KEY_DIRECTORY}"
# ramfs, not tmpfs: tmpfs pages can be swapped, and while the installed
# box has no swap (box-hardware.nix) that is a property of the system
# this is about to boot, not of the initrd doing the booting.
mount -t ramfs none "${KEY_DIRECTORY}"
umask 277

# The same password-agent protocol systemd-cryptsetup itself speaks, so
# the box asks for this exactly the way it asks for the recovery
# passphrase -- through plymouth when run mode's splash is up, and on
# the console when it is not (setup mode, --debug).
#
# --echo, which is not the obvious choice for a passphrase prompt. Three
# reasons it is the right one here:
#
#   * The threat it gives up is an observer at the monitor, and this box
#     concedes that one already: it prints the LUKS recovery passphrase
#     on its login screen at every boot (box.nix), and the console is a
#     root shell after one keypress.
#   * What it buys is the only feedback there is about the keyboard map.
#     Under a wrong map `-` arrives as `/` and `y` as `z`, and a masked
#     prompt makes that indistinguishable from a wrong passphrase -- on
#     a box that will not boot, with nothing else on screen to go on.
#   * --echo=masked would show asterisks, which confirms keystrokes
#     register and says nothing about *which*. That is the one thing
#     worth knowing here, so masked is the worst of the three.
#
# The keyboard is named in the prompt, and that is the other half of the
# echo. Echo shows an operator that `-` came out as `/`; this tells them
# why, and what to pass to `--keymap` to fix it. It is named even when it
# is the default `us`, because that is the case most likely to be wrong
# and the one nothing else on the screen would mention.
# Escaped, like every other use of this value -- `keymap.nix` passes the raw
# `--keymap` argument through, and this lands in a double-quoted bash string
# in a stage-1 script running as root before the root filesystem is unlocked.
# Unreachable today behind two build-time guards (`keymapCheck` runs
# `loadkeys` on it, and `pkgs.runCommand "loom-keymap-check-${cfg}"` makes a
# value containing `$`, a backtick, `;` or a space an invalid derivation name)
# -- which is exactly why it should not be load-bearing for something it was
# not written for.

# Stop trying, say why where it can actually be read, and let the boot
# fall through to the recovery prompt.
#
# Falling through is deliberate: a box whose stick is dead has no other
# way in, so making this unit a hard dependency of the root would trade a
# real escape hatch for a tidier failure. The message below is there
# because the next prompt wants a *different secret* and has nothing to
# say so with.
#
# plymouth first, because with the splash up it is the only thing on the
# screen -- then out of the way, because a still logo over a boot that has
# gone wrong is actively misleading (the same argument modes.nix makes for
# --debug builds), and because the console behind it is where the message
# below and the recovery prompt both land.
give_up() {
    local reason="${1}"

    if plymouth --ping 2>/dev/null; then
        plymouth display-message --text="${reason}" || true
        plymouth quit || true
    fi

    {
        echo
        echo "[loom] ${reason}"
        echo "[loom] The next prompt is the LUKS RECOVERY passphrase: the long"
        echo "[loom] dash-separated one the installer printed and the login"
        echo "[loom] screen shows -- NOT the words that came with this stick."
        echo
    } > /dev/console 2>/dev/null || true

    exit 1
}

prompt="Loom key stick passphrase ${KEYBOARD}:"
attempt=1
while true; do
    # `|| give_up` rather than letting `set -e` take it: a prompt that
    # timed out or found no agent is not a wrong passphrase, and dying
    # here silently would read as "it just asks again".
    passphrase="$(systemd-ask-password --echo=yes --id=loom-keystore \
      "${prompt}")" \
      || give_up 'The key stick passphrase prompt was cancelled.'

    # Blank on the last try is the documented way out, offered by the
    # prompt itself. It exists so that moving to the recovery passphrase
    # is something the operator *chose*, rather than something that
    # happened to them between two prompts that look alike.
    if [[ -z "${passphrase}" ]] && (( attempt >= ATTEMPTS )); then
        give_up 'No key stick passphrase given.'
    fi

    # Through a pipe, so the passphrase is never a path in /proc and
    # never an argument any other process can read.
    #
    # The status comes off PIPESTATUS rather than `$?`, which would be
    # `printf`'s: on the statuses where cryptsetup exits before reading
    # its key file, printf dies of SIGPIPE and `$?` reports 141 instead
    # of the reason. That would turn a precise message into a number.
    status=0
    if ! printf '%s' "${passphrase}" | cryptsetup open \
      --type luks2 \
      --key-file - \
      "${KEY_DEVICE}" "${MAPPING}"
    then
        status="${PIPESTATUS[1]}"
    fi

    if (( status == 0 )); then
        break
    fi

    # Only `2` -- the passphrase was wrong -- is worth asking again for.
    # The rest describe a box rather than a typo, and retrying would burn
    # the operator's remaining tries while telling them something untrue.
    #
    # `3` matters more than its rarity suggests: the container is argon2id
    # pinned at 1 GiB (cicd/build_appliance_image.sh) and this runs in an
    # initrd, so "wrong passphrase" would be an outright lie about a box
    # that is simply short of memory.
    case "${status}" in
    2) ;;
    1 | 4) give_up 'The key partition is not a LUKS2 container.' ;;
    3)     give_up 'Not enough memory to unlock the key store.' ;;
    5)     give_up 'The key store is busy, or already open.' ;;
    *)     give_up "cryptsetup failed (status ${status})." ;;
    esac

    if (( attempt >= ATTEMPTS )); then
        give_up "The key stick passphrase was wrong ${ATTEMPTS} times."
    fi

    # The count goes in the *next* prompt rather than onto the console,
    # and that is not a style choice: in run mode the splash is up, and
    # the ask-password message is the only text that reaches the screen.
    if (( attempt + 1 >= ATTEMPTS )); then
        prompt="Wrong passphrase, last try -- blank for recovery ${KEYBOARD}:"
    else
        prompt="Wrong passphrase, $(( ATTEMPTS - attempt )) left ${KEYBOARD}:"
    fi
    attempt=$(( attempt + 1 ))
done

dd if=/dev/mapper/"${MAPPING}" \
  of="${PLAIN_KEY_FILE}" \
  bs="${KEY_BYTES}" count=1 status=none

# Closed immediately. Stage 1 has what it needs, and leaving the mapping
# open would carry a second route to the key bytes across the switch-root
# and keep it there for the life of the box.
cryptsetup close "${MAPPING}"
