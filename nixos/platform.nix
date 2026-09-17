# The platform dimension: which physical box this closure is for.
#
# Deliberately separate from `system`. Architecture and machine are different
# questions -- two platforms could share an architecture, and everything that
# actually differs between the DGX Spark and the GMKtec EVO-X2 (which NIC to
# claim, whether there is a serial port, which initrd modules are needed) is a
# property of the machine rather than of aarch64 vs x86_64.
#
# This file declares the options only. The values live in platforms/<id>.nix,
# and nixos/default.nix picks one from its `platform` argument.
{ lib, ... }:
{
  options.loom.platform = {
    id = lib.mkOption {
      type = lib.types.enum [
        "spark"
        "evo-x2"
      ];
      description = "Identifier of the appliance platform this closure targets.";
    };

    description = lib.mkOption {
      type = lib.types.str;
      description = ''
        Human-readable name of the box. Shown on the console banner, which on an
        appliance with no remote access is the only place it can reach anyone.
      '';
    };

    nixSystem = lib.mkOption {
      type = lib.types.str;
      description = ''
        The nix system this platform must be built for. nixos/default.nix
        asserts that it matches the `system` argument, so a
        `--platform evo-x2 --system aarch64-linux` mismatch fails during
        evaluation rather than at boot.
      '';
    };

    hasSerialConsole = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Whether the box has a usable serial port. When true the installer runs a
        second menu on ttyS0 and makes it the primary console. On a machine with
        no serial header that unit would fail and, with `Restart=always`, loop.
      '';
    };

    netMatch = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      description = ''
        systemd `[Match]` section identifying the wired interface that serves the
        appliance network. network.nix renames whatever matches to `loom0`, so
        that the static address, the dnsmasq binding and the banner never have to
        guess a kernel-assigned name.

        Keep this specific. A broad match (`Type = "ether"`) would also claim the
        interface of any VM this configuration is evaluated in, including the
        NixOS test driver's.
      '';
      example = {
        Driver = "mlx5_core";
      };
    };

    extraInitrdModules = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = ''
        Platform-specific additions to `boot.initrd.availableKernelModules`, for
        both the appliance and the installer. The shared list covers USB and
        NVMe; anything a particular box needs to reach its disk or its keyboard
        belongs here.
      '';
    };
  };
}
