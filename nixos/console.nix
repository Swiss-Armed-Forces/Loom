# What the operator meets at the appliance's console.
#
# The box has no remote access (box.nix, `services.openssh.enable = false`), so
# this screen is the entire user interface for whoever is standing in front of
# it. Three things happen here:
#
#   * The banner waits, and nothing logs itself in. agetty prints box.nix's
#     `loom-info` as the issue and then blocks on a keypress.
#   * A keypress opens a three-pane session: the live bring-up log, a shell and
#     btop. Both boot modes get the same session; only the unit in the first
#     pane differs, which is what `loom.progressUnit` carries over from
#     modes.nix.
#   * Nothing else writes to that screen. The units that used to log to
#     /dev/console -- which, with no `console=` on the command line, meant the
#     VT the operator is looking at -- log to the journal only now, and the
#     first pane is what shows them.
#
# Loom itself is still reached the way Documentation/appliance.md describes --
# a laptop on the appliance NIC, browsing https://frontend.loom. There is no
# browser on the box.
{
  config,
  lib,
  pkgs,
  loomUser,
  loomRepoDir,
  ...
}:
let
  cfg = config.loom;

  tmuxSocket = cfg.consoleSocket;

  tmuxConf = pkgs.writeText "loom.tmux.conf" ''
    # Panes are deliberately NOT login shells. tmux's default is `bash -l`,
    # which re-sources /etc/profile and would re-enter the hook at the bottom of
    # this file. A non-login shell still reads /etc/bashrc, so the prompt and
    # aliases survive, and PATH plus environment.sessionVariables are inherited
    # from the login shell that started the server.
    set -g default-command "${pkgs.bashInteractive}/bin/bash"

    # Do not shrink every pane to the smallest attached client. Without this a
    # second, smaller client -- a serial line at 80x24, say -- squeezes the
    # session the operator is actually looking at.
    set -g window-size largest

    set -g default-terminal "screen-256color"
    set -g history-limit 20000
    set -g mouse on
    set -g escape-time 10
    set -g main-pane-width 60%

    # The status line is the only place these key bindings are written down, and
    # the box ships no manual (documentation.nixos.enable = false in box.nix).
    set -g status-style "bg=colour24,fg=white"
    set -g status-left "  LOOM  "
    set -g status-right " Ctrl-b d detach | Alt-F2 plain console "
    set -g status-right-length 70
  '';

  # The first pane. Prints where the unit stands before following it, because a
  # bare `journalctl --follow` on a unit that has not started -- or that a
  # condition skipped -- is an empty screen with no explanation.
  loom-progress = pkgs.writeShellApplication {
    name = "loom-progress";
    runtimeInputs = with pkgs; [
      systemd
      coreutils
    ];
    text = ''
      unit=${lib.escapeShellArg cfg.progressUnit}

      printf '  Following %s. This pane is the live bring-up log.\n' "$unit"
      state="$(systemctl show --property=ActiveState --value "$unit" || echo unknown)"
      case "$state" in
        inactive)
          # Setup mode guards loom-fetch with ConditionPathExists, so on every
          # boot after the first the unit never runs at all.
          if [ -e ${lib.escapeShellArg "${loomRepoDir}/.loom-setup-complete"} ]; then
            printf '  First-time setup already completed. Reboot into the default\n'
            printf '  "Loom" boot entry to run offline. Below is the log of that run.\n'
          else
            printf '  %s has not started yet; output appears here when it does.\n' "$unit"
          fi
          ;;
        failed)
          printf '  %s FAILED. The end of its log is below.\n' "$unit"
          ;;
        *) ;;
      esac
      printf '\n'

      # Deliberately not --boot: in setup mode the run worth reading is usually
      # the previous boot's, because this boot skipped the unit.
      #
      # `exec` so that tmux's #{pane_current_command} reads `journalctl` rather
      # than `loom-progress` -- tests/appliance.nix asserts on it.
      exec journalctl --no-hostname --lines=500 --follow --unit "$unit"
    '';
  };

  # The third pane. btop refuses to draw anything but "Terminal size too small"
  # below a minimum that grows with the boxes it shows, and its stock set --
  # cpu, mem, net and proc -- needs 80x24. The pane it runs in is the lower half
  # of a column 40% of the screen wide (`main-pane-width 60%` below), so on
  # anything but a large monitor that minimum is simply not there, and the
  # operator gets a pane with nothing in it. Hence a box set chosen from the
  # pane's real size at startup:
  #
  #   80x24  cpu mem net proc   the full set
  #   60x18  cpu mem
  #   60x8   cpu                the smallest thing btop will draw
  #
  # `stty size` rather than `tput`, to keep the pane working on a VT whose TERM
  # has no terminfo entry on the box.
  loom-btop = pkgs.writeShellApplication {
    name = "loom-btop";
    runtimeInputs = with pkgs; [
      btop
      coreutils
    ];
    text = ''
      read -r lines cols < <(stty size 2>/dev/null || echo "24 80")

      if [ "$cols" -ge 80 ] && [ "$lines" -ge 24 ]; then
        boxes="cpu mem net proc"
      elif [ "$cols" -ge 60 ] && [ "$lines" -ge 18 ]; then
        boxes="cpu mem"
      else
        boxes="cpu"
      fi

      # A fixed path in the directory this module already creates, not a
      # mktemp: btop writes the whole config back when it exits, and one file
      # rewritten on every start leaves nothing behind to clean up.
      conf=${lib.escapeShellArg "${builtins.dirOf tmuxSocket}/btop.conf"}
      printf 'shown_boxes = "%s"\n' "$boxes" > "$conf"

      # --force-utf: a Linux VT with no locale set otherwise drops btop back to
      # ASCII box drawing. Spelled --utf-force before btop 1.4, where it is now
      # an unknown argument and btop exits non-zero.
      exec btop --force-utf --config "$conf"
    '';
  };

  loom-console = pkgs.writeShellApplication {
    name = "loom-console";
    runtimeInputs = with pkgs; [
      tmux
      coreutils
    ];
    text = ''
      # An array rather than a function, because the attach at the bottom is
      # `exec`ed: exec replaces the shell with an external program and cannot
      # run a shell function at all -- it fails with "tm: not found".
      tm=(tmux -S ${lib.escapeShellArg tmuxSocket} -f ${tmuxConf})

      create() {
        "''${tm[@]}" new-session -d -s loom -n loom ${lib.getExe loom-progress}
        "''${tm[@]}" split-window -h -t loom:0.0 -c ${lib.escapeShellArg loomRepoDir}
        "''${tm[@]}" split-window -v -t loom:0.1 ${lib.getExe loom-btop}
        "''${tm[@]}" select-layout -t loom:0 main-vertical
        # A dead log or btop pane keeps its error on screen instead of
        # collapsing the layout. The shell pane is left alone, so `exit` there
        # closes it the way anyone would expect.
        "''${tm[@]}" set-option -p -t loom:0.0 remain-on-exit on
        "''${tm[@]}" set-option -p -t loom:0.2 remain-on-exit on
        # Land in the shell, not in the log.
        "''${tm[@]}" select-pane -t loom:0.1
      }

      # `new-session -A` would be terser but cannot run the layout only on
      # creation. Two logins racing here is not worth a lock: `|| true` lets the
      # loser fall through to the attach below, which joins the winner's
      # session. If creation failed for a real reason the attach fails too, this
      # script exits non-zero, and the hook in console.nix hands the operator a
      # plain shell instead of looping.
      if ! "''${tm[@]}" has-session -t loom 2>/dev/null; then
        create || true
      fi

      exec "''${tm[@]}" attach-session -t loom
    '';
  };
