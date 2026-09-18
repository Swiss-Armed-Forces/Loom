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
# `system` defaults to the host, which is what lets either platform be evaluated
# and boot-tested without the corresponding hardware to hand.
{
  nixpkgs ? throw "nixos: pass --arg nixpkgs <path>; normally done by the 'build-appliance-image' script",
  system ? builtins.currentSystem,
  # Which physical box this image is for. See platforms/<id>.nix; the chosen
  # platform's `nixSystem` is asserted against `system` below.
  platform ? "spark",
  repoSrc ? throw "nixos: pass --arg repoSrc <path to the prepared checkout>",
  tag ? "dev",
  loomHostsJson ? throw "nixos: pass --argstr loomHostsJson '[\"api.loom\", ...]'",
  # The namespace up.sh deploys into -- `NAMESPACE` in vars.sh, passed through by
  # cicd/build_appliance_image.sh for the same reason the host list is. It is
  # what the console session's k9s pane watches. Defaulted rather than thrown so
  # that `nix-build ./nixos -A tests.appliance` needs no arguments beyond the
  # ones it already takes.
  loomNamespace ? "loom",
  # The model the console's chat pane pins itself to -- `LOOM_CHAT_MODEL` in
  # vars.sh, passed through the same way the namespace is. Defaulted for the same
  # reason, and the default is the one model ollama/Dockerfile's production target
  # bakes in, because an air-gapped box has no way to fetch another.
  loomChatModel ? "huihui_ai/qwen3.5-abliterated:9b",
  minikubeIp ? "192.168.49.2",
  # First three octets of the appliance network. build-appliance-image
  # randomises the middle two so two boxes on one wire cannot collide, and so a
  # visitor's own 10.0.0.0/24 or 192.168.1.0/24 does not either.
  loomSubnet ? "10.13.37",
  # Normally empty: the appliance renames whatever the platform's `netMatch`
  # selects to `loom0` and pins everything to that. Set this only to override the
  # match with a specific kernel-assigned name.
  loomInterface ? "",
  enableGpu ? false,
  # The optional access point (nixos/wifi.nix). Off unless
  # build-appliance-image is given --wifi, which also generates the credentials
  # below; they are baked into the closure, so they are world-readable in
  # /nix/store and present on the stick. See Documentation/appliance.md.
  enableWifi ? false,
  wifiSsid ? "",
  wifiPsk ? "",
  # Empty means "no country code": 2.4GHz under regulatory domain 00. Setting one
  # moves the AP to 5GHz, which domain 00 forbids an AP from beaconing on at all.
  wifiCountry ? "",
  # As `loomInterface`, but for the radio: empty means "use the platform's match".
  wifiInterface ? "",
}:
let
  nixpkgsConfig = {
    # devenv.yaml's `allowUnfree` is a devenv option and does not reach a
    # manually imported nixpkgs, so it has to be repeated here.
    allowUnfree = true;
    nvidia.acceptLicense = true;
  };

  pkgs = import nixpkgs {
    inherit system;
    config = nixpkgsConfig;
  };

  # The machine doing the building, as opposed to `system`, which is the machine
  # the image is *for*. The two differ only when building under emulation; see
  # `nativeImageAssembly` below for the one place that has to care.
  hostSystem = builtins.currentSystem;

  hostPkgs = import nixpkgs {
    system = hostSystem;
    config = nixpkgsConfig;
  };

  # Resolved through an explicit table rather than by interpolating `platform`
  # into a path, so an unknown name produces a list of the valid ones instead of
  # a "file does not exist" from deep inside the evaluation.
  platformModules = {
    spark = ./platforms/spark.nix;
    evo-x2 = ./platforms/evo-x2.nix;
    nuc12 = ./platforms/nuc12.nix;
  };

  platformModule =
    platformModules.${platform}
      or (throw "nixos: unknown platform '${platform}'; known platforms: ${builtins.concatStringsSep ", " (builtins.attrNames platformModules)}");

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
      loomNamespace
      loomChatModel
      minikubeIp
      loomSubnet
      loomInterface
      enableGpu
      enableWifi
      wifiSsid
      wifiPsk
      wifiCountry
      wifiInterface
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
      modules = modules ++ [
        ./platform.nix
        platformModule
        (
          { config, ... }:
          {
            nixpkgs.pkgs = pkgs;
            # Setting `pkgs` alone leaves hostPlatform undefined, which anything
            # reading it (the installer needs `efiArch`) then trips over.
            nixpkgs.hostPlatform = system;

            # Catch a platform/system mismatch here rather than three hours into
            # a build, or -- worse -- on a box that will not boot.
            assertions = [
              {
                assertion = config.loom.platform.nixSystem == system;
                message =
                  "nixos: platform '${config.loom.platform.id}' is ${config.loom.platform.nixSystem}, "
                  + "but system is '${system}'. Drop --system, or pass a matching --platform.";
              }
            ];
          }
        )
      ];
    };

  # tests/appliance.nix builds its node from this list directly rather than
  # through evalConfig, so the platform modules have to be in here too. The
  # module system keys modules by path, so evalConfig importing them as well is
  # a no-op rather than a conflict.
  applianceModules = [
    ./platform.nix
    platformModule
    ./branding.nix
    ./box.nix
    ./console.nix
    ./key-guard.nix
    ./modes.nix
    ./network.nix
    ./repo.nix
    ./storage.nix
    ./usb-ingest.nix
    ./wifi.nix
  ];

  # Assemble the disk image with host binaries rather than target ones.
  #
  # `nixos/modules/image/repart-image.nix` builds the image with:
  #
  #   unshare --map-root-user fakeroot systemd-repart ...
  #
  # Taken from `pkgs`, those are aarch64 binaries, and under binfmt emulation
  # the `unshare` fails with "Invalid argument": the kernel only unshares a user
  # namespace for a single-threaded process, and qemu-user never is one. Every
  # other derivation in the closure emulates happily -- this is the single step
  # that cannot, and it is the last one, so it wastes the whole build.
  #
  # Nothing about the assembly is architecture-specific. repart copies opaque
  # bytes into partitions, and the partition types installer.nix asks for (`esp`
  # and `linux-generic`) carry no architecture. The one place the target does
  # appear is repart's `--architecture=` flag, which is a string in the
  # derivation's own attrs and is left exactly as it was. So the tools may just
  # as well be the host's: the emulated shell execs a native ELF, the kernel
  # runs it without qemu, and the unshare succeeds.
  #
  # Upstream has the same idea in `image.repart.package`, which defaults to
  # `buildPackages.systemd` "so that repart images are built with the build
  # platform's systemd, allowing for cross-compiled systems to work". That only
  # bites under real cross-compilation, where `buildPackages` is the host's;
  # with binfmt emulation `buildPackages == pkgs`. `util-linux` and `fakeroot`
  # are not options at all, so the whole `nativeBuildInputs` list is replaced.
  #
  # Building natively changes nothing, so leave the derivation alone there.
  nativeImageAssembly =
    image:
    if system == hostSystem then
      image
    else
      image.overrideAttrs (_: {
        nativeBuildInputs = with hostPkgs; [
          systemd # carries systemd-repart
          util-linux # unshare
          fakeroot
          # The filesystem tools repart-image.nix picks per `Format=`. Only vfat
          # is used today; the rest cost nothing and keep this from breaking the
          # day a partition changes format.
          dosfstools
          mtools
          e2fsprogs
          squashfsTools
          erofs-utils
          btrfs-progs
          xfsprogs
        ];
      });

  boxSystem = evalConfig (applianceModules ++ [ ./box-hardware.nix ]);

  # branding.nix is in both lists on purpose: the stick is the first Loom screen
  # anyone sees, and it would otherwise boot a NixOS-branded splash into a
  # Loom-branded installer.
  installerSystem = evalConfig [
    ./branding.nix
    (import ./installer.nix { inherit boxSystem; })
  ];
