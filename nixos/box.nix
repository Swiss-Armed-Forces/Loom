# The Loom appliance system.
#
# Everything up.sh mutates on the host imperatively is declared here instead, so
# that a `nixos-rebuild` cannot silently revert it. The appliance therefore runs
# up.sh with those two steps skipped -- see the `loom-up` wrapper below.
{
  config,
  lib,
  pkgs,
  loomHostsJson,
  minikubeIp,
  loomUser,
  loomRepoDir,
  recoveryPassphraseFile,
  tag,
  ...
}:
let
  # Ship a wrapper rather than only documenting the flags. Running bare `up.sh`
  # here is actively harmful: `setup_system` writes /etc/sysctl.d/99-loom.conf
  # that NixOS ignores, and `install_host_entries` replaces the /etc/hosts store
  # symlink with a mutable copy (up.sh:963-977) -- undoing the declarative work
  # this module exists to do. writeShellApplication also shellchecks at build
  # time, matching the rest of the repo.
  loom-up = pkgs.writeShellApplication {
    name = "loom-up";
    runtimeInputs = with pkgs; [
      minikube
      coreutils
    ];
    text = ''
      cd ${lib.escapeShellArg loomRepoDir}

      # networking.hosts pins *.loom at a fixed address; if minikube ever lands
      # somewhere else, fail loudly instead of serving a silently broken stack.
      if ip="$(minikube ip 2>/dev/null)" && [ "$ip" != ${lib.escapeShellArg minikubeIp} ]; then
        echo >&2 "[!] minikube is at $ip but *.loom is pinned to ${minikubeIp} in /etc/hosts."
        echo >&2 "[!] Run 'minikube delete' and retry, or rebuild the image with a matching IP."
        exit 1
      fi

      exec ./up.sh --skip-setup_system --skip-install_host_entries "$@"
    '';
  };

  loom-down = pkgs.writeShellApplication {
    name = "loom-down";
    text = ''
      cd ${lib.escapeShellArg loomRepoDir}
      exec ./up.sh --down "$@"
    '';
  };
