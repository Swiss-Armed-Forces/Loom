#!/usr/bin/env bats
#
# The rule that decides whether a disk is destroyed with nobody watching.
#
# Run in the installer scripts' own derivation (nixos/installer.nix), so a
# mistake here fails the image build in seconds rather than at a box -- the same
# argument the pytest suite under nixos/usb-ingest/ is run for.
#
# Only `auto_install_decision` is covered, and deliberately so: it is pure by
# construction, every input handed to it as an argument, precisely so that the
# rule can be exercised exhaustively without a disk anywhere near it. What
# gathers those inputs is covered by nixos/tests/appliance-install.nix.

setup() {
    # common.sh takes these from installer.nix's wrapProgram, which no test has.
    # The values are irrelevant to the decision; only their presence is.
    export LOOM_VG_NAME="loom"
    export LOOM_LV_NAME="root"
    export LOOM_ROOT_DEVICE="/dev/mapper/loom-root"

    # Defaulted rather than assumed: bats sets BATS_TEST_DIRNAME itself, and the
    # fallback is what lets this file also be sourced by a plain shell -- which
    # is the only reason anyone would reach for it while debugging.
    : "${BATS_TEST_DIRNAME:=$(dirname "${BASH_SOURCE[0]}")}"

    # shellcheck source-path=SCRIPTDIR/..
    # shellcheck source=../common.sh
    # shellcheck disable=SC1091
    source "${BATS_TEST_DIRNAME}/../common.sh"

    # Either side of LOOM_MIN_POOL_BYTES (250 GB). NOT_ENOUGH is picked so that
    # two of it clear the minimum and one of it does not, which is what the
    # pooled case below turns on.
    ENOUGH=$((300 * 1000 * 1000 * 1000))
    NOT_ENOUGH=$((140 * 1000 * 1000 * 1000))
}

# Argument order: attempted boot key_status target_count bytes claimed
@test "a fresh box with one big enough disk installs by itself" {
    run auto_install_decision 0 /dev/sda present 1 "${ENOUGH}" no
    [[ "${output}" = "armed" ]]
}

@test "two disks too small alone are armed once pooled" {
    # The whole point of measuring the pool rather than each member: this box
    # has no disk that would pass on its own.
    run auto_install_decision 0 /dev/sda present 2 $((NOT_ENOUGH * 2)) no
    [[ "${output}" = "armed" ]]
}

@test "a second attempt in the same boot never starts" {
    # Set by the menu before it hands over, so a service restart cannot count
    # down again onto a disk the first attempt already began partitioning.
    run auto_install_decision 1 /dev/sda present 1 "${ENOUGH}" no
    [[ "${output}" = "attempted" ]]
}

@test "the marker outranks every other verdict" {
    # Including one that would itself have refused: after an attempt the disks
    # may be half written, and nothing read off them means anything.
    run auto_install_decision 1 "" missing 0 0 yes
    [[ "${output}" = "attempted" ]]
}

@test "an ambiguous boot medium refuses" {
    # Two Loom sticks attached: boot_disk declines to guess, and guessing here
    # is how the wrong device gets erased.
    run auto_install_decision 0 "" present 1 "${ENOUGH}" no
    [[ "${output}" = "no-boot-medium" ]]
}

@test "a stick with no key refuses" {
    # Installing from one produces a box that encrypts itself and then never
    # boots again.
    run auto_install_decision 0 /dev/sda empty 1 "${ENOUGH}" no
    [[ "${output}" = "no-key" ]]

    run auto_install_decision 0 /dev/sda missing 1 "${ENOUGH}" no
    [[ "${output}" = "no-key" ]]
}

@test "no eligible disk refuses" {
    run auto_install_decision 0 /dev/sda present 0 0 no
    [[ "${output}" = "no-target" ]]
}

@test "a pool under the minimum refuses" {
    run auto_install_decision 0 /dev/sda present 1 "${NOT_ENOUGH}" no
    [[ "${output}" = "too-small" ]]
}

@test "a box this stick already installed is left alone" {
    # The accident this guard exists for: cleared NVRAM or a firmware that
    # re-scans removable media boots the stick again, and the box reinstalls
    # over its own indexed data with nobody at the keyboard.
    run auto_install_decision 0 /dev/sda present 1 "${ENOUGH}" yes
    [[ "${output}" = "already-installed" ]]
}

@test "a box installed from a different stick is still armed" {
    # A re-flashed stick carries a fresh key, so it cannot open that container
    # and re-provisioning stays unattended. This is the half of the guard that
    # would be easy to lose by making it test for a Loom layout instead.
    run auto_install_decision 0 /dev/sda present 1 "${ENOUGH}" no
    [[ "${output}" = "armed" ]]
}

@test "every verdict has something to say for itself" {
    # The reason line is the only explanation an operator gets for a box that
    # is sitting at a menu instead of installing, so none of them may come out
    # blank -- and a new verdict added without a reason must fail here.
    local verdict
    for verdict in attempted no-boot-medium no-key no-target too-small already-installed; do
        run auto_install_reason "${verdict}"
        [[ -n "${output}" ]]
        [[ "${output}" != "${verdict}" ]]
    done
}
