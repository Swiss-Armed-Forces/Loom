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
#
# Stage 1 is the only place that *needs* the key, but it is no longer the only
# place that looks at it: key-guard.nix keeps watching the same device for as
# long as the box runs, and powers it off when the key goes away. The three
# values below come from there so the initrd and the guard cannot name
# different devices.
{ config, ... }:
let
  guard = config.loom.keyGuard;
in
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
    device = guard.rootDevice;
    keyFile = guard.keyDevice;
    keyFileSize = guard.keyBytes;
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
    # How wide the console ends up being is decided here, before Linux starts.
    #
    # branding.nix picks a 6-pixel font to get more columns out of the panel,
    # but that only divides whatever framebuffer the firmware hands over: a box
    # left in a 1024x768 GOP mode caps at 170 columns no matter what font is
    # loaded. `max` asks the firmware for its largest mode, and Linux inherits
    # whatever was last set. NixOS defaults this to "keep", which takes the
    # firmware's own default -- frequently the smallest one it has.
    #
    # There is deliberately no `video=` to go with it. On a box with a real KMS
    # driver the default is already the panel's preferred mode, so naming a
    # resolution could only pin a 4K panel lower; and where the display is
    # simpledrm on a firmware framebuffer, `video=` cannot change the mode at
    # all. It is a way down from native, not a way up.
    consoleMode = "max";
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
