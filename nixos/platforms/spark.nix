# NVIDIA DGX Spark.
#
# The original appliance target: 20-core Grace CPU, Blackwell GPU, 128 GB
# unified memory, ConnectX-7 networking.
{
  loom.platform = {
    id = "spark";
    description = "NVIDIA DGX Spark";
    nixSystem = "aarch64-linux";

    # ConnectX-7, claimed by mlx5_core. There is one such port, so the driver
    # alone identifies it. Confirm on the box with:
    #   udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
    netMatch = {
      Driver = "mlx5_core";
    };

    # Nothing beyond the shared USB/NVMe list: the LUKS key lives on the stick,
    # so the initrd never needs the network, and this is the module set the
    # appliance has always shipped with.
    extraInitrdModules = [ ];
  };
}
