# The appliance's optional debug access.
#
# Off unless the image was built with `build-appliance-image --debug`, in which
# case the box runs an SSH server that accepts exactly one key -- the one the
# build script generated for that image and left in a directory on the build
# host. Nothing else about the box changes the way in: there is still no
# password anywhere, and still no second account.
#
# This is the one flag that takes the appliance's central promise back. The
# threat model (Documentation/appliance.md) says "there is no remote access",
# box.nix says `services.openssh.enable = lib.mkDefault false` and
# loom_tests/appliance/banner.py asserts it on every VM test run. So an image
# built this way is not an appliance anybody may be handed, and it says so in
# five places that are hard to miss:
#
#   * the pre-login banner, in red, as the LAST thing on the screen -- see the
#     `warningLines` comment below for why the position is not cosmetic
#   * the boot menu entry's version line, via `system.nixos.tags`
#   * the message of the day, so an ssh session sees it on arrival
#   * the console session's status line (console.nix)
#   * the image filename (installer.nix)
#
# The two halves are gated differently, and the difference is deliberate:
#
#   * What the image IS -- the tags, the motd, the bundle -- follows the flag
#     into both boot modes. A debug stick booted into first-time-setup is still
#     a debug stick, and that mode holds the screen for hours.
#   * The way IN follows the flag only into run mode. First-time setup is a DHCP
#     client on whatever network somebody plugged it into (network.nix), which
#     is the worst place to open a port that hands out root, and it powers the
#     box off when it finishes. The installer stick never imports this module at
#     all; `appliance-vm installer --serial` is what reaches that half.
{
  config,
  lib,
  pkgs,
  loomUser,
  loomNamespace,
  debugAccess,
  debugSshAuthorizedKey,
  ...
}:
let
  cfg = config.loom;

  active = cfg.debug.enable && cfg.mode == "run";

  # Collect everything that explains a misbehaving box into one file, because
  # the interesting cases are the ones where reading it off a monitor is exactly
  # what nobody can do.
  #
  # Self-contained rather than a call into cicd/fetch_all_pod_logs.sh from the
  # embedded checkout: that script hardcodes its namespace and writes into
  # ./logs relative to wherever it was started, neither of which is right here.
  #
  # Nothing in it is allowed to fail the run. A box whose cluster never came up
  # is the single most likely thing to be debugging, and a bundle that aborted
  # on the first `kubectl` timeout would carry none of the journal that says
  # why. Hence `|| true` on every collector and a `set +e`-free structure: each
  # command's own output, including its error, lands in the file named after it.
  loom-debug-bundle = pkgs.writeShellApplication {
    name = "loom-debug-bundle";
    runtimeInputs = with pkgs; [
      coreutils
      gnutar
      gzip
      iproute2 # `ip addr`
      kubectl
      config.systemd.package # journalctl, systemctl
    ];
    text = ''
      stamp="$(date +%Y%m%dT%H%M%S)"
      out="/tmp/loom-debug-''${stamp}.tar.gz"
      dir="$(mktemp --directory)"
      trap 'rm --recursive --force "$dir"' EXIT
      root="$dir/loom-debug-''${stamp}"
      mkdir --parents "$root"

      echo "[*] Collecting. Nothing here is fatal -- a section that could not be"
      echo "[*] read is an empty file rather than a missing bundle."

      # --no-pager everywhere: this runs unattended over ssh as often as not,
      # and a pager waiting for a keypress on a closed stdout is a hang.
      journalctl --no-pager --boot >"$root/journal-this-boot.txt" 2>&1 || true
      # The previous boot as well, which is the only copy of why a box that is
      # now up went down. Absent on the first boot after an install; the
      # redirection captures journalctl saying so.
      journalctl --no-pager --boot=-1 >"$root/journal-previous-boot.txt" 2>&1 || true
      systemctl --no-pager list-units --all >"$root/units.txt" 2>&1 || true
      systemctl --no-pager list-units --failed >"$root/units-failed.txt" 2>&1 || true
      systemctl --no-pager status loom.service >"$root/loom-service.txt" 2>&1 || true

      # What the box is, as the box sees it -- against what platforms/<id>.nix
      # claimed. See the option below for why this is reached by store path.
      ${lib.getExe cfg.platformInfo} >"$root/platform-info.txt" 2>&1 || true

      # The login screen, verbatim. It carries the readiness line, the key
      # guard state and the recovery passphrase, so it answers three questions
      # at once -- and it is the one thing a remote session cannot look at.
      cp --recursive /run/issue.d "$root/issue.d" 2>/dev/null || true
      cat /etc/loom/network.conf >"$root/network.conf" 2>&1 || true
      ip addr >"$root/ip-addr.txt" 2>&1 || true

      # The cluster. Every one of these is a timeout waiting to happen on a box
      # where minikube never started, which is why they are last and why the
      # deadline is short.
      kube() { kubectl --request-timeout=20s "$@"; }
      kube get nodes -o wide >"$root/k8s-nodes.txt" 2>&1 || true
      kube get all --namespace ${lib.escapeShellArg loomNamespace} \
        >"$root/k8s-all.txt" 2>&1 || true
      kube describe pods --namespace ${lib.escapeShellArg loomNamespace} \
        >"$root/k8s-pods-describe.txt" 2>&1 || true
      kube get events --namespace ${lib.escapeShellArg loomNamespace} \
        --sort-by=.lastTimestamp >"$root/k8s-events.txt" 2>&1 || true

      mkdir --parents "$root/k8s-logs"
      # `|| true` on the listing too: with no cluster this prints nothing and
      # the loop body never runs, which is the correct outcome rather than an
      # error. --all-containers so an init container that is the actual problem
      # is not the one thing left out.
      for pod in $(kube get pods --namespace ${lib.escapeShellArg loomNamespace} \
        --output=name 2>/dev/null || true); do
        name="''${pod#pod/}"
        kube logs --namespace ${lib.escapeShellArg loomNamespace} \
          --tail=-1 --all-containers=true --prefix=true "$name" \
          >"$root/k8s-logs/''${name}.txt" 2>&1 || true
      done

      tar --create --gzip --file "$out" --directory "$dir" "loom-debug-''${stamp}"
      chmod 0600 "$out"

      echo "[*] Wrote $out"
      echo "[*] Pull it with: scp -F <the ssh_config the build printed> loom-appliance:$out ."
    '';
  };
