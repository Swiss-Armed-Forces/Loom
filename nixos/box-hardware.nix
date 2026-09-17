# Disks, boot and initrd for the appliance.
#
# Every device is addressed by GPT partition label, which is what lets a single
# system closure serve every box: only the LUKS key bytes differ between sticks,
# and those live on the stick rather than in the closure.
#
# Label prefixes are deliberately disjoint from the installer stick's
# (`loom-live-*`), because /dev/disk/by-partlabel is not unique -- with both
# media attached, a shared name would resolve nondeterministically.
#
# The root is LUKS2, unlocked from 4096 raw bytes on the USB stick's `loom-key`
# partition. The stick therefore has to stay plugged in. If it is missing,
# systemd stage 1 falls back to prompting for the recovery passphrase that the
# installer enrolled in keyslot 1.
{ config, ... }:
{
  # ---------------------------------------------------------------------------
  # Root encryption
  #
  # systemd initrd rather than the scripted one, deliberately: it makes
  # systemd-cryptsetup-generator emit `Requires=` + `After=` on the key device's
  # .device unit, so boot blocks until slow USB enumeration finishes and fails
  # closed if the stick is absent. The scripted initrd instead polls for a
  # hard-coded 10 seconds, which is a coin flip on USB.
  # ---------------------------------------------------------------------------
  boot.initrd.luks.devices."cryptroot" = {
    device = "/dev/disk/by-partlabel/loom-root-luks";
    keyFile = "/dev/disk/by-partlabel/loom-key";
    keyFileSize = 4096;
    keyFileOffset = 0;
    allowDiscards = true;

    # Two options are deliberately NOT set here:
    #   keyFileTimeout     - would downgrade the above Requires= to Wants=,
    #                        turning a missing stick into a silent boot.
    #   fallbackToPassword - implied by systemd stage 1, and asserted to be
    #                        false there. The recovery prompt happens anyway.
  };

  # USB enumeration is slow; this is the budget before boot gives up and asks
  # for the recovery passphrase instead.
  boot.initrd.systemd.settings.Manager.DefaultDeviceTimeoutSec = "60s";

  fileSystems."/" = {
    device = "/dev/mapper/cryptroot";
    fsType = "ext4";
    options = [ "noatime" ];
  };

  fileSystems."/boot" = {
    device = "/dev/disk/by-partlabel/loom-esp";
    fsType = "vfat";
    options = [ "umask=0077" ];
  };

  # vm.swappiness is pinned to 1 for Elasticsearch's benefit anyway.
  swapDevices = [ ];

  boot.initrd.systemd.enable = true;

  # `usb_storage` and `uas` are NOT part of boot.initrd.includeDefaultModules.
  # They are already needed here so that the later LUKS-key-on-USB milestone
  # does not fail in a way that looks identical to a missing key.
  boot.initrd.availableKernelModules = [
    "usb_storage"
    "uas"
    "xhci_pci"
    "nvme"
  ]
  ++ config.loom.platform.extraInitrdModules;

  boot.loader.systemd-boot = {
    enable = true;
    # The ESP is modest and the initrds are not.
    configurationLimit = 3;
  };
  # Appliance firmware: the loader is placed on the ESP directly and the boot
  # entry is managed by the installer, so there is no need to write EFI vars on
  # every rebuild.
  boot.loader.efi.canTouchEfiVariables = false;
  # Generous on purpose: the first boot after installation has to be interrupted
  # to pick the `Loom (first-time-setup)` entry, and on a box whose display only
  # wakes up part way through firmware init, five seconds can elapse before the
  # menu is visible. The appliance reboots rarely and an operator is normally
  # standing there.
  boot.loader.timeout = 30;
}
