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
# LUKS is added in a later milestone; this is the plain-root variant so the
# system can be evaluated and boot-tested in a VM first.
{ ... }:
{
  fileSystems."/" = {
    device = "/dev/disk/by-partlabel/loom-root";
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
  ];

  boot.loader.systemd-boot = {
    enable = true;
    # The ESP is modest and aarch64 initrds are large.
    configurationLimit = 3;
  };
  # Appliance firmware: the loader is placed on the ESP directly and the boot
  # entry is managed by the installer, so there is no need to write EFI vars on
  # every rebuild.
  boot.loader.efi.canTouchEfiVariables = false;
  boot.loader.timeout = 5;
}
