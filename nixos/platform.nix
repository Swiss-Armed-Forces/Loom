# The platform dimension: which physical box this closure is for.
#
# Deliberately separate from `system`. Architecture and machine are different
# questions -- two platforms could share an architecture, and everything that
# actually differs between the DGX Spark and the GMKtec EVO-X2 (which NIC to
# claim, which initrd modules are needed) is a property of the machine rather
# than of aarch64 vs x86_64.
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

    wifiMatch = lib.mkOption {
      type = lib.types.nullOr (lib.types.attrsOf lib.types.str);
      default = null;
      description = ''
        systemd `[Match]` section identifying the radio the access point runs on,
        or `null` if this platform has no AP-capable one. wifi.nix renames
        whatever matches to `loomwl0`, for the same reason network.nix renames the
        wired NIC: nothing may depend on a kernel-assigned name.

        `null` is what makes `--wifi` fail during evaluation rather than on a box
        that boots without the access point it was built for.

        `Type = "wlan"` is the right default. Unlike the wired `netMatch`, a broad
        match is safe here -- it cannot claim an ethernet NIC or the NixOS test
        driver's virtio device -- and no one has yet confirmed which driver each
        box's radio binds to. Pin it once someone has run this on the hardware:
          iw list | grep -A15 'Supported interface modes'   # needs a '* AP' line
          udevadm info /sys/class/net/<iface> | grep ID_NET_DRIVER=
      '';
      example = {
        Driver = "mt7921e";
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
