# A serial getty on ttyS0, so that a virtualised appliance can be reached from
# a terminal that does copy and paste.
#
# Never part of a stick anyone flashes. nixos/default.nix imports this into the
# `boxVm` target unconditionally and into `installerImage` only when
# `vmSerialGetty` is set, which nothing but `appliance-vm installer --serial`
# does -- and that path refuses to flash what it built.
#
# What this deliberately does NOT do is set `console=`. console.nix rejects that
# in as many words: naming a serial port there makes it the *primary* console,
# so a panic on a box with nothing plugged into the port goes nowhere at all
# instead of onto the monitor somebody is standing in front of. The test asserts
# `fgconsole` is 1 (tests/appliance.nix) so it cannot come back.
#
# A getty is not a console, which is the whole reason this is safe: tty1 stays
# the foreground VT, the installer menu keeps the `TTYPath = /dev/tty1` that
# installer.nix gives it, and the serial line is a second way in rather than a
# replacement for the first.
{
  config,
  lib,
  loomUser,
  ...
}:
{
  # systemd's getty generator instantiates this template only for whatever
  # `console=` names, and nothing here names ttyS0 -- see above. So the instance
  # has to be wanted explicitly.
  systemd.services."serial-getty@ttyS0" = {
    enable = true;
    overrideStrategy = "asDropin";
    wantedBy = [ "getty.target" ];

    # Carried across by hand, and this is the whole reason this file is more
    # than three lines.
    #
    # systemd collects drop-ins by BASENAME, and every drop-in NixOS generates
    # is called `overrides.conf`. The instance directory outranks the template
    # directory, so this unit's `serial-getty@ttyS0.service.d/overrides.conf`
    # does not merge with nixpkgs' `serial-getty@.service.d/overrides.conf` --
    # it replaces it outright. What that file carried, and what therefore
    # vanishes, is the only ExecStart that works:
    #
    #   ExecStart=/nix/store/.../agetty --login-program .../login
    #             --issue-file ... --autologin loom --login-pause %I
    #             --keep-baud $TERM
    #
    # Left masked, the unit falls back to the upstream unit's own
    # `ExecStart=-/sbin/agetty`, which on NixOS resolves to nothing:
    #
    #   (agetty)[825]: Unable to locate executable '/usr/bin/agetty'
    #
    # agetty exits at once, systemd restarts it about eight times, the start
    # limit stops the unit for good, and by the time anybody attaches there is
    # nothing on the port -- with no trace of why outside the guest's journal.
    #
    # Read off the template rather than rebuilt here, so `services.getty.*` stays
    # the one place the appliance's agetty arguments are decided: console.nix
    # sets `--login-pause` and `autologinUser` there for tty1, and the serial
    # line must behave the same way or it is not the same box.
    inherit (config.systemd.services."serial-getty@")
      restartIfChanged
      ;
    serviceConfig.ExecStart = config.systemd.services."serial-getty@".serviceConfig.ExecStart;

    # The upstream unit says `vt220`, which is enough for a shell and not enough
    # for the session below: tmux falls back to ASCII line drawing and eight
    # colours, and btop's own `--force-utf` cannot fix the frame tmux drew
    # around it. `ncurses` is in `environment.defaultPackages`, so the terminfo
    # entry for this is already on the box and costs nothing to name. The
    # ExecStart above ends in `$TERM`, which is where this lands.
    environment.TERM = "xterm-256color";
  };

  # tty1 gets the console session from console.nix, which gates on `$(tty)`
  # precisely so that tty2-tty6 stay ordinary shells. The serial line is a third
  # case: it should land in the same session, and it should be the only client
  # attached to it.
  #
  # Hence `-d`. tmux sizes a window to its *smallest* attached client, so an
  # 80x24 serial client would shrink the layout on the monitor as well -- and
  # `loom-btop` has already chosen its box set from the size of the pane it
  # started in (console.nix), so what both clients would then be looking at is a
  # layout no operator ever sees. Detaching the other client instead leaves one
  # client, one size, and the panes as they were drawn.
  #
  # The cost is a ping-pong: pressing ENTER on tty1 takes the session back and
  # drops the serial client, which then has to reconnect. That is the right way
  # round -- whoever is physically at the box wins the screen.
  environment.loginShellInit = ''
    if [ -z "''${LOOM_SESSION:-}" ] \
      && [ "$(id -un)" = ${lib.escapeShellArg loomUser} ] \
      && [ "$(tty)" = /dev/ttyS0 ]; then
      export LOOM_SESSION=1

      # Ask the terminal how big it is, because the serial line cannot say.
      #
      # A VT gets its size from the kernel and a pty from TIOCSWINSZ, but a
      # serial port carries neither, so agetty falls back to 80x24 and no
      # SIGWINCH ever arrives. tmux then splits that into panes of about 39x23,
      # which is below the 60x8 loom-btop needs for even its smallest box set --
      # so the monitoring pane comes up saying "Terminal size too small" instead
      # of drawing anything.
      #
      # This is what xterm's `resize` does, in the four lines of it that matter:
      # park the cursor past the bottom right, where it can only stop at the
      # real edge, and ask where it ended up.
      #
      # The terminal has to be out of canonical mode for this, which is the part
      # that is easy to leave out: the reply carries no newline, so a line
      # discipline that buffers by line never hands it over and the read waits
      # for the full timeout every single login. `min 0 time 20` also bounds the
      # read in the driver -- 2 seconds -- so a terminal that does not answer
      # cannot wedge the login either way.
      loom_rows=""
      loom_cols=""
      loom_stty="$(stty -g 2>/dev/null || true)"
      if [ -n "''${loom_stty}" ]; then
        stty -icanon -echo min 0 time 20 2>/dev/null || true
        printf '\e7\e[9999;9999H\e[6n\e8'
        IFS='[;' read -r -d R _ loom_rows loom_cols 2>/dev/null || true
        stty "''${loom_stty}" 2>/dev/null || true
      fi
      case "''${loom_rows}x''${loom_cols}" in
        *[!0-9x]* | x* | *x) : ;;
        *) stty rows "''${loom_rows}" cols "''${loom_cols}" 2>/dev/null || true ;;
      esac
      unset loom_stty loom_rows loom_cols

      # Not `exec`, for the reason console.nix gives at the same place: a
      # loom-console that died on startup would take the login shell with it,
      # agetty would respawn, and there would be nowhere left to type.
      if loom-console -d; then
        exit 0
      fi
      echo "[!] loom-console failed -- dropping to a plain shell." >&2
    fi
  '';
}