in
{
  options.loom.consoleSocket = lib.mkOption {
    type = lib.types.str;
    default = "/run/loom/tmux.sock";
    readOnly = true;
    internal = true;
    description = ''
      The socket the operator's tmux session listens on.

      A fixed path rather than $XDG_RUNTIME_DIR: logind removes /run/user/<uid>
      when the operator's last session ends, which would kill the server -- and
      every pane with it -- on each detach. The alternative is
      `users.users.<loomUser>.linger`, one more moving part.
      `services.logind.settings.KillUserProcesses` defaults to false, so a
      server outside /run/user survives logout untouched.

      An option rather than a literal because key-guard.nix writes its removal
      warnings into this session, and a second copy of the path is a second
      thing to get wrong.
    '';
  };

  options.loom.progressUnit = lib.mkOption {
    type = lib.types.str;
    internal = true;
    description = ''
      The systemd unit whose live output fills the first pane of the operator's
      console session.

      Set by modes.nix, right next to the unit it names: `loom.service` in run
      mode, `loom-fetch.service` in setup mode. Declared here and set there for
      the same reason as `loom.toolchain` and `loom.entrypoints` -- the value
      belongs beside the thing it describes, so the two cannot drift.
    '';
  };

  config = {
    # -------------------------------------------------------------------------
    # Nothing logs in unattended.
    #
    # `--login-pause` makes agetty print the issue -- box.nix's banner -- then
    # `[press ENTER to login]`, then block on a single keypress before running
    # `login -f loom`. The operator types no username and no password, but the
    # box no longer opens a session for nobody at boot.
    #
    # `--autologin` is still what performs the login (agetty adds `-f <user>` to
    # the login command line for it), so PAM sees exactly what it saw before:
    # the account's locked shadow entry is bypassed the same way it always was.
    # Removing `autologinUser` instead would not produce a passwordless Enter --
    # agetty re-prompts on empty input and would simply demand the username.
    #
    # Both options apply to every getty, `serial-getty@` included; on NixOS
    # tty1's getty runs as `autovt@tty1.service`, an alias of the `getty@`
    # template, so per-instance overrides of `getty@tty1` are not consulted and
    # scoping these would not work anyway.
    # -------------------------------------------------------------------------
    services.getty.autologinUser = loomUser;
    services.getty.extraArgs = [ "--login-pause" ];
    # This box is a Loom appliance, not a NixOS installation, and the banner
    # from box.nix's loom-issue.service says so. Drops agetty's stock
    # `<<< Welcome to ... >>>` from /etc/issue.
    services.getty.greetingLine = "";

    # -------------------------------------------------------------------------
    # /dev/console
    #
    # The appliance named no console at all, so /dev/console was the active VT
    # and every `StandardOutput = "journal+console"` line from modes.nix and
    # network.nix landed on tty1 -- on top of the login prompt, and on top of
    # the session below. That is fixed where it belongs: those units log to the
    # journal only now, and the first pane follows them instead.
    #
    # There is deliberately NO `console=ttyN` here to go with it. Naming a VT on
    # the kernel command line does not merely redirect output to it, it makes
    # that VT the foreground console -- `console=tty12` leaves the box showing
    # the kernel log, with the banner and the press-a-key prompt rendered on a
    # tty1 nobody is looking at and nobody's keystrokes reach. The test asserts
    # `fgconsole` is 1 so this cannot come back.
    #
    # Deliberately in this shared module rather than in either mode: a
    # specialisation can only add to its parent's kernel command line, so a
    # `console=` set in one mode could never be taken back in the other.
    # -------------------------------------------------------------------------
    boot.kernelParams = lib.optionals cfg.platform.hasSerialConsole [
      # A serial line is not a VT, so this one is safe: it makes /dev/console
      # the serial port -- where that box's operator usually is -- without
      # touching which VT the monitor shows. It also gives the installed
      # appliance a serial getty it does not otherwise have, because
      # systemd-getty-generator only spawns serial-getty@ for consoles named on
      # the kernel command line. That getty is an escape hatch: console.nix
      # starts the session on tty1 alone.
      "console=ttyS0,115200"
      # plymouth renders a text fallback onto every console it finds; same
      # reason installer.nix passes this.
      "plymouth.ignore-serial-consoles"
    ];

    # -------------------------------------------------------------------------
    # The session
    # -------------------------------------------------------------------------
    systemd.tmpfiles.rules = [
      "d /run/loom 0700 ${loomUser} users -"
    ];

    environment.systemPackages = [
      loom-console
      loom-progress
      loom-btop
    ];

    # Only tty1. tty2-tty6 and any serial console deliberately get an ordinary
    # shell, so a session that will not start is never the only thing between
    # the operator and a prompt.
    environment.loginShellInit = ''
      if [ -z "''${LOOM_SESSION:-}" ] \
        && [ "$(id -un)" = ${lib.escapeShellArg loomUser} ] \
        && [ "$(tty)" = /dev/tty1 ]; then
        export LOOM_SESSION=1
        # agetty already printed the banner as the issue. Without this every
        # pane would print it again from box.nix's interactiveShellInit.
        export LOOM_BANNER_SHOWN=1

        # Deliberately not `exec`: a loom-console that died on startup would
        # take the login shell with it, agetty would respawn, and the operator
        # would be left in a loop with nowhere to type. Run it as a child and
        # only leave the shell when it actually worked.
        if ${lib.getExe loom-console}; then
          exit 0
        fi
        echo "[!] loom-console failed -- dropping to a plain shell." >&2
        unset LOOM_BANNER_SHOWN
      fi
    '';
  };
}
