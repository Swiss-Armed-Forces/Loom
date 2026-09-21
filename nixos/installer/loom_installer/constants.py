"""Names and numbers the stick and the box it installs must agree on.

The three storage names are deliberately NOT here: they come from nixos/storage.nix by
way of installer.nix's wrapper, so the names the installer creates and the names the
box's stage 1 waits for cannot drift apart. See settings.py.
"""

from typing import Final

# Partition labels. The stick uses `loom-live-*` and `loom-key`; the internal disks
# use `loom-esp` and `loom-pv<N>`. The prefixes must stay disjoint --
# /dev/disk/by-partlabel is not unique, and with both media attached a shared name
# would resolve to whichever udev linked last.
#
# The PV label carries an index for the same reason: every internal disk gets one,
# and two partitions sharing a name would make `by-partlabel` a coin toss between
# the members of the very pool being built.
LIVE_ESP_LABEL: Final = "loom-live-esp"
LIVE_STORE_LABEL: Final = "loom-live-store"
KEY_LABEL: Final = "loom-key"
ESP_LABEL: Final = "loom-esp"
PV_LABEL_PREFIX: Final = "loom-pv"

# Kept identical to `fileSystems."/boot".options` in box-hardware.nix. vfat carries no
# permissions on disk, so the ESP is only as private as whatever mounted it -- and the
# installer mounts the target ESP itself, long before the installed configuration has
# any say. See mount_target().
ESP_MOUNT_OPTIONS: Final = "umask=0077"

BY_PARTLABEL: Final = "/dev/disk/by-partlabel"
KEY_DEVICE: Final = f"{BY_PARTLABEL}/{KEY_LABEL}"

KEY_BYTES: Final = 4096

# The whole pool, not each disk: a box with two small NVMes has as much room as one
# with a single large one, and refusing it would be arithmetic nobody can argue with
# from the console.
MIN_POOL_BYTES: Final = 250 * 1000 * 1000 * 1000

# Set by the menu before it hands over to an unattended install, so that a menu
# restarted by systemd cannot count down a second time onto a disk the first attempt
# already began partitioning. In tmpfs: it must not survive a reboot, because a
# reboot is how an operator retries.
AUTO_MARKER: Final = "/run/loom-auto-install-attempted"

# `loom-install` exits with this when the install itself succeeded but the box may
# not boot into it unattended -- see `fix_boot_order`. The menu holds the console
# open on it rather than counting down, because the firmware fix it asks for is
# printed nowhere else: the installed box's login banner repeats the recovery
# passphrase, but not this.
EXIT_BOOT_ORDER_DEGRADED: Final = 2

# Where the target filesystem is assembled.
MOUNT: Final = "/mnt"
CRYPT_MAPPING: Final = "cryptroot"

# Written by installer.nix from the evaluated configuration, so this never has to
# spell `first-time-setup` and a rename in modes.nix cannot drift away from it.
TARGET_SYSTEM_FILE: Final = "/etc/loom/target-system"
SETUP_SPECIALISATION_FILE: Final = "/etc/loom/setup-specialisation"

# Relative to the freshly installed root.
RECOVERY_FILE_REL: Final = "var/lib/loom/recovery-passphrase"

GIGABYTE: Final = 1000 * 1000 * 1000