in
{
  options.loom.debug = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = debugAccess;
      description = ''
        Run an SSH server keyed to the build's generated keypair, and mark the
        box as a debug build everywhere an operator looks. Set by
        `build-appliance-image --debug` and by `appliance-vm box --debug`; off
        in every other image, which is what keeps box.nix's
        `services.openssh.enable = lib.mkDefault false` in force.
      '';
    };

    authorizedKey = lib.mkOption {
      type = lib.types.str;
      default = debugSshAuthorizedKey;
      description = ''
        The single public key allowed in, in `authorized_keys` format.
        Generated per image by the build script, which keeps the private half
        in a directory on the build host and prints where.

        Only the public half ever reaches Nix, so unlike the WiFi passphrase
        next door there is no secret in /nix/store and none on the stick.
      '';
    };

    warningLines = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      readOnly = true;
      description = ''
        The warning, as plain ASCII lines, for everything that has to render it:
        box.nix's banner, the motd below and console.nix's status line.

        One definition rather than three copies, for the same reason `loom-info`
        generates the banner and the issue from one script -- and with a harder
        constraint than that one: these lines reach an agetty issue file, which
        means no backslash may appear anywhere in them. agetty reads a backslash
        as the start of an escape of its own and eats it before the screen sees
        it. No line is longer than 62 characters either, so the red block stays
        a rectangle on the narrowest console branding.nix's font produces.
      '';
      default = [
        "DEBUG IMAGE -- NEVER USE THIS IN PRODUCTION"
        ""
        "This box runs an SSH server. Anyone holding the key that"
        "was generated when this image was built has root on it,"
        "and Loom has no user management behind that."
        ""
        "Wipe it before it is handed to anybody."
      ];
    };
  };

  # Declared here and set in box.nix, the way `loom.bannerRefresh` is declared
  # in ready.nix and set there too: the package belongs beside the thing that
  # builds it, and the bundle above must not carry a second copy of a script
  # whose whole purpose is to report what this box actually is.
  options.loom.platformInfo = lib.mkOption {
    type = lib.types.package;
    internal = true;
    description = "The `loom-platform-info` command, as set by box.nix.";
  };

  config = lib.mkMerge [
    {
      assertions = [
        {
          assertion = cfg.debug.enable -> cfg.debug.authorizedKey != "";
          message =
            "nixos: --debug was given with no SSH public key. The box would run sshd with "
            + "an empty authorized_keys and nobody could get in, which is the worst of both "
            + "outcomes. build-appliance-image generates one; pass --argstr "
            + "debugSshAuthorizedKey '<key>' when driving nix by hand.";
        }
        {
          # A path is the mistake this catches: `--argstr debugSshAuthorizedKey
          # ~/.ssh/id_ed25519.pub` evaluates perfectly and produces a box whose
          # sshd rejects every connection, with no remote access to find out
          # why and no console message either.
          assertion =
            cfg.debug.enable
            ->
              builtins.match "(ssh-ed25519|ssh-rsa|ecdsa-sha2-[a-z0-9-]+|sk-[a-z0-9@.-]+) [A-Za-z0-9+/=]+.*" cfg.debug.authorizedKey
              != null;
          message =
            "nixos: debugSshAuthorizedKey does not look like an SSH public key: "
            + "'${cfg.debug.authorizedKey}'. Pass the contents of the .pub file, not its path.";
        }
      ];
    }

    # -------------------------------------------------------------------------
    # What this image IS -- both modes.
    #
    # Keyed on the flag rather than on `active`, unlike the access below. A
    # debug stick booted into first-time-setup is still a debug stick, and the
    # one screen it shows for the hours that fetch takes should say so. It is
    # also where `system.nixos.tags` has to be set for the specialisation to
    # inherit it: the run-mode entry and the first-time-setup entry both carry
    # `debug`, which is the whole point of putting it in the boot loader.
    # -------------------------------------------------------------------------
    (lib.mkIf cfg.debug.enable {
      # The marker that is visible before anything has booted at all, which on
      # a box whose problem is that it never reaches a login screen is the only
      # one there is.
      #
      # It lands in the boot entry's *version* line, not its title -- exactly
      # the asymmetry modes.nix records for `first-time-setup`. The title is
      # `distroName` plus the specialisation and nothing else
      # (systemd-boot-builder.py), so the menu still says `Loom`; what carries
      # the tag is `system.nixos.label`, which the version line beneath it
      # shows as `debug-<version>`, and the generation directory, which becomes
      # `nixos-system-loom-debug-<version>`.
      #
      # It merges with the specialisation's own `first-time-setup` tag rather
      # than replacing it, and `loom-promote-boot-entry` keys its glob on
      # `-specialisation-` rather than on tags, so neither is disturbed.
      system.nixos.tags = [ "debug" ];

      # What an ssh session sees on arrival: the one screen the operator
      # standing at the box never looks at.
      #
      # Written to /etc/motd and pointed at from `users.motdFile`, rather than
      # the more obvious `users.motd`. They are not the same thing: `users.motd`
      # renders the text to a *store path* and wires only `pam_motd` to it, and
      # pam_motd prints on an interactive login and nowhere else. So with that
      # option, `ssh box some-command` -- which is how an agent uses this port,
      # and how most of the diagnosis actually happens -- never sees a word of
      # it, and there is no file to `cat` either.
      #
      # This way there is one copy of the text, at the path everyone already
      # knows to look at, shown by pam on a human's login and readable by
      # anything else. The two options are mutually exclusive by assertion
      # upstream, so this cannot drift into two.
      environment.etc."motd".text = lib.concatStringsSep "\n" (
        [ "" ] ++ cfg.debug.warningLines ++ [ "" ]
      );
      users.motdFile = "/etc/motd";

      environment.systemPackages = [ loom-debug-bundle ];
    })

    # -------------------------------------------------------------------------
    # The way in, and the two behaviours that follow from it -- run mode only.
    #
    # First-time setup is a DHCP client on whatever network somebody plugged it
    # into (network.nix), which is the worst place to open a port that hands out
    # root. It also powers the box off when it finishes, so there would be
    # little to reach. The installer stick never imports this module at all.
    # -------------------------------------------------------------------------
    (lib.mkIf active {
      # -----------------------------------------------------------------------
      # The way in.
      # -----------------------------------------------------------------------
      services.openssh = {
        # Plain `true` against box.nix's `lib.mkDefault false`, rather than a
        # mkForce: the policy statement over there should stay readable as a
        # policy, and this should stay readable as the one exception to it.
        enable = true;

        # Already the NixOS default, and stated anyway because the failure it
        # prevents is unguessable: modern `scp` speaks the sftp protocol, so
        # without the subsystem, pulling a file off the box fails with a
        # "subsystem request failed" that reads like a network problem.
        allowSFTP = true;

        settings = {
          # The only account on the box, and the only one that needs to be. It
          # is in `wheel` with `wheelNeedsPassword = false` (box.nix), so this
          # key is root -- which is the same bargain the console already makes,
          # not a new one.
          AllowUsers = [ loomUser ];
          # Root's shadow entry is locked (box.nix), so this changes nothing
          # today. It is here so that unlocking root later cannot silently
          # open a second way in through this port.
          PermitRootLogin = "no";
          # The operator account has no password at all. Leaving password auth
          # on would not let anyone in -- PAM rejects an empty password -- but
          # it would leave sshd advertising a method that can never succeed,
          # and a bruteforcer filling the journal with attempts at it.
          PasswordAuthentication = false;
          KbdInteractiveAuthentication = false;
          # There is no X on this box at all (box.nix's comment on vim).
          X11Forwarding = false;
          # This port exists to be debugged through. When the question is "did
          # my key even reach it", the default LogLevel does not answer.
          LogLevel = "VERBOSE";
        };

        # Opens 22 in `networking.firewall.allowedTCPPorts`, globally rather
        # than on one interface, and that is the right shape here:
        #
        #   * In run mode the appliance segment is the only network the box has
        #     (network.nix), so "global" and "on loom0" are the same packets.
        #   * With --wifi the address moves off loom0 onto the bridge
        #     (wifi.nix), so an interface-scoped rule would silently exclude
        #     every client that joined over the air.
        #   * vm.nix forces `networking.interfaces` empty, so loom0 never
        #     materialises in `appliance-vm box` -- an interface-scoped rule
        #     would make the VM, which is the cheapest way to use this feature
        #     at all, the one place it does not work.
        openFirewall = true;
      };

      users.users.${loomUser}.openssh.authorizedKeys.keys = [ cfg.debug.authorizedKey ];

      # Never power the box off under somebody who is debugging it.
      #
      # modes.nix sets `poweroff` for run mode and explains why: a box holding
      # indexed data is expected to be left alone, so pulling the key is a
      # deliberate act. On a debug box it is far more likely to be a glitching
      # port on a bench, and losing the session -- and the reproduction -- to
      # that is the failure worth avoiding here. mkForce because modes.nix
      # states the safe default plainly, and it should go on doing so.
      loom.keyGuard.action = lib.mkForce "warn";

      # No splash. modes.nix drops `quiet` and `udev.log_level=3` for a debug
      # build (they cannot be subtracted later, so that has to happen at the
      # definition site), and this takes plymouth off the same screen -- the
      # same pair setup mode uses, for the same reason: a still logo over a
      # boot that is going wrong is actively misleading.
      boot.kernelParams = [ "plymouth.enable=0" ];
    })
  ];
}
