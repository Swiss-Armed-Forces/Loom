# Entry point for the Loom appliance images.
#
# This is deliberately a plain default.nix and not a flake:
#
#   * Flake inputs strip `.git`, but up.sh's offline mode hard-requires
#     `git describe --exact-match --tags HEAD` (up.sh:236) inside the embedded
#     checkout. `builtins.path` copies the directory verbatim, `.git` included.
#   * devenv.lock plus the `# renovate:` comments in devenv.yaml already govern
#     nixpkgs. A nixos/flake.lock would be a second pin and guaranteed drift.
#
# nixpkgs is supplied by cicd/build_appliance_image.sh, which passes devenv's
# `inputs.nixpkgs-stable` store path through as ${LOOM_NIXPKGS}.
#
# `system` defaults to the host so the whole thing can be evaluated, built and
# boot-tested on x86_64 long before any aarch64 hardware is involved.
{
  nixpkgs ? throw "nixos: pass --arg nixpkgs <path>; normally done by the 'build-appliance-image' script",
  system ? builtins.currentSystem,
  repoSrc ? throw "nixos: pass --arg repoSrc <path to the prepared checkout>",
  tag ? "dev",
  loomHostsJson ? throw "nixos: pass --argstr loomHostsJson '[\"api.loom\", ...]'",
  minikubeIp ? "192.168.49.2",
  enableGpu ? false,
}:
let
  pkgs = import nixpkgs {
    inherit system;
    # devenv.yaml's `allowUnfree` is a devenv option and does not reach a
    # manually imported nixpkgs, so it has to be repeated here.
    config = {
      allowUnfree = true;
      nvidia.acceptLicense = true;
    };
  };

  # Copied verbatim, `.git` and materialised git-lfs payloads included.
  # cicd/build_appliance_image.sh is responsible for preparing the directory;
  # its `verify_repo` step asserts the properties up.sh depends on.
  loomSrc = builtins.path {
    name = "loom-src-${tag}";
    path = repoSrc;
  };

  specialArgs = {
    inherit
      loomSrc
      tag
      loomHostsJson
      minikubeIp
      enableGpu
      ;
    loomUser = "loom";
    loomRepoDir = "/home/loom/loom";
  };

  evalConfig =
    modules:
    import "${nixpkgs}/nixos/lib/eval-config.nix" {
      # eval-config.nix: "To set it modularly, pass `null`". `pkgs` already
      # carries the system, so passing both would be redundant and could
      # disagree.
      system = null;
      inherit specialArgs;
      modules = modules ++ [ { nixpkgs.pkgs = pkgs; } ];
    };

  boxSystem = evalConfig [
    ./box.nix
    ./box-hardware.nix
    ./repo.nix
  ];
in
{
  inherit pkgs loomSrc boxSystem;

  # The appliance itself.
  box = boxSystem.config.system.build.toplevel;

  # `nix-build ./nixos -A boxVm --argstr system x86_64-linux` then
  # `./result/bin/run-*-vm` -- the tier 2 test harness.
  boxVm = boxSystem.config.system.build.vm;
}
