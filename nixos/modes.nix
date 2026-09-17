# The appliance's two boot modes, as a NixOS specialisation.
#
# A specialisation produces a second system closure and a second systemd-boot
# entry, sharing almost the whole store closure with the default. So the two
# modes cost a boot menu entry rather than a second image.
#
#   Run mode (default)  offline. Serves DHCP and *.loom, starts Loom with
#                       --offline --expose so visitors can reach it.
#   Setup mode          DHCP client. Builds and pulls every container image
#                       into minikube, once, then the box never needs the
#                       internet again.
#
# Setup mode is what removes the ~60 GB of container images from the USB stick:
# it writes them into minikube's store on the encrypted root, and run mode
# inherits them.
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
    path = with pkgs; [
      bash
      git
      git-lfs
      docker
      kubectl
      kubernetes-helm
      minikube
      skaffold
      yq
      jq
      gnutar
      gzip
      procps
      util-linux
    ];
  };
in
{
  options.loom.mode = lib.mkOption {
    type = lib.types.enum [
      "run"
      "setup"
    ];
    default = "run";
    description = ''
      Which appliance mode this system closure is. `run` is the default boot
      entry; `setup` is generated as a specialisation of it.
    '';
  };

  config = lib.mkMerge [
    # -------------------------------------------------------------------------
    # Run mode
    # -------------------------------------------------------------------------
    (lib.mkIf (cfg.mode == "run") {
      specialisation.setup.configuration = {
        loom.mode = lib.mkForce "setup";
        # Names the boot entry, so the two are distinguishable in the menu.
        system.nixos.tags = [ "setup" ];
      };

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
