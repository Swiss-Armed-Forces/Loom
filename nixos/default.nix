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
  # First three octets of the appliance network. build-appliance-image
  # randomises the middle two so two boxes on one wire cannot collide, and so a
  # visitor's own 10.0.0.0/24 or 192.168.1.0/24 does not either.
  loomSubnet ? "10.13.37",
  loomInterface ? "eth0",
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
      loomSubnet
      loomInterface
      enableGpu
      ;
    loomUser = "loom";
    loomRepoDir = "/home/loom/loom";
    # Written by the installer onto the encrypted root; displayed on login.
    recoveryPassphraseFile = "/var/lib/loom/recovery-passphrase";
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

  applianceModules = [
    ./box.nix
    ./modes.nix
    ./network.nix
    ./repo.nix
  ];

  boxSystem = evalConfig (applianceModules ++ [ ./box-hardware.nix ]);
in
{
  inherit pkgs loomSrc boxSystem;

  # The appliance itself.
  box = boxSystem.config.system.build.toplevel;

  # `nix-build ./nixos -A boxVm --argstr system x86_64-linux` then
  # `./result/bin/run-*-vm` -- for poking at the appliance by hand.
  boxVm = boxSystem.config.system.build.vm;

  # `nix-build ./nixos -A tests.appliance --argstr system x86_64-linux`
  # Asserts the values box.nix restates from up.sh and vars.sh, so the two
  # cannot drift apart unnoticed.
  tests.appliance = import ./tests/appliance.nix {
    inherit
      pkgs
      specialArgs
      applianceModules
      loomHostsJson
      minikubeIp
      loomSubnet
      ;
    inherit (specialArgs) loomUser loomRepoDir;
  };
}
