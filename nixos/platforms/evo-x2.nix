# GMKtec EVO-X2.
#
# AMD Ryzen AI Max+ 395 (Strix Halo) mini PC: x86_64, Radeon 8060S iGPU, dual
# M.2 NVMe, dual Realtek 2.5GbE, AMI UEFI.
#
# The one platform here that offloads Ollama to its GPU. amdgpu is mainline and
# already loaded -- it is what puts the installer menu on the monitor -- and
# up.sh gained the AMD half in #284, so `--gpus amd` now has both ends.
{ lib, nixosHardware, ... }:
{
  # nixos-hardware has no GMKtec EVO-X2. What it has is the same SoC:
  # framework/desktop/amd-ai-max-300-series is a Strix Halo box, and everything
  # in it that is about the silicon rather than the chassis is in these three
  # leaves. They are imported directly instead of the Framework profile, which
  # also pulls framework/framework-tool.nix -- `pkgs.framework-tool` on a GMKtec
  # box, controlling an embedded controller that is not there.
  #
  #   common/cpu/amd/pstate.nix -> amd_pstate=active (and microcode, mkDefault)
  #   common/gpu/amd            -> amdgpu in the initrd, hardware.graphics
  #   common/pc/ssd             -> fstrim, which nixpkgs already defaults to
  #                                true, so nothing. Imported anyway so this
  #                                platform tracks the upstream Strix Halo set
  #                                rather than a subset of it that happens to
  #                                match today's defaults.
  #
  # The initrd amdgpu is the one worth having beyond the GPU work: early KMS is
  # what gets the console onto the panel's own mode from stage 1 rather than a
  # firmware framebuffer -- what box-hardware.nix's `consoleMode = "max"` and
  # branding.nix's banner-repaint unit are both working around.
  #
  # Also not taken from the Framework profile: its `boot.kernelPackages` bump,
  # which is gated on `pkgs.linux` being older than 6.14. Our nixpkgs pin is
  # nixos-26.05, whose default kernel is 6.18, so it would be inert -- but
  # tests/appliance-hardware.nix asserts the kernel is still the pin's default,
  # so a future bump that starts overriding it fails there rather than on a box.
  imports = [
    "${nixosHardware}/common/cpu/amd/pstate.nix"
    "${nixosHardware}/common/gpu/amd"
    "${nixosHardware}/common/pc/ssd"
  ];

  loom.platform = {
    id = "evo-x2";
    description = "GMKtec EVO-X2 (AMD Ryzen AI Max+ 395)";
    nixSystem = "x86_64-linux";

    # The Radeon 8060S, through ROCm. Two things have to hold for this and
    # neither is about the appliance:
    #
    #   * The kernel exposes /dev/kfd. amdgpu does that on its own; minikube's
    #     docker driver passes it and /dev/dri into the node container for
    #     `--gpus amd`, and the amd-gpu-device-plugin addon advertises
    #     `amd.com/gpu` off the back of it.
    #   * ROCm enumerates gfx1151. The ollama/ollama:rocm base image carries its
    #     own ROCm userspace, so the host needs none of it beyond `rocm-smi` for
    #     up.sh's preflight (box.nix adds it from this option).
    #
    # The second is the one to watch. Strix Halo is recent enough that ROCm
    # support for it arrived late, and a box where it does not enumerate fails
    # closed rather than dropping to CPU -- see the gpuVendor option in
    # ../platform.nix. `build-appliance-image --no-gpu` builds the CPU-only
    # stick this platform used to produce.
    gpuVendor = "amd";

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

  # Kept explicit even though common/cpu/amd now sets it from
  # `enableRedistributableFirmware` with mkDefault. The upstream default is a
  # rule about a general-purpose machine; this is a statement about a box that
  # gets handed to somebody, and it should not change because an import moved.
  hardware.cpu.amd.updateMicrocode = true;
  # Realtek NICs and amdgpu both want firmware blobs that are redistributable
  # but not free, and neither is in the default closure.
  hardware.enableRedistributableFirmware = true;

  # ---------------------------------------------------------------------------
  # How much memory the iGPU may reach
  #
  # On Strix Halo the firmware's UMA carve-out is not where the GPU's working
  # memory comes from. That carve-out is fixed, and Linux never sees it -- so a
  # large one is subtracted from the host and *still* caps what the GPU can use.
  # The real pool is GTT: ordinary system memory the GPU pins on demand. The
  # guidance in Documentation/appliance.md follows from this -- set the firmware
  # split to its minimum, and size the GPU here.
  #
  # Three things about these two numbers:
  #
  #   * They raise a CEILING; they do not reserve. Nothing leaves the host until
  #     the GPU actually pins it. That is what makes a generous value nearly
  #     free -- and what makes it dangerous if the GPU ever does pin all of it,
  #     on a box that is also running Elasticsearch, Tika, Gotenberg and a
  #     minikube node.
  #   * 64 GiB is half of the 128 GB box. Comfortably more than the baked-in
  #     chat and embedding models need, while leaving the rest of the stack more
  #     than twice the 25 GiB LOOM_MIN_MEMORY that up.sh checks.
  #     nix-strix-halo uses 80 GiB, on a machine that does nothing else.
  #   * They are PROVISIONAL. Every published Strix Halo write-up targets a
  #     6.11-6.14 kernel, where the defaults were much tighter than the 6.18 our
  #     pin ships. Run `loom-platform-info` on the box and compare
  #     mem_info_gtt_total against this ceiling: it may turn out to be redundant,
  #     or too low.
  #
  # Deliberately NOT here: `amd_iommu=off`, which several of those write-ups
  # recommend. The measurement against it puts IOMMU-on at roughly +3% latency
  # on a large iGPU workload, which is not worth weakening DMA isolation on a
  # box that gets given away.
  boot.kernelParams = [
    "amdgpu.gttsize=65536" # MiB
    "ttm.pages_limit=16777216" # 4 KiB pages, so also 64 GiB
  ];

  # nixos-hardware's common/gpu/amd assumes a desktop session. `hardware.graphics
  # .enable` stays on -- it is what the amdgpu integration expects, and Mesa is
  # nothing beside ~60 GB of container layers -- but the 32-bit half goes: there
  # is no X, no Wayland and no 32-bit anything here, and the ROCm userspace
  # Ollama needs lives inside ollama/ollama:rocm rather than on the host.
  #
  # Forced rather than defaulted, and asserted by tests/appliance-hardware.nix,
  # because an upstream refactor could otherwise quietly put them back. They land
  # in the installer's closure as well as the box's -- evalConfig gives the
  # platform module to both -- so this keeps them off the stick too.
  hardware.graphics.enable32Bit = lib.mkForce false;
  hardware.graphics.extraPackages = lib.mkForce [ ];
  hardware.graphics.extraPackages32 = lib.mkForce [ ];
}
