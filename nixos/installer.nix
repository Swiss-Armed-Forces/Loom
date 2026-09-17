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
  tag,
  ...
}:
let
  efiArch = config.nixpkgs.hostPlatform.efiArch;
  hasSerial = config.loom.platform.hasSerialConsole;

  # The read-only store carried by the stick.
  #
  # Built with mksquashfs rather than handed to systemd-repart as `storePaths`,
  # for two reasons that both only show up at install time:
  #
  #   * repart turns each store path into a `CopyFiles=` instruction, and that
  #     dereferences a store path that is itself a symlink. `nix-<v>-man` is
  #     one: it is a symlink to `nix-manual-<v>-man`. On the stick it became a
  #     134-file directory, so its NAR no longer matched the hash Nix had for
  #     it, and the install died with "hash mismatch importing path".
  #   * make-squashfs also emits `nix-path-registration`, which is what lets
  #     the paths be registered as valid below. Without that, nixos-install
  #     cannot copy them at all.
  #
  # Paths land at the root of the image, which is what /nix/.ro-store is
  # mounted as and what the overlay lowerdir below expects.
  storeImage = pkgs.callPackage "${modulesPath}/../lib/make-squashfs.nix" {
    storeContents = [
      config.system.build.toplevel
      # The appliance rides along, so the install is entirely offline.
      boxSystem.config.system.build.toplevel
    ];
    # xz is the default and is markedly slower to build and to page in; the
    # stick has room to spare.
    comp = "zstd -Xcompression-level 6";
  };

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
                  diffutils # `cmp`, used by key_state
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
                  # nixos-install is a wrapper around `nix-env` and friends and
                  # does not carry them itself, so without this the install
                  # dies with "nix-env: command not found" -- after the disk
                  # has already been partitioned and encrypted.
                  config.nix.package
                ]
              )
            } \
            --set LOOM_INSTALLER_LIB "$out/libexec/loom" \
            --set LOOM_INSTALLER_BIN "$out/bin" \
            --set LOOM_EFI_ARCH "${efiArch}" \
            --set LOOM_TAG "${tag}" \
            --set LOOM_PLATFORM "${config.loom.platform.description}"
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
    "squashfs"
  ]
  ++ config.loom.platform.extraInitrdModules;

  fileSystems = {
    "/" = {
      fsType = "tmpfs";
      options = [ "mode=0755" ];
    };
    "/nix/.ro-store" = {
      device = "/dev/disk/by-partlabel/loom-live-store";
      fsType = "squashfs";
      neededForBoot = true;
    };
    "/nix/.rw-store" = {
      fsType = "tmpfs";
      options = [ "mode=0755" ];
      neededForBoot = true;
    };
    "/nix/store".overlay = {
      # The partition root *is* the store: make-squashfs hands mksquashfs each
      # store path as its own source, so they land at the top of the image
      # rather than under a `nix/store/` prefix. This is the same layout the
      # installer ISO's squashfs has, and the reason `storeImage` above is built
      # with mksquashfs rather than assembled by repart -- with repart's
      # `storePaths` the prefix is preserved and this would have to be
      # `/nix/.ro-store/nix/store` instead.
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

      # Written as a finished filesystem image rather than assembled in place;
      # see `storeImage` above for why.
      "20-store" = {
        repartConfig = {
          Type = "linux-generic";
          Label = "loom-live-store";
          # No `Minimize`: the partition is sized from the finished image, so
          # there is nothing for repart to guess at and nothing to under-allocate.
          CopyBlocks = "${storeImage}";
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

  # The stick's one advantage over the appliance: systemd-stub draws this while
  # the kernel is still loading, so the Loom logo is up before Linux exists.
  # branding.nix's plymouth then picks the same logo up with no visible seam.
  # Interpolated, not passed as a package: `boot.uki.settings` is an INI file
  # and takes atoms only.
  boot.uki.settings.UKI.Splash = "${config.loom.branding.splashBmp}";
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

  # nixos-install copies the appliance closure out of the stick's read-only
  # store, and for that the daemon has to consider those paths valid. They are
  # all present on the squashfs, but nothing has told the Nix database they
  # exist, so the install dies with "path ... is required, but there is no
  # substituter that can build it" -- after having already partitioned and
  # encrypted the disk.
  #
  # The manifest comes from make-squashfs, which writes it at the root of the
  # image next to the store paths it describes. Same approach as the NixOS
  # netboot and ISO media.
  systemd.services.loom-register-store = {
    description = "Register the appliance closure in the Nix database";
    wantedBy = [ "multi-user.target" ];
    before = [
      "loom-menu.service"
    ]
    ++ lib.optional hasSerial "loom-menu-serial.service";
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    script = ''
      ${lib.getExe' config.nix.package "nix-store"} --load-db < /nix/.ro-store/nix-path-registration
    '';
  };

  # ---------------------------------------------------------------------------
  # The menu owns the console.
  # ---------------------------------------------------------------------------
  systemd.services."getty@tty1".enable = false;
  systemd.services."serial-getty@ttyS0".enable = lib.mkIf hasSerial false;

  systemd.services.loom-menu = {
    description = "Loom appliance installer menu";
    wantedBy = [ "multi-user.target" ];
    conflicts = [ "getty@tty1.service" ];
    # Both this and plymouth want tty1, and `Type = "idle"` only waits for the
    # job queue to drain -- it knows nothing about who still holds the console.
    # Without the ordering the menu can paint underneath a splash that has not
    # released DRM yet, which looks exactly like a stick that failed to boot.
    after = [ "plymouth-quit-wait.service" ];
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
      # Not "journal". The scripts print their own prompts to stdout, but
      # everything that goes wrong arrives on stderr -- `err`, and the output of
      # cryptsetup, sgdisk and nixos-install underneath it. Sent to the journal
      # that is a failed install with no visible reason, on media whose whole
      # job is being diagnosable by whoever is standing at the box.
      StandardError = "tty";
      Restart = "always";
      RestartSec = 2;
    };
  };

  # Only on boxes that have a serial port. The Spark is usually reached over
  # one; the EVO-X2 has no header at all, and there `Restart=always` on a
  # TTYPath that cannot be opened is a restart loop every two seconds.
  # ConditionPathExists is the belt to that braces: a platform can be wrong
  # about its own hardware, a missing device node cannot.
  systemd.services.loom-menu-serial = lib.mkIf hasSerial {
    description = "Loom appliance installer menu (serial)";
    wantedBy = [ "multi-user.target" ];
    conflicts = [ "serial-getty@ttyS0.service" ];
    restartIfChanged = false;
    unitConfig.ConditionPathExists = "/dev/ttyS0";
    serviceConfig = {
      Type = "idle";
      ExecStart = "${installerScripts}/bin/loom-menu";
      TTYPath = "/dev/ttyS0";
      TTYReset = true;
      StandardInput = "tty-force";
      StandardOutput = "tty";
      # Not "journal". The scripts print their own prompts to stdout, but
      # everything that goes wrong arrives on stderr -- `err`, and the output of
      # cryptsetup, sgdisk and nixos-install underneath it. Sent to the journal
      # that is a failed install with no visible reason, on media whose whole
      # job is being diagnosable by whoever is standing at the box.
      StandardError = "tty";
      Restart = "always";
      RestartSec = 2;
    };
  };

  # This is rescue media. If stage 1 fails at a site, whoever is standing in
  # front of the box needs a shell to diagnose it, not a locked sulogin prompt.
  # (The appliance itself deliberately does NOT get this.)
  boot.initrd.systemd.emergencyAccess = true;

  # The last `console=` wins as /dev/console. On a serial box that should be the
  # serial line; on one without, naming ttyS0 at all would send boot output to a
  # port nobody can read.
  #
  # Deliberately no `quiet`, unlike the appliance in modes.nix. This is the
  # recovery medium: the monitor gets branding.nix's splash, and the kernel log
  # keeps reaching the serial line and the journal, which is the entire reason
  # somebody boots the stick at a box that will not come up.
  #
  # Equally deliberately no `systemd.journald.forward_to_console=1`. It would
  # put every service's output on /dev/console, which here is the console the
  # menu owns -- tty1, or ttyS0 on a serial box. The menu redraws from the top
  # each pass, so the result is a status block interleaved with journal lines.
  # What that parameter is for is covered above: the kernel log is already
  # unsuppressed, and `emergencyAccess` handles the case where it fails early.
  boot.kernelParams = [
    "console=tty1"
  ]
  ++ lib.optional hasSerial "console=ttyS0,115200"
  # plymouth renders a text fallback onto every console it finds, and on a
  # serial box /dev/console *is* ttyS0 -- so without this it would type its
  # splash over the operator's serial installer menu.
  ++ lib.optional hasSerial "plymouth.ignore-serial-consoles";

  networking.hostName = "loom-installer";
  networking.useDHCP = false;
  services.openssh.enable = false;
  documentation.enable = false;

  system.stateVersion = "26.05";
}
