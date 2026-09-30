# NVIDIA DGX Spark.
#
# The original appliance target: 20-core Grace CPU, Blackwell GPU, 128 GB
# unified memory, ConnectX-7 networking.
#
# Unlike the other two platforms this file imports nothing. nixos-hardware has
# no DGX Spark, GB10, Grace or Tegra content of any kind, and its
# common/gpu/nvidia/* profiles are desktop-dGPU and PRIME-laptop oriented --
# wrong for a headless box with one soldered accelerator. What the GPU needs
# here is plain nixpkgs, and it is all below.
{
  config,
  lib,
  pkgs,
  ...
}:
{
  loom.platform = {
    id = "spark";
    description = "NVIDIA DGX Spark";
    nixSystem = "aarch64-linux";

    # The GB10 Blackwell, reached through the open kernel modules. This is a
    # claim about the box in the sense platform.nix's `gpuVendor` documentation
    # means it: get it wrong and up.sh's check_host_resources hard-exits rather
    # than falling back to CPU, and the way out is a stick rebuilt with
    # --no-gpu. Confirm it on the hardware with `loom-platform-info`, whose GPU
    # and "GPU in containers" sections exist for exactly this -- /dev/nvidiactl
    # present, nvidia-smi naming a GB10, and a CDI spec for the container
    # runtime to hand the device to minikube with.
    #
    # `runsAiServices` follows from this, so setting it is also what brings back
    # Ollama and the console's assistant pane.
    gpuVendor = "nvidia";

    # The 10GbE RJ45 management port, claimed by r8169.
    #
    # The Spark also carries two QSFP cages with ConnectX-7 (mlx5_core), presenting
    # four 100G MACs across two PCIe Gen5 x4 links. Those ports are left unmatched:
    # they require QSFP modules and are not the intended operator access path.
    #
    # The Realtek management port is the correct default: it is always populated,
    # requires no transceiver, and is what NVIDIA documents for out-of-band access.
    # An operator can plug a standard ethernet cable directly into the RJ45 port
    # and reach the appliance without additional hardware.
    #
    # If you need to use the QSFP ports instead, rebuild with
    # `--interface enp1s0f0np0` (or the name `loom-platform-info` reports).
    netMatch = {
      Driver = "r8169";
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

  # ---------------------------------------------------------------------------
  # The GB10, on the stock kernel.
  #
  # Deliberately NOT graham33/nixos-dgx-spark, which is the obvious place to
  # look and is worth saying why:
  #
  #   * The GPU half is already here. Our nixpkgs pin carries NVIDIA 595.71.05
  #     with the open modules -- GB10 support landed in the 580 series -- and
  #     `hardware.nvidia-container-toolkit` is stock. Upstream takes
  #     `nvidiaPackages.production` too, so it would be the same driver.
  #   * What their fork buys is the ConnectX-7, not the Blackwell. Their own USB
  #     image offers both kernels and describes the split as NVIDIA kernel =
  #     "full GPU support and working Ethernet" against standard kernel =
  #     "Ethernet has problems", saying nothing about the GPU; and their
  #     `hardware.nvidia` block is not gated on the kernel choice.
  #   * That Ethernet claim is one README bullet with no issue, no commit
  #     message and no symptom behind it, written when mainline was ~6.11. Their
  #     fork is NV-Kernels 6.17.13; our pin is 6.18.49. Taking it means going
  #     back a major version on the box where NIC support is the open question.
  #   * Its kernel config also sets IOMMU_DEFAULT_PASSTHROUGH=y,
  #     IOMMU_DEFAULT_DMA_STRICT=n and ARM_SMMU_DISABLE_BYPASS_BY_DEFAULT=n,
  #     against the position platforms/evo-x2.nix takes explicitly about
  #     weakening DMA isolation on a box that gets given away. Should it ever be
  #     adopted, `iommu.passthrough=0 iommu.strict=1` puts both back without
  #     touching a kernel config they generate and test.
  #
  # So this is the cheap path, and `loom-platform-info` on a real Spark is what
  # decides whether it is enough. If it shows no usable wired NIC, that report
  # is the evidence for pinning their input -- as its own issue, and worth it
  # then. What their kernel would also bring is `cppc_cpufreq.auto_sel_mode=1`,
  # which they measure at ~3x single-thread memory bandwidth and which is inert
  # without it; on this image that is a real and accepted cost.
  # ---------------------------------------------------------------------------

  # NOT the desktop stack, and it must not be forced off the way the graphics
  # userspace is below. nixpkgs' hardware/video/nvidia.nix gates the entire
  # module on `lib.elem "nvidia"` here -- so dropping this takes the driver, the
  # kernel modules, nvidia-smi and the container toolkit with it, and trips
  # nvidia-container-toolkit's own assertion on the way. `services.xserver
  # .enable` stays false and no X configuration is generated; this list is read,
  # not acted on.
  services.xserver.videoDrivers = [ "nvidia" ];

  hardware.nvidia = {
    # GB10 has no closed-module option: Blackwell is open-modules only.
    open = true;
    # Also what puts the console on the monitor. This box has no other display
    # path -- which is why the driver stays even under --no-gpu.
    modesetting.enable = true;
    # Keeps the driver loaded between clients. Without it the first container to
    # ask for the GPU pays device initialisation, and on a 128 GB unified-memory
    # part that is not a small pause.
    nvidiaPersistenced = true;
  };

  # The host half of `up.sh --gpus nvidia`: generates the CDI spec that lets
  # docker, and through it the minikube node, hand /dev/nvidia* to a container.
  # up.sh's own preflight only checks that nvidia-smi counts a GPU, so without
  # this the box passes validation and then schedules Ollama onto a node that
  # advertises no nvidia.com/gpu at all.
  hardware.nvidia-container-toolkit.enable = true;

  # Override the CDI spec to allow containers to access GPUs.
  # The default nvidia-container-toolkit module generates a spec with
  # NVIDIA_VISIBLE_DEVICES=void which blocks GPU access. This fix sets it to "all".
  systemd.services.nvidia-cdi-fix = {
    description = "Fix NVIDIA CDI spec to allow GPU access in containers";
    wantedBy = [ "multi-user.target" ];
    after = [ "nvidia-container-toolkit-cdi-generator.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.bash}/bin/sh -c 'sed -i \"s/NVIDIA_VISIBLE_DEVICES=void/NVIDIA_VISIBLE_DEVICES=all/g\" /etc/cdi/nvidia.yaml && systemctl restart containerd'";
    };
  };

  # The same trade platforms/evo-x2.nix and platforms/nuc12.nix make with their
  # nixos-hardware GPU profiles: keep the driver library, drop the desktop
  # userspace.
  #
  # nixpkgs sets this to [ nvidia_x11.out <EGL ICD join> ]. The first is
  # load-bearing -- it is what puts libnvidia-ml.so.1 under /run/opengl-driver
  # /lib, which console.nix's btop dlopens for the GPU row and which the
  # container toolkit reads when it builds the CDI spec. The join behind it is
  # egl-wayland, egl-gbm and egl-x11: platform bindings for a compositor this
  # box does not have and will never run.
  #
  hardware.graphics.extraPackages = lib.mkForce [ config.hardware.nvidia.package.out ];

  # The 32-bit half has to be forced too, and on this platform that is not
  # tidiness -- it is what lets the configuration be evaluated at all.
  #
  # nixpkgs sets `extraPackages32` to [ nvidia_x11.lib32 <ICDs from
  # pkgs.pkgsi686Linux> ], and `pkgsi686Linux` throws outright on aarch64:
  # "i686 Linux package set can only be used with the x86 family". Nothing on a
  # booted box trips that, because `enable32Bit` is false and the option is
  # never read -- but anything that reads the option directly does, and
  # tests/appliance-hardware.nix asserts on it for every platform. Forcing it
  # empty makes the value well-defined instead of merely unreached, so the
  # assertion holds and flipping `enable32Bit` some day fails honestly rather
  # than exploding inside a package set that cannot exist here.
  hardware.graphics.extraPackages32 = lib.mkForce [ ];

  # nouveau cannot drive a GB10, and leaving it loadable only lets it race the
  # real driver for the framebuffer -- on a box whose console is the entire user
  # interface.
  boot.blacklistedKernelModules = [ "nouveau" ];

  hardware.enableRedistributableFirmware = true;
}
