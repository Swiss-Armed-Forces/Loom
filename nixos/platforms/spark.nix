# NVIDIA DGX Spark.
#
# The original appliance target: 20-core Grace CPU, Blackwell GPU, 128 GB
# unified memory, ConnectX-7 networking.
{
  loom.platform = {
    id = "spark";
    description = "NVIDIA DGX Spark";
    nixSystem = "aarch64-linux";

    # No gpuVendor, and on the one box here built around its GPU. NVIDIA drives
    # both the Blackwell and the ConnectX-7 through their own kernel fork, and
    # mainline Linux is reported to lose both -- so the NIC this appliance
    # serves DHCP and *.loom on is part of the same question. Nobody has booted
    # stock NixOS on a Spark to find out, and that is the first step; see the
    # GPU section of Documentation/appliance.md.
    #
    # Until then this box also ships without Ollama and open-webui, because
    # runsAiServices follows gpuVendor -- 128 GB of unified memory is no help
    # when nothing can reach the accelerator it is unified with. Making the GPU
    # work is what brings them back; there is nothing to set here for it.

    # ConnectX-7, claimed by mlx5_core. There is one such port, so the driver
    # alone identifies it. Confirm on the box with:
    #   udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
    netMatch = {
      Driver = "mlx5_core";
    };

    # Whatever radio the box carries, matched by type rather than by driver --
    # see platform.nix for why that is safe here and why it is not pinned.
    # Only consulted when the image is built with --wifi.
    wifiMatch = {
      Type = "wlan";
    };

    # Nothing beyond the shared USB/NVMe list: the LUKS key lives on the stick,
    # so the initrd never needs the network, and this is the module set the
    # appliance has always shipped with.
    extraInitrdModules = [ ];
  };
}