in
{
  # ---------------------------------------------------------------------------
  # Host tuning -- mirrors up.sh `setup_system` (up.sh:616-684).
  #
  # up.sh additionally persists these to /etc/sysctl.d/99-loom.conf; NixOS writes
  # its own /etc/sysctl.d/60-nixos.conf from the values below, so that file is
  # redundant here and `--skip-setup_system` keeps up.sh from creating it.
  # ---------------------------------------------------------------------------
  boot.kernel.sysctl = {
    "vm.max_map_count" = 1677720; # NixOS default 1048576 -> raised
    "vm.overcommit_memory" = 1;
    "fs.inotify.max_user_watches" = 655360; # NixOS default 524288 -> raised
    # Deliberately LOWER than the NixOS default of 524288. up.sh forces this
    # value with an equality test rather than a floor, so 1280 is what every
    # Loom deployment is actually tested against. Keep the two in sync.
    "fs.inotify.max_user_instances" = 1280;
    "fs.file-max" = 2097152;
    "vm.swappiness" = 1;
    "vm.dirty_background_ratio" = 10;
    "vm.dirty_ratio" = 40;
  };

  # ---------------------------------------------------------------------------
  # Name resolution -- mirrors up.sh `install_host_entries` (up.sh:936-996).
  #
  # The host list is generated from vars.sh by the build script, so vars.sh stays
  # the single source of truth and the 22 names are never duplicated in Nix.
  #
  # Declaring them here also avoids up.sh's `sudo cp --remove-destination` hack
  # (up.sh:963-977), which breaks /etc/hosts out of the Nix store on immutable
  # distributions -- it names NixOS in its own comment.
  # ---------------------------------------------------------------------------
  networking.hosts."${minikubeIp}" = builtins.fromJSON loomHostsJson;

  networking.hostName = "loom";
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [
      80
      443
    ];
  };

  # ---------------------------------------------------------------------------
  # Toolchain -- every binary up.sh's `validate_environment` insists on
  # (up.sh:402-428). devenv is deliberately not used on the appliance: once we
  # are building a NixOS closure anyway, systemPackages carries the toolchain for
  # free, with no nix store pre-seeding and no direnv trust step.
  # ---------------------------------------------------------------------------
  environment.systemPackages =
    (with pkgs; [
      # `cp` `mkdir` `nproc` `df` `tee` `realpath`
      coreutils
      diffutils # `diff`
      gnugrep # `grep`
      procps # `sysctl` `pidwait` `pkill` -- pidwait needs procps-ng >= 4
      gawk # `awk`
      curl
      kubectl
      kubernetes-helm # `helm`
      minikube
      skaffold
      # Must be the kislyuk wrapper, NOT yq-go: up.sh:359 calls
      # `yq -y -s 'reduce .[] as $item ({}; . * $item)'`, which is jq syntax.
      yq

      # Not in up.sh's check list, but bring-up fails without them:
      git
      git-lfs # the embedded checkout configures filter.lfs.*
      gnutar # cicd/skaffold untars the vendored traefik chart
      gzip
      jq
      nano # up.sh:15 defaults EDITOR to nano

      # Field diagnosis on a box with no remote access.
      cryptsetup
      gptfdisk
      nvme-cli
      pciutils
      usbutils
      htop
      less
    ])
    ++ [
      loom-up
      loom-down
    ];

  virtualisation.docker = {
    enable = true;
    daemon.settings = {
      log-driver = "json-file";
      log-opts = {
        max-size = "100m";
        max-file = "3";
      };
      storage-driver = "overlay2";
    };
  };

  # ---------------------------------------------------------------------------
  # Operator account
  # ---------------------------------------------------------------------------
  users.mutableUsers = true;
  users.users.${loomUser} = {
    isNormalUser = true;
    description = "Loom operator";
    createHome = true;
    extraGroups = [
      "wheel"
      "docker"
    ];
  };
  # No direct root login; the appliance is reached through the operator account.
  users.users.root.hashedPassword = "!";

  security.sudo = {
    enable = true; # up.sh:406 requires `sudo` to exist
    # up.sh backgrounds `sudo minikube tunnel` for --expose (up.sh:924-933), and
    # the appliance starts Loom unattended, so this cannot prompt. Acceptable
    # only because the box has no sshd and is reachable from the console alone.
    wheelNeedsPassword = false;
  };

  # Appliance policy: no remote access at all.
  services.openssh.enable = false;

  # ---------------------------------------------------------------------------
  # Loom entry point
  # ---------------------------------------------------------------------------
  environment.sessionVariables = {
    # Mirrors devenv.nix:273,276 -- the layout every Loom code path is tested
    # against. Both directories are already in .gitignore, so the working tree
    # of the embedded checkout stays clean.
    MINIKUBE_HOME = "${loomRepoDir}/.minikube";
    SKAFFOLD_HOME = "${loomRepoDir}/.skaffold";
  };

  # ---------------------------------------------------------------------------
  # Console banner.
  #
  # These boxes are given away, and have no remote access, so the console is the
  # only place this information can reach anyone. The recovery passphrase is
  # written by the installer onto the encrypted root, which means reading it
  # already requires having booted -- which already requires the stick.
  # ---------------------------------------------------------------------------
  environment.interactiveShellInit = ''
    if [ -z "''${LOOM_BANNER_SHOWN:-}" ]; then
      export LOOM_BANNER_SHOWN=1
      printf '\n  Loom appliance -- %s\n' "${tag}"
      if [ -r /etc/loom/network.conf ]; then
        # shellcheck disable=SC1091
        . /etc/loom/network.conf
        printf '  Plug a laptop into %s and browse https://frontend.loom\n' \
          "''${LOOM_INTERFACE}"
        printf '  This box serves DHCP on %s and answers for *.loom\n' \
          "''${LOOM_SUBNET}"
      fi
      if [ -r ${recoveryPassphraseFile} ]; then
        printf '\n  LUKS recovery passphrase: %s\n' \
          "$(cat ${recoveryPassphraseFile})"
        printf '  Write it down. Without the USB stick it is the only way\n'
        printf '  to unlock this disk, and nobody else holds a copy.\n'
      fi
      printf '\n'
    fi
  '';

  # The installer writes the recovery passphrase here. wheel-readable so the
  # operator can see it without sudo; the disk it sits on is encrypted anyway.
  systemd.tmpfiles.rules = [
    "d /var/lib/loom 0750 root wheel -"
  ];

  system.stateVersion = "26.05";

  documentation.nixos.enable = false;
}
