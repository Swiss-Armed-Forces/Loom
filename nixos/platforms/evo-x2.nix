# GMKtec EVO-X2.
#
# AMD Ryzen AI Max+ 395 (Strix Halo) mini PC: x86_64, Radeon 8060S iGPU, dual
# M.2 NVMe, dual Realtek 2.5GbE, AMI UEFI.
#
# The appliance runs CPU-only here, same as on the Spark. Driving the iGPU needs
# ROCm support that does not exist in up.sh yet (see issue #284); amdgpu still
# loads, because it is what puts the installer menu on the monitor.
{
  loom.platform = {
    id = "evo-x2";
    description = "GMKtec EVO-X2 (AMD Ryzen AI Max+ 395)";
    nixSystem = "x86_64-linux";

    # Both 2.5GbE ports are Realtek, claimed by r8169, so the driver does not
    # single one out: whichever port udev processes first becomes loom0 and the
    # other keeps its kernel name. That is deliberate. Pinning a guessed
    # `Path = "pci-0000:xx:00.0"` instead would give a box with *no* loom0 at all
    # if the guess were wrong -- unrecoverable without a keyboard on an appliance
    # with no remote access, whereas "plug into the other port" is not.
    #
    # To pin a specific port once you have the box in front of you, read the
    # stable path off it and replace Driver with Path:
    #   udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
    netMatch = {
      Driver = "r8169";
    };

    # The MediaTek Wi-Fi/BT combo, matched by type rather than by driver -- see
    # platform.nix for why that is safe here and why it is not pinned. Only
    # consulted when the image is built with --wifi.
    wifiMatch = {
      Type = "wlan";
    };

    # Nothing extra. The obvious candidates for a box reached with a monitor
    # and a USB keyboard -- ahci, sd_mod, usbhid, hid_generic -- are already
    # pulled in by boot.initrd.includeDefaultModules, which defaults to true.
    # Verified by evaluating the closure rather than assumed; listing them again
    # would only suggest they were the difference.
    extraInitrdModules = [ ];
  };

  hardware.cpu.amd.updateMicrocode = true;
  # Realtek NICs and amdgpu both want firmware blobs that are redistributable
  # but not free, and neither is in the default closure.
  hardware.enableRedistributableFirmware = true;
}