in
{
  inherit
    pkgs
    loomSrc
    boxSystem
    installerSystem
    ;

  # The appliance itself.
  box = boxSystem.config.system.build.toplevel;

  # The flashable USB stick. This is what `build-appliance-image` builds.
  installerImage = nativeImageAssembly installerSystem.config.system.build.image;

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
      loomChatModel
      minikubeIp
      loomSubnet
      ;
    inherit (specialArgs) loomUser loomRepoDir;
  };

  # `nix-build ./nixos -A tests.applianceInstall --argstr system x86_64-linux`
  # What the installer lays down on the internal disks, and whether the box
  # could find it again. The three names come off the appliance's own evaluated
  # configuration rather than being restated in the test, which is the whole
  # point: the installer and stage 1 have to agree, and a test that spelled the
  # path itself could agree with neither.
  tests.applianceInstall = import ./tests/appliance-install.nix {
    inherit pkgs;
    inherit (boxSystem.config.loom.storage) volumeGroup rootVolume rootDevice;
  };

  # `nix-build ./nixos -A tests.applianceWifi --argstr system x86_64-linux`
  # The --wifi build, which tests.appliance deliberately does not cover: it
  # forces off the two things (dnsmasq, static addresses) this one exercises.
  # `nix-build ./nixos -A tests.applianceUsbIngest --argstr system x86_64-linux`
  # Boots a box with scratch disks, puts real filesystems on them, and checks
  # what usb-ingest.nix decides about each -- above all that the LUKS key stick
  # is never touched.
  tests.applianceUsbIngest = import ./tests/appliance-usb-ingest.nix {
    inherit
      pkgs
      specialArgs
      applianceModules
      loomSubnet
      ;
  };

  # `nix-build ./nixos -A tests.applianceInterfaceFallback --argstr system x86_64-linux`
  # The box no platform matches: that a wired NIC is claimed as loom0 anyway,
  # which one is picked when there are several, and that switching it off
  # restores the old behaviour.
  tests.applianceInterfaceFallback = import ./tests/appliance-interface-fallback.nix {
    inherit
      pkgs
      specialArgs
      applianceModules
      loomSubnet
      ;
  };

  tests.applianceWifi = import ./tests/appliance-wifi.nix {
    inherit
      pkgs
      specialArgs
      applianceModules
      loomSubnet
      ;
  };
}
