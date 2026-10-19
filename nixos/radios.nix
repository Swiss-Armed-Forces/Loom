# Radios off, on the box and on the stick.
#
# Generic on purpose -- this covers the Spark's radios and the EVO-X2's MediaTek
# Wi-Fi/BT alike, and it is in both boot modes and in the installer, because a
# medium that is booted on the box is a medium whose radios are the box's.
#
# Bluetooth is unconditional. --wifi opts a box into an access point, not into a
# radio free-for-all, and nothing in Loom has ever wanted BT.
#
# A firmware-level disable in the box's own BIOS is the only true guarantee and
# is a documented manual step -- see Documentation/appliance.md. So is the other
# gap this cannot close: `insmod` names a .ko by path and never consults
# modprobe, so a root shell on the box can still load what is blocked here.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  allowWifi = config.loom.radios.allowWifi;
in
{
  options.loom.radios.allowWifi = lib.mkOption {
    type = lib.types.bool;
    default = false;
    internal = true;
    description = ''
      Leave the 802.11 stack loadable, for the access point wifi.nix runs. Set
      from `loom.wifi.enable` there, and false wherever wifi.nix is not imported
      -- which includes the installer stick, since that never runs an access
      point whatever the image was built with.
    '';
  };

  config = {
    # wpa_supplicant, i.e. joining someone else's network. Never wanted, in
    # either build: the access point is hostapd, which is the other direction.
    networking.wireless.enable = false;
    networking.networkmanager.enable = false;
    hardware.bluetooth.enable = false;

    # What `blacklist` does, and all it does: modprobe.d(5) scopes the keyword to
    # "that particular module's internal aliases", so it stops udev autoloading a
    # module when a device matches an alias the module itself declares. btusb
    # carries USB aliases and is genuinely held back by this; btintel, btbcm and
    # btrtl are its helpers and bluetooth is the core, none of which bind to a
    # device at all.
    boot.blacklistedKernelModules = [
      "bluetooth"
      "btusb"
      "btintel"
      "btbcm"
      "btrtl"
    ]
    # The 802.11 stack itself, without which hostapd has nothing to drive.
    ++ lib.optionals (!allowWifi) [
      "cfg80211"
      "mac80211"
    ];

    # And what `install` does, which is the half that stops a radio.
    #
    # The core modules above carry no device aliases -- the drivers do, and the
    # drivers are not named here: a radio is claimed by `mt7925e`
    # (pci:v000014C3d00007925) or `iwlwifi` (pci:v00008086d...), udev loads that,
    # and modprobe pulls mac80211 and cfg80211 in behind it as dependencies.
    # libkmod filters the blacklist over the *lookup* result, never over the
    # dependency list, so the module arrives anyway. It checks install commands
    # for every entry of the probe list instead, dependencies included, which is
    # why these two lines reach what the blacklist cannot.
    #
    # Two names are enough, and they are enough on hardware nobody wrote a
    # platform for: every WiFi driver, softmac and fullmac alike, depends on
    # cfg80211, and every Bluetooth transport -- btusb, hci_uart, btnxpuart,
    # btmtksdio -- depends on bluetooth. A list of drivers would have to be
    # guessed per box; a chokepoint does not.
    #
    # `options rfkill` is the third mechanism and the one with no window.
    # loom-rfkill-block below runs at multi-user.target, so a driver that does
    # load is live from probe until then, and a radio plugged in afterwards is
    # never reached at all. This makes every rfkill switch register soft-blocked,
    # from the kernel's own initialisation. It is a modprobe.d option rather than
    # a kernel parameter because rfkill is a module in this pin: a
    # `rfkill.default_state=0` on the command line would work -- libkmod reads
    # /proc/cmdline -- but this way the policy is one file, it applies when the
    # module is pulled in as a dependency, and `cat
    # /sys/module/rfkill/parameters/default_state` reads back what was asked for.
    #
    # NixOS copies this file into the systemd initrd (nixpkgs
    # system/boot/systemd/initrd.nix), where the store path below is not present.
    # The command then fails to exec, modprobe reports an error, and the module
    # is not inserted -- the same outcome, reached the same direction. Nothing
    # the initrd needs sits behind either of these.
    boot.extraModprobeConfig = ''
      options rfkill default_state=0
      install bluetooth ${pkgs.coreutils}/bin/false
    ''
    + lib.optionalString (!allowWifi) ''
      install cfg80211 ${pkgs.coreutils}/bin/false
    '';

    # Belt to the above's braces: a switch that registered before the policy
    # applied, or one whose driver is not blocked because it is neither 802.11
    # nor Bluetooth -- a WWAN modem, NFC, a GPS receiver -- is blocked here.
    #
    # Deliberately journal-only (the default): on the installer, loom-menu owns
    # tty1 and must not be written over.
    systemd.services.loom-rfkill-block = {
      description = if allowWifi then "Hard-block bluetooth" else "Hard-block all radios";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        # `rfkill block` exits non-zero when there is nothing to block, which on
        # a box whose radio drivers never loaded is the expected case.
        ExecStart = "${pkgs.util-linux}/bin/rfkill block ${if allowWifi then "bluetooth" else "all"}";
        SuccessExitStatus = [
          0
          1
        ];
      };
    };
  };
}
