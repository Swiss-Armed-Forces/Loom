# shellcheck shell=bash
#
# The body of `loom-promote-boot-entry`, which takes a box off the first-time
# setup entry and makes run mode the default once the fetch has finished.
# nixos/modes.nix reads this file into the writeShellApplication of the same
# name. It needs no values from the module: every path it touches is fixed.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

entries=/boot/loader/entries
conf=/boot/loader/loader.conf

# -----------------------------------------------------------------------
# 1. Point `default` back at run mode.
#
# This half can go through the bootloader builder, unlike the installer's
# own selection (install.sh `select_setup_entry`), and the asymmetry is
# worth knowing: the builder decides which entry is default by comparing
# DEFAULT-CONFIG against the *main* toplevel only, and calls
# write_loader_conf() with no specialisation. The run closure is that main
# toplevel, so handing it over works and writes
# `default nixos-generation-<N>.conf` itself. Handing it a specialisation
# would match nothing and leave loader.conf untouched, which is exactly why
# the installer has to write that line by hand.
#
# It also rewrites every entry, including the specialisation one that step
# 2 removes -- hence this order. Reversed, a power cut between the two
# would leave `default` naming a file that no longer exists.
#
# NIXOS_INSTALL_BOOTLOADER=1 keeps it on the `bootctl install` path rather
# than the version-comparing `update` path, matching what the installer
# already did to this ESP. It cannot disturb the NVRAM order fix_boot_order
# set: box-hardware.nix sets canTouchEfiVariables = false, and that is what
# puts --no-variables on every bootctl call the builder makes.
# -----------------------------------------------------------------------
NIXOS_INSTALL_BOOTLOADER=1 \
  /nix/var/nix/profiles/system/bin/switch-to-configuration boot

# -----------------------------------------------------------------------
# 2. Remove the first-time-setup entry.
#
# The glob is deliberately narrow -- it carries both `nixos-generation-`
# and `-specialisation-`, so nothing else living in this directory can be
# caught by it. systemd-boot's own `Reboot Into Firmware Interface` is
# synthesised by the loader rather than stored here, so it survives
# regardless; the scoping is what makes that true by construction.
#
# None is not an error: this runs by hand as well as from loom-fetch (see
# systemPackages below), and a re-run after a successful promotion should
# report that rather than fail. The state check in step 3 is what decides
# whether "nothing to remove" means "already done" or "something is wrong",
# so it runs either way.
#
# Several *is* an error -- it means the entry layout changed under us, and
# guessing which to delete is not a decision to make on an appliance.
# -----------------------------------------------------------------------
mapfile -t setup_entries < <(
  find "${entries}" -maxdepth 1 -type f \
    -name 'nixos-generation-*-specialisation-*.conf' | sort
)
case "${#setup_entries[@]}" in
  0) echo "[-] No first-time-setup entry to remove; checking the menu anyway." ;;
  1) rm -- "${setup_entries[0]}" ;;
  *)
    echo >&2 "[!] Found ${#setup_entries[@]} specialisation entries in ${entries}, expected one."
    echo >&2 "[!] Leaving the boot menu alone rather than guessing which to remove."
    exit 1
    ;;
esac

# -----------------------------------------------------------------------
# 3. Check the menu is what it now claims to be: one entry, and `default`
#    names it. Nothing else verifies this, and the failure it guards
#    against -- a box that boots to a menu with no valid default -- is one
#    nobody would enjoy meeting in the field.
# -----------------------------------------------------------------------
remaining="$(find "${entries}" -maxdepth 1 -type f -name 'nixos-*.conf' | wc -l)"
default="$(awk '$1 == "default" { print $2 }' "${conf}")"
if [[ "${remaining}" -ne 1 ]] || [[ ! -f "${entries}/${default}" ]]; then
  echo >&2 "[!] Boot menu is not in the expected state: ${remaining} entries, default '${default}'."
  exit 1
fi

echo "[*] Boot menu promoted: one entry, ${default}."
