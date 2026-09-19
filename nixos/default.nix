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
# nixpkgs is supplied by cicd/build_appliance_image.sh, which takes devenv's
# `inputs.nixpkgs-stable` store path on its own --nixpkgs flag and passes it
# through as --arg nixpkgs.
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
  # Build the CPU-only image for a platform that declares a GPU vendor.
  #
  # An opt-out rather than an opt-in, because whether the box has a usable GPU
  # is a fact about the hardware and belongs in platforms/<id>.nix, not in the
  # invocation. What this is for is the box where that fact turns out to be
  # wrong: up.sh counts GPUs through the vendor's SMI tool and hard-exits when
  # it finds none, so an appliance that cannot see its own GPU serves nothing,
  # and there is no remote access to fix it with. This is the way back, and it
  # costs a new stick.
  disableGpu ? false,
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

  # The checkout the box carries, `.git` and materialised git-lfs payloads
  # included. cicd/build_appliance_image.sh is responsible for preparing the
  # directory; its `verify_repo` step asserts the properties up.sh depends on.
  #
  # Two kinds of thing are dropped on the way in, and this filter is the only
  # place either is expressed:
  #
  #   * Volatile `.git` internals. `builtins.path` hashes what it copies, so one
  #     file whose bytes differ between two runs of the same tag -- the index,
  #     which stores mtime, ctime and inode for all ~4000 files; git-lfs's
  #     timestamped logs -- yields a new store path, and with it a new appliance
  #     closure, a new squashfs and a new ~1.5 GB image for a working tree that
  #     is bit-for-bit identical. A handful of builds is enough to put ten
  #     gigabytes of near-duplicates in the store. Nothing on the box reads any
  #     of them: up.sh runs `git describe --exact-match --tags HEAD` (up.sh:240),
  #     which needs refs and objects, and git rebuilds an index on demand for
  #     anything that does want one.
  #
  #   * What a working checkout accumulates. The directory prepared by
  #     build_appliance_image.sh holds tracked files only, but the test targets
  #     below are documented (nixos/README.md) as taking `--arg repoSrc ./.`,
  #     and a developer's checkout of this repository runs to ~22 GB of which
  #     ~20 GB is build and test scratch -- .pytest_tmp, node_modules, .venv.
  #     Unfiltered, every run that touched any of it copied the lot in again.
  #
  # The second half is a safety net rather than a correctness boundary: a name
  # missing from it costs disk, never a broken image. The first half is not --
  # it is what keeps the store path stable, so it is paired with the
  # normalisation cicd/build_appliance_image.sh still has to do by hand
  # (`normalize_git_config`, for the one thing a path filter cannot express).
  loomSrc =
    let
      root = toString repoSrc;

      # Dropped wherever they appear, so backend/worker/.pytest_tmp goes the
      # same way as the one at the root.
      junkNames = [
        "node_modules"
        ".pnpm-store"
        ".venv"
        ".pytest_tmp"
        ".pytest_cache"
        ".mypy_cache"
        "__pycache__"
        ".minikube"
        ".devenv"
        ".direnv"
        ".skaffold"
        ".appliance-build"
        "result"
      ];

      # Dropped only at the position named. `logs` is the repository's own log
      # directory (.gitignore:1); the rest are the volatile .git entries.
      junkPaths = [
        "logs"
        ".git/index"
        ".git/logs"
        ".git/lfs/logs"
        ".git/lfs/tmp"
        ".git/ORIG_HEAD"
        ".git/FETCH_HEAD"
        ".git/COMMIT_EDITMSG"
      ];
    in
    builtins.path {
      name = "loom-src-${tag}";
      path = repoSrc;
      # Excluding a directory prunes its subtree, so this stays cheap on a tree
      # with a quarter of a million files in node_modules alone.
      filter =
        path: _type:
        let
          name = baseNameOf path;
        in
        !(
          builtins.elem name junkNames
          || builtins.elem (pkgs.lib.removePrefix "${root}/" path) junkPaths
          # `aitools` scratch directories: .loom_diagnose_<random> and friends.
          || pkgs.lib.hasPrefix ".loom_" name
        );
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

  # Every test node takes the real `loomSrc`, filtered but complete.
  #
  # A slim stand-in was tried here -- the wifi, usb-ingest and interface-fallback
  # tests read nothing out of the checkout, and skipping it would keep an edit
  # under nixos/ from re-copying the tree. It was dropped: with the filter above,
  # a working-checkout copy is ~120 MB rather than the 1.3 GB it used to be, so
  # there is little left to save, and a stand-in changes what the box *is*.
  # tests/appliance-wifi.nix caught exactly that -- its console-repaint subtest
  # reads the banner off /dev/vcsa1, and a box seeded from a fixture repository
  # painted a different one.
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
          { config, lib, ... }:
          {
            nixpkgs.pkgs = pkgs;
            # Setting `pkgs` alone leaves hostPlatform undefined, which anything
            # reading it (the installer needs `efiArch`) then trips over.
            nixpkgs.hostPlatform = system;

            # `--no-gpu`, applied by overriding the platform's own claim rather
            # than by threading a second flag through to everything that reads
            # it. modes.nix builds the up.sh arguments and box.nix picks the SMI
            # tool for the toolchain, and neither should have to ask the
            # question twice.
            loom.platform.gpuVendor = lib.mkIf disableGpu (lib.mkForce null);

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
    # Off the evaluated configuration rather than restated in the test, for the
    # same reason applianceInstall takes its device names that way: the test
    # asserts that the toolchain carries what up.sh demands of a GPU box, and
    # a test that decided for itself which box this is could not.
    inherit (boxSystem.config.loom.platform) gpuVendor;
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
