# Intel NUC 12 Pro ("Wall Street Canyon").
#
# Alder Lake-P mini PC: x86_64, Iris Xe iGPU, M.2 NVMe, one Intel 2.5GbE port,
# Intel AX211 Wi-Fi 6E, AMI UEFI. Covers both chassis -- the slim NUC12WSK and
# the tall NUC12WSH -- because they share a board and a NIC.
#
# The appliance runs CPU-only here, same as on the other platforms; i915 still
# loads, because it is what puts the installer menu on the monitor.
{ lib, nixosHardware, ... }:
{
  # nixos-hardware has this exact box: "12WSHi7" spells out Wall Street canyon,
  # H (the tall chassis) and i7. The slim WSK and the i3/i5 kits share the board
  # and the silicon, so the profile covers them too.
  #
  # Four lines upstream, and this is their whole transitive effect:
  #   common/cpu/intel/alder-lake -> microcode (mkDefault), and
  #   common/gpu/intel/alder-lake -> i915 in the initrd + the media/compute
  #                                  userspace, which the block below drops
  #   common/pc                   -> an ath3k blacklist, inert here
  #   common/pc/ssd               -> fstrim, which nixpkgs already defaults to
  #                                  true, so also inert
  #   (the profile itself)        -> thermald
  #
  # thermald and the initrd i915 are the only two that do anything. The first
  # because
  # Alder Lake-P in a chassis this size throttles without it; the second because
  # early KMS is what gets the console onto the panel's own mode from stage 1,
  # rather than whatever framebuffer the firmware left behind -- which is the
  # thing box-hardware.nix's `consoleMode = "max"` and branding.nix's
  # banner-repaint unit are both working around.
  imports = [ "${nixosHardware}/intel/nuc/12wshi7" ];

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

    # The kits ship with a single SO-DIMM and the iGPU takes its share before
    # Linux sees the rest, which lands around 15 GiB usable -- well under
    # LOOM_MIN_MEMORY (25Gi in vars.sh). Two facts follow, and both are about
    # this box rather than about policy:
    #
    #   * Ollama does not fit. The image bakes in a 9b chat model and an
    #     embedding model, and they are the single largest consumer by a wide
    #     margin. Without them the rest of the stack is a plausible fit.
    #   * check_host_resources would refuse to start at all, and it is a hard
    #     exit rather than a warning.
    #
    # Fit both SO-DIMM slots and `meetsResourceMinimum` can go: the board takes
    # 64 GB, and a NUC with real memory clears the check.
    #
    # `runsAiServices` is a separate matter and stays either way. It is already
    # what the default would give -- no gpuVendor above, because Loom has no
    # path to an Intel iGPU at all -- and it is written out because memory is an
    # independent reason for it. Give this box 64 GB and an Iris Xe still cannot
    # run the models; the line below is what stops the default's disappearance
    # from quietly turning them on.
    runsAiServices = false;
    meetsResourceMinimum = false;

    # Nothing extra. NVMe, USB storage, usbhid and hid_generic are already in
    # boot.initrd.includeDefaultModules, which defaults to true, and the LUKS key
    # comes off the stick rather than the network.
    extraInitrdModules = [ ];
  };

  # Kept explicit even though common/cpu/intel/cpu-only.nix now sets it from
  # `enableRedistributableFirmware` with mkDefault. The upstream default is a
  # rule about a general-purpose machine; this is a statement about a box that
  # gets handed to somebody, and it should not change because an import moved.
  hardware.cpu.intel.updateMicrocode = true;
  # i915 and the AX211 both want firmware blobs that are redistributable but not
  # free, and neither is in the default closure.
  hardware.enableRedistributableFirmware = true;

  # nixos-hardware's GPU profiles assume a desktop session. Take the kernel half
  # -- i915 in the initrd, above -- and drop the userspace: this box has no X, no
  # Wayland and no 32-bit anything, and Loom has no path to an Intel iGPU at all
  # (see `runsAiServices` above), so intel-media-driver, intel-compute-runtime
  # and vpl-gpu-rt are weight with no consumer.
  #
  # Forced rather than defaulted, and asserted by tests/appliance-hardware.nix,
  # because an upstream refactor could otherwise quietly put them back. They land
  # in the installer's closure as well as the box's -- evalConfig gives the
  # platform module to both -- so this keeps them off the stick too.
  hardware.graphics.enable32Bit = lib.mkForce false;
  hardware.graphics.extraPackages = lib.mkForce [ ];
  hardware.graphics.extraPackages32 = lib.mkForce [ ];
}
