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

  # The console banner, as a command. Everything it prints is also what the
  # login screen shows: `loom-issue.service` below captures this output into
  # /run/issue.d, and the interactive shell calls it again on login. One
  # generator rather than two copies that drift -- and the operator can re-run
  # it by hand once the bring-up log has scrolled the boot-time copy away.
  #
  # Produces no backslashes on purpose: agetty interprets them as issue-file
  # escapes. The passphrase charset (install.sh:225-231) cannot contain one.
  loom-info = pkgs.writeShellApplication {
    name = "loom-info";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      printf '\n  Loom appliance -- %s\n' ${lib.escapeShellArg tag}
      printf '  %s\n' ${lib.escapeShellArg config.loom.platform.description}
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
  # Toolchain -- every binary up.sh needs, in one list.
  #
  # `validate_environment` checks most of them (up.sh:402-428), but not all: it
  # pipes through `awk` at up.sh:380, *above* its own checks, and `cicd/skaffold`
  # reaches for `tar` and `mktemp`. So this list is wider than the check list.
  #
  # It is deliberately a shared option rather than a literal here, because the
  # units in modes.nix need exactly the same set on their PATH and a unit's PATH
  # has nothing to do with systemPackages -- `/run/current-system/sw/bin` is
  # never on it. The two used to be maintained separately and drifted, which
  # shipped a box whose loom.service died on `awk: command not found`.
  #
  # devenv is deliberately not used on the appliance: once we are building a
  # NixOS closure anyway, this carries the toolchain for free, with no nix store
  # pre-seeding and no direnv trust step.
  # ---------------------------------------------------------------------------
  loom.toolchain = with pkgs; [
    bash # `sh` (up.sh:415, and `sudo sh -c` at up.sh:927)
    # `cp` `mkdir` `nproc` `df` `tee` `realpath` `mktemp`
    coreutils
    diffutils # `diff`
    gnugrep # `grep`
    procps # `sysctl` `pidwait` `pkill` -- pidwait needs procps-ng >= 4
    gawk # `awk`
    curl # also `is_offline` (up.sh:216-221), which runs every invocation
    util-linux
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
    jq # the kislyuk `yq` shells out to it
  ];

  environment.systemPackages =
    config.loom.toolchain
    ++ (with pkgs; [
      nano # up.sh:15 defaults EDITOR to nano

      # Field diagnosis on a box with no remote access. Interactive only -- a
      # unit has no use for any of these, so they stay out of `loom.toolchain`.
      cryptsetup
      gptfdisk
      nvme-cli
      pciutils
      usbutils
      htop
      less
    ])
    ++ [ loom-info ]
    ++ config.loom.entrypoints;

  # Also handed to the units in modes.nix, which need them on their PATH rather
  # than merely in the operator's shell.
  loom.entrypoints = [
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

  # The operator account has no password, so the console logs into it directly.
  # A password would buy nothing: `wheelNeedsPassword = false` below already
  # hands out root without one, there is no sshd, and the disk is LUKS-encrypted
  # with the key on the USB stick -- physical possession is the whole trust
  # boundary. Without this the login prompt is unanswerable, because a user with
  # no declared password gets a locked shadow entry and `users.mutableUsers` is
  # true, which switches off the assertion that would otherwise catch it.
  services.getty.autologinUser = loomUser;
  # This box is a Loom appliance, not a NixOS installation, and the banner from
  # loom-issue.service below says so. Drops agetty's stock
  # `<<< Welcome to NixOS ... >>>` from /etc/issue.
  services.getty.greetingLine = "";

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
  # only place this information can reach anyone. It is therefore shown before
  # anyone logs in, as the agetty issue, and again in the operator's shell.
  #
  # The recovery passphrase is part of it, which is safe here for the same
  # reason the file itself is: reading it requires the box to have booted, which
  # requires the stick -- and the console hands out a root-capable shell without
  # a password anyway, so the issue exposes nothing the VT did not already.
  # ---------------------------------------------------------------------------

  # /run rather than /etc: the issue is regenerated on every boot, and 26.05 may
  # mount /etc read-only through the etc overlay. NixOS points agetty at
  # `/etc/issue:/etc/issue.d:/run/issue:/run/issue.d` (getty.nix:13-18), and
  # util-linux 2.42 reads every one of them.
  #
  # getty-pre.target is the ordering hook for exactly this, but it is a passive
  # target: systemd.special(7) requires its users to pull it into the boot
  # transaction themselves. Hence `wants` as well as `before` -- and
  # `wantedBy = multi-user.target`, because being wanted *by* a target that
  # nothing starts would leave this unit unreachable and the banner missing.
  # getty@tty1 and serial-getty@ are both After=getty-pre.target upstream, so
  # this lands before any of them render the issue.
  systemd.services.loom-issue = {
    description = "Loom console banner for the login screen";
    wantedBy = [ "multi-user.target" ];
    wants = [ "getty-pre.target" ];
    before = [ "getty-pre.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = pkgs.writeShellScript "loom-write-issue" ''
        set -euo pipefail
        ${pkgs.coreutils}/bin/mkdir -p /run/issue.d
        # Rendered through a temporary file so agetty can never read a
        # half-written banner from a getty that respawns mid-write.
        ${loom-info}/bin/loom-info >/run/issue.d/50-loom.issue.tmp
        ${pkgs.coreutils}/bin/mv /run/issue.d/50-loom.issue.tmp \
          /run/issue.d/50-loom.issue
      '';
    };
  };

  # Repeated in the shell because the boot-time copy scrolls away behind
  # loom.service's console output. `loom-info` reprints it on demand.
  environment.interactiveShellInit = ''
    if [ -z "''${LOOM_BANNER_SHOWN:-}" ]; then
      export LOOM_BANNER_SHOWN=1
      ${loom-info}/bin/loom-info
    fi
  '';

  # The installer writes the recovery passphrase here. wheel-readable so the
  # operator can see it without sudo; the disk it sits on is encrypted anyway.
  systemd.tmpfiles.rules = [
    "d /var/lib/loom 0750 root wheel -"
  ];

  # Names the systemd-boot entries. NixOS builds each entry's title from this
  # string plus the specialisation name, so the two modes read `Loom` and
  # `Loom (setup)` rather than `NixOS` and `NixOS (setup)` -- which is what
  # Documentation/appliance.md tells the operator to look for on first boot.
  # It also sets NAME/PRETTY_NAME in /etc/os-release; `system.nixos.distroId`
  # is untouched, so anything matching on `ID=nixos` still works.
  system.nixos.distroName = "Loom";

  system.stateVersion = "26.05";

  documentation.nixos.enable = false;
}
