# shellcheck shell=bash
#
# The body of `environment.loginShellInit` on a `--vm-serial` image: the
# operator logging in on ttyS0 gets the console session, after the terminal
# has been asked how big it is. nixos/vm-serial.nix reads this file in behind
# a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, because `loginShellInit` is
# linted by nothing at all -- it is a fragment pasted into /etc/profile, and
# nothing in the image build looks at it.
#
# No `set` line, and that is deliberate rather than an omission: this runs
# inside the operator's login shell, so `set -e` here would make any failing
# command log them straight back out. The linter is told the dialect by the
# directive on the first line and reads the fragment as it runs.
#
# Read as bash, which is what it is: NixOS interpolates this into
# /etc/profile and the size probe below uses `read -d`, a bash extension that
# no POSIX shell has.

if [[ -z "${LOOM_SESSION:-}" ]] \
    && [[ "$(id -un)" == "${LOOM_USER:?nixos/vm-serial.nix must set this}" ]] \
    && [[ "$(tty)" == /dev/ttyS0 ]]; then
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
    loom_stty="$(stty -g 2> /dev/null || true)"
    if [[ -n "${loom_stty}" ]]; then
        stty -icanon -echo min 0 time 20 2> /dev/null || true
        printf '\e7\e[9999;9999H\e[6n\e8'
        IFS='[;' read -r -dR _ loom_rows loom_cols 2> /dev/null || true
        stty "${loom_stty}" 2> /dev/null || true
    fi
    case "${loom_rows}x${loom_cols}" in
        *[!0-9x]* | x* | *x) : ;;
        *) stty rows "${loom_rows}" cols "${loom_cols}" 2> /dev/null || true ;;
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
