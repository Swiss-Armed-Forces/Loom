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

    # The 10GbE RJ45 management port: a Realtek RTL8127 at 0007:01:00.0
    # (10ec:8127), claimed by r8169 -- the pin's kernel carries that id -- and
    # the only interface on the box that driver matches. Measured with
    # `loom-platform-info` on a Spark, as is everything else here.
    #
    # The two QSFP cages behind it are a ConnectX-7 presenting four 100G MACs
    # (mlx5_core), two per cage across PCI domains 0000 and 0002. They are left
    # unmatched deliberately: each needs a transceiver to carry anything, while
    # the RJ45 takes the cable an operator already has. Matching the driver
    # instead -- as this did until a box was available -- claims all four and
    # hands loom0 to whichever udev reaches first, which on the hardware was a
    # dark cage sitting beside a live port.
    #
    # To serve the appliance network off a QSFP port instead, build with
    # `--interface enp1s0f0np0`, using the name `loom-platform-info` reports:
    # only the domain-0000 pair is named that way, and the rest of this box
    # carries the PCI domain in the name (the RJ45 is enP7p1s0).
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
  # decided that it is enough: the RJ45 this box serves from comes up on the
  # pin's own r8169 and carries traffic, so the Ethernet claim above does not
  # reach the port the appliance uses. Their kernel would still bring
  # `cppc_cpufreq.auto_sel_mode=1`, which they measure at ~3x single-thread
  # memory bandwidth and which is inert without it; on this image that is a real
  # and accepted cost.
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

  # And the half of it nixpkgs leaves out, without which the box gets all the
  # way to `minikube start` and then dies on `Error response from daemon: AMD
  # CDI spec not found` -- on a machine with no AMD anything.
  #
  # docker 29 decides which GPU driver to register by looking for a binary on
  # *dockerd's own* PATH (moby's daemon/devices_linux.go):
  #
  #   * `getNVIDIADeviceDrivers` registers the `nvidia` driver only if
  #     `nvidia-cdi-hook` or `nvidia-container-runtime-hook` resolves there.
  #   * failing that, `getAMDDeviceDrivers` registers an `amd` driver whenever a
  #     CDI cache exists at all -- which the option above guarantees, since it
  #     turns on `features.cdi` -- and claims the generic `gpu` capability.
  #
  # `--gpus nvidia` reaches docker as `--gpus all` (minikube rewrites it in
  # pkg/drivers/kic/oci/oci.go), which is a request for the `gpu` capability and
  # nothing more specific, so the AMD driver is the one that matches. It then
  # reads the one vendor we do have, `nvidia.com`, decides it is not `amd.com`,
  # and refuses.
  #
  # The missing link is only the PATH: NixOS builds docker.service's as
  # `[ kmod ] ++ virtualisation.docker.extraPackages` and nothing else, and the
  # nvidia-container-toolkit module adds the `tools` output to the *rootless*
  # daemon's copy of that list while never adding it here. So the hook the spec
  # generator already points at by absolute path is invisible to the daemon that
  # has to decide whether NVIDIA exists.
  #
  # Done here rather than by teaching up.sh to pass minikube's `--gpus
  # nvidia.com` (which would emit `--device nvidia.com/gpu=all` and skip driver
  # selection entirely): that flag is four `case` arms in up.sh, on every host
  # Loom runs on, to work around something that is this box's business.
  virtualisation.docker.extraPackages = [
    (lib.getOutput "tools" config.hardware.nvidia-container-toolkit.package)
  ];

  # nixpkgs' mount list, minus the one entry that stops Kubernetes from
  # starting. Upstream's first mount is
  #
  #   { hostPath = /run/opengl-driver; containerPath = /run/opengl-driver; }
  #
  # and on a box where that reaches the minikube node, kubelet dies on
  #
  #   invalid Node Allocatable configuration. Resource "ephemeral-storage" has
  #   a reservation of {{18253611008 0}} but capacity of {{0 0}}
  #
  # The chain is worth writing out, because nothing in it is local to NVIDIA and
  # every link was confirmed on a Spark:
  #
  #   * The CDI spec binds the driver, glibc and every libnvidia-*.so into the
  #     node container -- 51 mounts, all of them on the box's one ext4 root.
  #   * cadvisor, inside kubelet, builds its partition table keyed by device and
  #     keeps only the FIRST mount it sees per device; its comment says "Avoid
  #     bind mounts", on the assumption that the first is the filesystem and the
  #     rest are binds of it. Here the first is a bind and the real one, /var,
  #     is 47 lines further down /proc/self/mountinfo.
  #   * So the root device is recorded as living at /run/opengl-driver -- which
  #     does not exist in the container. docker applies the bind at creation and
  #     the node's own systemd then mounts a tmpfs over /run, shadowing it. The
  #     mount stays in mountinfo; the path is gone.
  #   * cadvisor statfs's that path, gets ENOENT, and returns a zero-valued
  #     filesystem rather than an error -- so kubelet reports an
  #     ephemeral-storage capacity of 0, logs nothing about why, and refuses to
  #     start because up.sh's 17 GiB of reservations exceed it.
  #
  # Dropping the mount costs nothing that works today: it is shadowed in every
  # systemd-based container image, so nothing inside has ever been able to read
  # it. What it buys is the correct number rather than merely a non-zero one --
  # cadvisor falls through to the driver's own store path, which is reachable,
  # and reports the whole disk. Creating the missing directory by hand also
  # starts kubelet, but then the node advertises /run's tmpfs as its disk.
  #
  # Restated rather than filtered because the option is built with `mkMerge`
  # upstream, and a definition that read it in order to filter it would be
  # circular. The two toggles are honoured so they keep meaning what they say; a
  # bump that adds a mount up there will not carry into this list, which is what
  # tests/appliance-hardware.nix's two assertions on it are for.
  hardware.nvidia-container-toolkit.mounts =
    let
      driver = config.hardware.nvidia.package;
      toolkit = config.hardware.nvidia-container-toolkit;
      executable = name: {
        hostPath = lib.getExe' driver name;
        containerPath = "/usr/bin/${name}";
      };
    in
    lib.mkForce (
      [
        {
          hostPath = "${lib.getLib driver}";
          containerPath = "${lib.getLib driver}";
        }
        {
          hostPath = "${lib.getLib pkgs.glibc}/lib";
          containerPath = "${lib.getLib pkgs.glibc}/lib";
        }
        {
          hostPath = "${lib.getLib pkgs.glibc}/lib64";
          containerPath = "${lib.getLib pkgs.glibc}/lib64";
        }
      ]
      ++ lib.optionals toolkit.mount-nvidia-executables (
        map executable [
          "nvidia-cuda-mps-control"
          "nvidia-cuda-mps-server"
          "nvidia-debugdump"
          "nvidia-powerd"
          "nvidia-smi"
        ]
      )
      # nvidia-docker 1.0 paths, kept because the images that look for them are
      # not ours to change.
      ++ lib.optionals toolkit.mount-nvidia-docker-1-directories [
        {
          hostPath = "${lib.getLib driver}/lib";
          containerPath = "/usr/local/nvidia/lib";
        }
        {
          hostPath = "${lib.getLib driver}/lib";
          containerPath = "/usr/local/nvidia/lib64";
        }
      ]
    );

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
