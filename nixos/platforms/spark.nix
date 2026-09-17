# NVIDIA DGX Spark.
#
# The original appliance target: 20-core Grace CPU, Blackwell GPU, 128 GB
# unified memory, ConnectX-7 networking, reached over serial as often as over a
# monitor.
{
  loom.platform = {
    id = "spark";
    description = "NVIDIA DGX Spark";
    nixSystem = "aarch64-linux";

    # The Spark is usually driven over a serial cable, so the installer menu and
    # the primary console both go to ttyS0.
    hasSerialConsole = true;

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
