# Intel NUC 12 Pro ("Wall Street Canyon").
#
# Alder Lake-P mini PC: x86_64, Iris Xe iGPU, M.2 NVMe, one Intel 2.5GbE port,
# Intel AX211 Wi-Fi 6E, AMI UEFI. Covers both chassis -- the slim NUC12WSK and
# the tall NUC12WSH -- because they share a board and a NIC.
#
# The appliance runs CPU-only here, same as on the other platforms; i915 still
# loads, because it is what puts the installer menu on the monitor.
{
  loom.platform = {
    id = "nuc12";
    description = "Intel NUC 12 Pro (Wall Street Canyon)";
    nixSystem = "x86_64-linux";

    # The i225/i226 2.5GbE part, claimed by igc. The slim kit has exactly one,
    # so the driver identifies it outright.
    #
    # A tall NUC12WSH fitted with the second-LAN expansion has two, and then this
    # match cannot single one out -- the same situation platforms/evo-x2.nix
    # documents for its pair of Realtek ports, with the same answer: whichever
    # udev processes first becomes loom0, and "plug into the other port" is the
    # fix. To pin one once the box is in front of you, read its stable path off
    # it and rebuild with --interface:
    #   udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
    netMatch = {
      Driver = "igc";
    };

    # The AX211, matched by type rather than by driver -- see platform.nix for
    # why that is safe here and why it is not pinned. Only consulted when the
    # image is built with --wifi.
    #
    # Whether this radio can run an access point at all is UNVERIFIED: Intel
    # parts have historically been patchy for AP mode. wifi.nix's loom-wifi-check
    # reports it on the console if hostapd never starts, with the `iw list`
    # command to confirm.
    wifiMatch = {
      Type = "wlan";
    };

    # Nothing extra. NVMe, USB storage, usbhid and hid_generic are already in
    # boot.initrd.includeDefaultModules, which defaults to true, and the LUKS key
    # comes off the stick rather than the network.
    extraInitrdModules = [ ];
  };

  hardware.cpu.intel.updateMicrocode = true;
  # i915 and the AX211 both want firmware blobs that are redistributable but not
  # free, and neither is in the default closure.
  hardware.enableRedistributableFirmware = true;
}
