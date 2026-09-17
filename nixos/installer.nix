# The bootable USB stick.
#
# Built with `image.repart` rather than the NixOS installer ISO, because on
# aarch64 the ISO has no partition table at all: `isoImage.makeUsbBootable` is a
# silent no-op unless `makeBiosBootable` is also set, and that is asserted
# x86-only. There would be no GPT to carve the key partition out of.
#
# repart gives a real, spec-valid GPT, so flashing is `dd` plus one `dd` of the
# key -- and re-flashing is idempotent, which partition-table surgery never is.
{ boxSystem }:
{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
let
  efiArch = config.nixpkgs.hostPlatform.efiArch;

  installerScripts =
    pkgs.runCommand "loom-installer-scripts"
      {
        nativeBuildInputs = [ pkgs.makeWrapper ];
      }
      ''
        install -Dm444 ${./installer-scripts/common.sh} $out/libexec/loom/common.sh
        install -Dm555 ${./installer-scripts/install.sh} $out/bin/loom-install
        install -Dm555 ${./installer-scripts/menu.sh}    $out/bin/loom-menu
        install -Dm555 ${./installer-scripts/wipe.sh}    $out/bin/loom-wipe

        for program in $out/bin/*; do
          wrapProgram "$program" \
            --prefix PATH : ${
              lib.makeBinPath (
                with pkgs;
                [
                  bash
                  coreutils
                  cryptsetup
                  dosfstools
                  e2fsprogs
                  efibootmgr
                  gawk
                  gnugrep
                  gnused
                  nvme-cli
                  gptfdisk
                  parted
                  systemd
                  util-linux
                  nixos-install-tools
                ]
              )
            } \
            --set LOOM_INSTALLER_LIB "$out/libexec/loom" \
            --set LOOM_INSTALLER_BIN "$out/bin"
        done
      '';
in
{
  imports = [ "${modulesPath}/image/repart.nix" ];

  # ---------------------------------------------------------------------------
  # Live media: tmpfs root over a read-only store partition.
  # ---------------------------------------------------------------------------
  boot.initrd.systemd.enable = true;
  boot.initrd.availableKernelModules = [
    "usb_storage"
    "uas"
    "xhci_pci"
    "nvme"
    "erofs"
  ];

  fileSystems = {
    "/" = {
      fsType = "tmpfs";
      options = [ "mode=0755" ];
    };
    "/nix/.ro-store" = {
      device = "/dev/disk/by-partlabel/loom-live-store";
      fsType = "erofs";
      neededForBoot = true;
    };
    "/nix/.rw-store" = {
      fsType = "tmpfs";
      options = [ "mode=0755" ];
      neededForBoot = true;
    };
    "/nix/store".overlay = {
      lowerdir = [ "/nix/.ro-store" ];
      upperdir = "/nix/.rw-store/store";
      workdir = "/nix/.rw-store/work";
    };
  };

  # ---------------------------------------------------------------------------
  # Stick layout
  # ---------------------------------------------------------------------------
  image.repart = {
    name = "loom-installer";
    partitions = {
      "10-esp" = {
        contents = {
          "/EFI/BOOT/BOOT${lib.toUpper efiArch}.EFI".source =
            "${pkgs.systemd}/lib/systemd/boot/efi/systemd-boot${efiArch}.efi";
          "/EFI/Linux/${config.system.boot.loader.ukiFile}".source =
            "${config.system.build.uki}/${config.system.boot.loader.ukiFile}";
        };
        repartConfig = {
          Type = "esp";
          Format = "vfat";
          Label = "loom-live-esp";
          SizeMinBytes = "256M";
        };
      };

      "20-store" = {
        storePaths = [
          config.system.build.toplevel
          # The appliance rides along, so the install is entirely offline.
          boxSystem.config.system.build.toplevel
        ];
        repartConfig = {
          Type = "linux-generic";
          Format = "erofs";
          Label = "loom-live-store";
          Minimize = "guess";
        };
      };

      # Deliberately unformatted: cicd/build_appliance_image.sh writes 4096
      # random bytes straight into it after flashing, one key per stick. The
      # label is constant so a single appliance closure serves every box.
      "30-key" = {
        repartConfig = {
          Type = "linux-generic";
          Label = "loom-key";
          SizeMinBytes = "1M";
          SizeMaxBytes = "1M";
        };
      };
    };
  };

  boot.uki.name = "loom-installer";
  boot.loader.grub.enable = false;
  # The loader is placed by hand in the ESP contents above.
  boot.loader.systemd-boot.enable = false;

  # ---------------------------------------------------------------------------
  # Offline guarantees
  # ---------------------------------------------------------------------------
  nix.settings.substituters = lib.mkForce [ ];
  nix.settings.trusted-substituters = lib.mkForce [ ];
  nix.channel.enable = false;

  # Which closure loom-install should install, with zero evaluation at runtime.
  environment.etc."loom/target-system".text = "${boxSystem.config.system.build.toplevel}";

  environment.systemPackages = [ installerScripts ];

  # ---------------------------------------------------------------------------
  # The menu owns the console.
  # ---------------------------------------------------------------------------
  systemd.services."getty@tty1".enable = false;
  systemd.services."serial-getty@ttyS0".enable = false;

  systemd.services.loom-menu = {
    description = "Loom appliance installer menu";
    wantedBy = [ "multi-user.target" ];
    conflicts = [ "getty@tty1.service" ];
    restartIfChanged = false;
    serviceConfig = {
      # Let the boot messages finish first.
      Type = "idle";
      ExecStart = "${installerScripts}/bin/loom-menu";
      TTYPath = "/dev/tty1";
      TTYReset = true;
      TTYVHangup = true;
      StandardInput = "tty-force";
      StandardOutput = "tty";
      StandardError = "journal";
      Restart = "always";
      RestartSec = 2;
    };
  };

  # The Spark is usually reached over serial; the same menu, same behaviour.
  systemd.services.loom-menu-serial = {
    description = "Loom appliance installer menu (serial)";
    wantedBy = [ "multi-user.target" ];
    conflicts = [ "serial-getty@ttyS0.service" ];
    restartIfChanged = false;
    serviceConfig = {
      Type = "idle";
      ExecStart = "${installerScripts}/bin/loom-menu";
      TTYPath = "/dev/ttyS0";
      TTYReset = true;
      StandardInput = "tty-force";
      StandardOutput = "tty";
      StandardError = "journal";
      Restart = "always";
      RestartSec = 2;
    };
  };

  boot.kernelParams = [
    "console=tty1"
    "console=ttyS0,115200"
  ];

  networking.hostName = "loom-installer";
  networking.useDHCP = false;
  services.openssh.enable = false;
  documentation.enable = false;

  system.stateVersion = "26.05";
}
