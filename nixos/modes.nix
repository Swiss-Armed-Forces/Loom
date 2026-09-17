# The appliance's two boot modes, as a NixOS specialisation.
#
# A specialisation produces a second system closure and a second systemd-boot
# entry, sharing almost the whole store closure with the default. So the two
# modes cost a boot menu entry rather than a second image.
#
#   `Loom`                    (default) offline. Serves DHCP and *.loom, starts
#                             Loom with --offline --expose so visitors can
#                             reach it.
#   `Loom (first-time-setup)` DHCP client. Builds and pulls every container
#                             image into minikube, once, then the box never
#                             needs the internet again.
#
# Those are the titles as they appear in the menu: NixOS builds each from
# branding.nix's `distroName` plus the specialisation's own attribute name, so
# renaming the specialisation below is what renames the entry.
#
# First-time setup is what removes the ~60 GB of container images from the USB
# stick: it writes them into minikube's store on the encrypted root, and run
# mode inherits them.
#
# The section banners below say "setup mode" because they mark branches keyed on
# `loom.mode`, which stays `setup` internally -- only the boot entry is renamed.
{
  config,
  lib,
  pkgs,
  loomSubnet,
  loomUser,
  loomRepoDir,
  enableGpu,
  ...
}:
let
  cfg = config.loom;
  boxAddress = "${loomSubnet}.1";
  gpuArgs = lib.optionalString enableGpu " --gpus all";

  # Loom takes a long time to come up; skaffold's own offline profile allows
  # six hours (skaffold.yaml:384). Never let systemd shoot it in the head.
  commonService = {
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      User = loomUser;
      Group = "users";
      WorkingDirectory = loomRepoDir;
      TimeoutStartSec = "infinity";
      # up.sh backgrounds `sudo minikube tunnel`, which must outlive the unit.
      KillMode = "process";
      StandardOutput = "journal+console";
      StandardError = "journal+console";
    };
    after = [
      "docker.service"
      "loom-seed-repo.service"
      "network-online.target"
    ];
    requires = [
      "docker.service"
      "loom-seed-repo.service"
    ];
    wants = [ "network-online.target" ];
    path = [
      # `sudo` is a setuid wrapper in /run/wrappers/bin rather than a package, so
      # no entry in `loom.toolchain` can supply it. A login shell gets this
      # directory for free; a unit does not. up.sh checks for it (up.sh:406) and
      # `stop_expose_minikube` (up.sh:883-894) runs it on every invocation.
      "/run/wrappers"
      # Not in `loom.toolchain`: the docker module already puts a client in
      # systemPackages, and taking the package from the module rather than from
      # `pkgs` guarantees the unit's client matches the daemon it talks to.
      config.virtualisation.docker.package
    ]
    ++ cfg.toolchain
    ++ cfg.entrypoints;
  };
in
{
  options.loom.entrypoints = lib.mkOption {
    type = lib.types.listOf lib.types.package;
    internal = true;
    default = [ ];
    description = ''
      The `loom-up` / `loom-down` wrappers, as set by box.nix.

      They have to be on the PATH of the units below explicitly. Being in
      `environment.systemPackages` puts them in the operator's interactive
      shell but not in a systemd unit's environment, so without this the
      appliance boots and `loom.service` dies immediately with
      "exec: loom-up: not found".
    '';
  };

  options.loom.toolchain = lib.mkOption {
    type = lib.types.listOf lib.types.package;
    internal = true;
    default = [ ];
    description = ''
      Every package up.sh needs at runtime, as set by box.nix.

      Shared with `environment.systemPackages` rather than restated here. A
      unit's PATH is built solely from its `path` list plus a minimal default
      (coreutils, findutils, gnugrep, gnused, systemd); `/run/current-system/sw/bin`
      is never on it. So a package that is only in systemPackages is absent from
      the units below, and the failure looks like a broken up.sh rather than a
      broken PATH.
    '';
  };

  options.loom.mode = lib.mkOption {
    type = lib.types.enum [
      "run"
      "setup"
    ];
    default = "run";
    description = ''
      Which appliance mode this system closure is. `run` is the default boot
      entry; `setup` is generated as a specialisation of it.

      Internal, and deliberately not renamed alongside the boot entry: this is
      what network.nix and the branches below switch on, and no operator ever
      sees it. The menu says `Loom (first-time-setup)`.
    '';
  };

  config = lib.mkMerge [
    # -------------------------------------------------------------------------
    # Run mode
    # -------------------------------------------------------------------------
    (lib.mkIf (cfg.mode == "run") {
      specialisation.first-time-setup.configuration = {
        loom.mode = lib.mkForce "setup";
        # The specialisation's *name* is the boot entry: NixOS builds the title
        # as distroName + specialisation, so this attribute is what an operator
        # reads in the menu. The tag only shows up in the entry's second line
        # and in `nixos-version`; it matches so the two cannot drift.
        system.nixos.tags = [ "first-time-setup" ];
      };

      # Run mode has nothing to say on its way up: the disk unlocks from the
      # stick without a prompt, and everything an operator needs is on the login
      # screen afterwards (box.nix's `loom-info`). So let branding.nix's splash
      # own the screen instead of a scroll of kernel messages -- the plymouth
      # module contributes `splash` itself, `quiet` is what silences the log.
      #
      # Deliberately here rather than in box-hardware.nix: a specialisation
      # *adds* to its parent's kernel command line and cannot subtract from it,
      # so a `quiet` set for both modes could never be taken back for setup.
      boot.kernelParams = [
        "quiet"
        "udev.log_level=3"
      ];

      systemd.services.loom = lib.mkMerge [
        commonService
        {
          description = "Loom (offline)";
          wantedBy = [ "multi-user.target" ];
          after = [ "dnsmasq.service" ];
          script = ''
            exec loom-up --offline --expose ${boxAddress}${gpuArgs}
          '';
        }
      ];
    })

    # -------------------------------------------------------------------------
    # Setup mode
    # -------------------------------------------------------------------------
    (lib.mkIf (cfg.mode == "setup") {
      # No splash in this mode, and no `quiet` either (the run-mode branch above
      # is what sets that). Fetching every container image takes hours, and a
      # scrolling log is the only thing telling an operator it is working rather
      # than wedged -- a still logo here would be actively misleading.
      boot.kernelParams = [ "plymouth.enable=0" ];

      systemd.services.loom-fetch = lib.mkMerge [
        commonService
        {
          description = "Loom setup: build and pull all container images";
          wantedBy = [ "multi-user.target" ];

          # Hours of work. Do not silently redo it because someone rebooted.
          unitConfig.ConditionPathExists = "!${loomRepoDir}/.loom-setup-complete";

          script = ''
            echo "[*] Loom setup mode: populating minikube's image store."
            echo "[*] This needs internet and takes a long time. Watch with:"
            echo "[*]   journalctl -fu loom-fetch"

            # --delete tears the deployment down again afterwards: the goal here
            # is a warm image store, not a running stack. Documentation/
            # installation.md:107 prescribes exactly this before going offline.
            loom-up --offline --delete${gpuArgs}

            touch ${loomRepoDir}/.loom-setup-complete
            echo "[*] Image store populated. Reboot into the default entry to run Loom offline."
          '';
        }
      ];
    })
  ];
}
