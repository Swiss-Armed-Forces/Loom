# What nixos-hardware actually gives this platform, asserted at evaluation time.
#
# Unlike every other file in this directory this is not a VM test. Nothing here
# needs a kernel to run: every value is readable straight off the evaluated
# configuration, so this is a `runCommand` that either exits 0 or prints what
# disagreed. It costs seconds and no KVM, which is the point -- it is the first
# target cicd/run_appliance_tests.sh runs, so a mistake that breaks everything
# is reported before the twenty minutes of VM boots rather than after them.
#
# It exists because of a specific risk. `nixos-hardware` has no release
# branches and tracks nixos-unstable, while the appliance builds against
# devenv's `inputs.nixpkgs-stable` (nixos-26.05). Nothing in CI builds this
# image. So an upstream commit -- or a renovate bump of the pin -- could change
# what lands on a flashed stick, and the first person to find out would be the
# one holding it. These assertions are the tripwire.
#
# Two kinds of thing are checked:
#
#   * That the profile still does what platforms/<id>.nix says it does in
#     prose. If upstream drops `thermald` from the NUC profile, the comment
#     there becomes a lie and this fails.
#   * That the Loom-side `mkForce`s still bite. The platform files take the
#     kernel half of upstream's GPU profiles and force the desktop userspace
#     off; an upstream refactor that renames or re-parents those options would
#     silently restore them. Both closures are checked, because evalConfig
#     hands the platform module to the installer as well as the box -- so a
#     regression would put the Intel media stack on the stick too.
{
  pkgs,
  boxSystem,
  installerSystem,
}:
let
  inherit (pkgs) lib;

  box = boxSystem.config;
  installer = installerSystem.config;
  platform = box.loom.platform.id;

  elem = builtins.elem;

  # The GTT ceiling is asserted by prefix rather than by value. The numbers in
  # platforms/evo-x2.nix are explicitly provisional -- they are meant to be
  # retuned once somebody has run `loom-platform-info` on the box -- and a test
  # that pinned them would turn every retune into a two-file edit for no gain.
  # What must not regress is that a ceiling is set at all.
  hasParamPrefix = prefix: lib.any (p: lib.hasPrefix prefix p) box.boot.kernelParams;

  check = what: ok: { inherit what ok; };

  # True for every platform, including the one that imports nothing.
  shared = [
    (check "box: hardware.graphics.extraPackages is empty" (box.hardware.graphics.extraPackages == [ ]))
    (check "box: hardware.graphics.extraPackages32 is empty" (
      box.hardware.graphics.extraPackages32 == [ ]
    ))
    (check "box: hardware.graphics.enable32Bit is off" (box.hardware.graphics.enable32Bit == false))

    # The installer carries the same platform module, so the same must hold on
    # the stick. This is the half a VM test of the appliance could not see.
    (check "installer: hardware.graphics.extraPackages is empty" (
      installer.hardware.graphics.extraPackages == [ ]
    ))
    (check "installer: hardware.graphics.extraPackages32 is empty" (
      installer.hardware.graphics.extraPackages32 == [ ]
    ))
    (check "installer: hardware.graphics.enable32Bit is off" (
      installer.hardware.graphics.enable32Bit == false
    ))

    # nixos-hardware's Framework Desktop profile bumps boot.kernelPackages to
    # `linuxPackages_latest` when `pkgs.linux` is older than 6.14. We import the
    # common/* leaves rather than that profile, and our pin's default kernel is
    # newer than the gate anyway -- but if either of those facts changes, the
    # appliance would start building a second kernel without anyone deciding to.
    (check "box: kernel is still the nixpkgs default" (
      box.boot.kernelPackages.kernel.version == pkgs.linuxPackages.kernel.version
    ))
  ];

  # Per-platform. Each list says both what the profile must provide and what it
  # must not leak from a sibling platform.
  perPlatform = {
    # platforms/nuc12.nix -> intel/nuc/12wshi7
    nuc12 = [
      (check "nuc12: i915 in the box initrd (early KMS)" (elem "i915" box.boot.initrd.kernelModules))
      (check "nuc12: i915 in the installer initrd (early KMS)" (
        elem "i915" installer.boot.initrd.kernelModules
      ))
      (check "nuc12: thermald is enabled" box.services.thermald.enable)
      (check "nuc12: intel microcode updates are on" box.hardware.cpu.intel.updateMicrocode)
      (check "nuc12: no Strix Halo GTT parameters" (!hasParamPrefix "amdgpu.gttsize="))
      (check "nuc12: no amd_pstate parameter" (!elem "amd_pstate=active" box.boot.kernelParams))
    ];

    # platforms/evo-x2.nix -> common/cpu/amd/pstate.nix, common/gpu/amd, common/pc/ssd
    "evo-x2" = [
      (check "evo-x2: amdgpu in the box initrd (early KMS)" (elem "amdgpu" box.boot.initrd.kernelModules))
      (check "evo-x2: amdgpu in the installer initrd (early KMS)" (
        elem "amdgpu" installer.boot.initrd.kernelModules
      ))
      (check "evo-x2: amd_pstate=active is set" (elem "amd_pstate=active" box.boot.kernelParams))
      (check "evo-x2: amd microcode updates are on" box.hardware.cpu.amd.updateMicrocode)
      (check "evo-x2: a GTT size ceiling is set" (hasParamPrefix "amdgpu.gttsize="))
      (check "evo-x2: a TTM page limit is set" (hasParamPrefix "ttm.pages_limit="))
      # Deliberately absent -- see the comment in platforms/evo-x2.nix. An
      # upstream profile that started setting it would weaken DMA isolation on a
      # box that gets given away, silently.
      (check "evo-x2: IOMMU is not switched off" (!elem "amd_iommu=off" box.boot.kernelParams))
      (check "evo-x2: no thermald leaking from the Intel profile" (!box.services.thermald.enable))
    ];

    # platforms/spark.nix imports nothing: nixos-hardware has no DGX Spark, GB10,
    # Grace or Tegra content at all (see issue #303). This is the control -- it
    # catches a change that applies a profile to every platform rather than to
    # the one that asked for it.
    spark = [
      (check "spark: no i915 in the initrd" (!elem "i915" box.boot.initrd.kernelModules))
      (check "spark: no amdgpu in the initrd" (!elem "amdgpu" box.boot.initrd.kernelModules))
      (check "spark: thermald is off" (!box.services.thermald.enable))
      (check "spark: no amd_pstate parameter" (!elem "amd_pstate=active" box.boot.kernelParams))
      (check "spark: no Strix Halo GTT parameters" (!hasParamPrefix "amdgpu.gttsize="))
    ];
  };

  checks = shared ++ perPlatform.${platform};
  failures = builtins.filter (c: !c.ok) checks;

  report = lib.concatMapStringsSep "\n" (c: "  FAIL  ${c.what}") failures;
  passed = lib.concatMapStringsSep "\n" (c: "  ok    ${c.what}") checks;
in
pkgs.runCommand "loom-appliance-hardware-${platform}"
  {
    # Handy when a failure needs context -- `nix-build` prints the derivation
    # path, and these are readable straight out of it with `nix derivation show`.
    inherit platform;
    kernelParams = lib.concatStringsSep " " box.boot.kernelParams;
    initrdModules = lib.concatStringsSep " " box.boot.initrd.kernelModules;
  }
  (
    if failures == [ ] then
      ''
        echo "loom-appliance-hardware (${platform}): ${toString (builtins.length checks)} checks passed"
        cat <<'EOF'
        ${passed}
        EOF
        touch "$out"
      ''
    else
      ''
        echo "loom-appliance-hardware (${platform}): ${toString (builtins.length failures)} of ${toString (builtins.length checks)} checks failed" >&2
        cat >&2 <<'EOF'
        ${report}

        boot.kernelParams:        ${lib.concatStringsSep " " box.boot.kernelParams}
        boot.initrd.kernelModules: ${lib.concatStringsSep " " box.boot.initrd.kernelModules}

        This is nixos-hardware drift, or a Loom override that stopped applying.
        Read the import block in nixos/platforms/${platform}.nix, then the
        upstream profile it names, before changing anything here.
        EOF
        exit 1
      ''
  )
