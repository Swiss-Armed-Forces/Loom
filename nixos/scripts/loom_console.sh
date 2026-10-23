# shellcheck shell=bash
#
# The body of `loom-console`, which builds the operator's tmux session and
# attaches to it. nixos/console.nix reads this file into the
# writeShellApplication of the same name, behind a prologue of `LOOM_*`
# assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# Where the module used to splice whole shell fragments in with
# `lib.optionalString aiEnabled ''...''`, the condition is now
# `LOOM_AI_ENABLED` and the branches are plain `if`s below. Same two layouts,
# but the linter sees one program instead of three strings, and the branch a
# given image does not take is still checked.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly TMUX_SOCKET="${LOOM_TMUX_SOCKET:?nixos/console.nix must set this}"
readonly TMUX_CONF="${LOOM_TMUX_CONF:?nixos/console.nix must set this}"
readonly REPO_DIR="${LOOM_REPO_DIR:?nixos/console.nix must set this}"
readonly PANE="${LOOM_PANE:?nixos/console.nix must set this}"
readonly PROGRESS="${LOOM_PROGRESS:?nixos/console.nix must set this}"
readonly BTOP="${LOOM_BTOP:?nixos/console.nix must set this}"
readonly CONSOLE_MOUSE="${LOOM_CONSOLE_MOUSE:?nixos/console.nix must set this}"
# "true" on a platform that runs the AI services, "false" otherwise.
readonly AI_ENABLED="${LOOM_AI_ENABLED:?nixos/console.nix must set this}"
# Only meaningful when AI_ENABLED is true, so it is allowed to be empty.
readonly CHAT="${LOOM_CHAT-}"

# An array rather than a function, because the attach at the bottom is
# `exec`ed: exec replaces the shell with an external program and cannot
# run a shell function at all -- it fails with "tm: not found".
tm=(tmux -S "${TMUX_SOCKET}" -f "${TMUX_CONF}")

# The size of the VT this script was started on. The session below is
# created detached, and a detached session takes its window size from
# tmux's `default-size` -- 80x24 -- however big the console actually is.
# Panes split out of that are tiny, and loom-btop, which picks its box set
# from the pane it starts in, would measure around 39x11 and draw one box
# on a console with room for four. The attach at the bottom resizes the
# window afterwards, but by then btop has already written its config.
# Nothing else knows the real size: this script runs on the VT, so it asks
# the VT and hands the answer to `new-session`.
read -r lines cols < <(stty size 2> /dev/null || echo "24 80")

# The layout:
#
#   +---------------------+---------------------+
#   |  log, then k9s      |  btop               |   40%
#   +---------------------+---------------------+
#   |  the assistant, full width                |   60%
#   +-------------------------------------------+
#
# The assistant gets the full width because it is the only pane anyone
# types prose into, and a chat wrapped into half a console is unreadable.
# The two above it are glanced at rather than read: k9s wants rows more
# than columns, and btop picks a smaller box set when it has to.
#
# On a box whose platform declares `runsAiServices = false` there is no
# Ollama for the assistant to talk to, so the session is the top row alone,
# full height:
#
#   +---------------------+---------------------+
#   |  log, then k9s      |  btop               |  100%
#   +---------------------+---------------------+
#
# Panes are addressed by pane ID (`%0`, `%3`, ...) rather than by index.
# Indices follow layout POSITION and so are rewritten by every later split
# -- splitting the top-left pane renumbers the bottom pane from 1 to 2 --
# which makes any fixed `loom:0.N` in the middle of this function a bug
# waiting for the next edit. IDs are assigned once and never move.
# Every pane runs under loom-pane, which restarts its program when it
# exits. Quitting k9s with `:q` or btop with `q` is a keystroke away, and
# on a box whose console is the whole user interface a pane that stays
# dead until somebody finds the restart control is a bad trade.
supervise="${PANE}"

create() {
    local main mon chat
    # Guarded, because `create || true` below turns `errexit` off for the
    # whole of this function -- bash suppresses it for every command on the
    # left of `||`, function bodies included, so `writeShellApplication`'s
    # `set -e` is inert in here. A lost race therefore left `main` empty and
    # ran every line below with `-t ""`, which tmux resolves to the *current*
    # session, window and pane: the winner's. The loser then split, respawned
    # and set `@loom-main` inside the session the operator was looking at --
    # and usb-ingest/pane.py searches for that option. Reachable today:
    # vm-serial.nix runs `loom-console -d` from its own login hook at the
    # same time as tty1's.
    if ! main=$("${tm[@]}" new-session -d -x "${cols}" -y "${lines}" -s loom \
        -n loom -P -F '#{pane_id}' "${supervise}" "${PROGRESS}"); then
        return 1
    fi
    [[ -n "${main}" ]] || return 1

    if [[ "${AI_ENABLED}" == true ]]; then
        # -c so the assistant starts in the checkout: it is what an operator
        # asking about this box would want it looking at, and `respawn-pane`
        # below keeps a pane's start directory.
        chat=$("${tm[@]}" split-window -v -l 60% -t "${main}" \
            -c "${REPO_DIR}" -P -F '#{pane_id}')
    fi

    mon=$("${tm[@]}" split-window -h -t "${main}" -P -F '#{pane_id}')

    # Plain shells first, the real commands only once every split is done. A
    # split takes its space from the pane it came from, so a pane created
    # early is resized by each later one -- and both loom-chat and loom-btop
    # draw TUIs that measure their pane once at startup and cannot take that
    # back. Hence the respawns into panes that have stopped moving.
    if [[ "${AI_ENABLED}" == true ]]; then
        "${tm[@]}" respawn-pane -k -t "${chat}" "${supervise}" "${CHAT}"
    fi

    "${tm[@]}" respawn-pane -k -t "${mon}" "${supervise}" "${BTOP}"

    # The backstop under loom-pane rather than the first line of defence.
    # Anything the operator quits is restarted by the supervisor above and
    # never reaches this; what gets here is the supervisor itself dying,
    # which is not routine and should leave its error on screen rather than
    # collapse the layout. `× restart pane` in the status line is how it
    # comes back -- with the prefix switched off there is no
    # `:respawn-pane` to type.
    # Set after the respawns above, which would otherwise have to kill panes
    # that `remain-on-exit` is keeping around.
    #
    # Every pane, where it used to be two of three: the session no longer
    # contains a shell, so there is no pane left whose death is routine.
    "${tm[@]}" set-option -p -t "${main}" remain-on-exit on
    "${tm[@]}" set-option -p -t "${mon}" remain-on-exit on

    # How usb-ingest.nix finds the pane to split while a stick is being
    # copied: k9s stays in the top half and the copy is drawn underneath it.
    # A user option rather than an index, because indices follow layout
    # position and are rewritten by every split -- including that one. See
    # nixos/usb-ingest/loom_usb_ingest/pane.py.
    "${tm[@]}" set-option -p -t "${main}" @loom-main 1

    if [[ "${AI_ENABLED}" == true ]]; then
        "${tm[@]}" set-option -p -t "${chat}" remain-on-exit on
        # Land in the assistant, not in the log.
        "${tm[@]}" select-pane -t "${chat}"
    else
        # No assistant to land in, so land on the log -- which is the pane
        # that becomes k9s, and the one an operator watches on this box.
        "${tm[@]}" select-pane -t "${main}"
    fi
}

# `new-session -A` would be terser but cannot run the layout only on
# creation. Two logins racing here is not worth a lock: `|| true` lets the
# loser fall through to the attach below, which joins the winner's
# session. If creation failed for a real reason the attach fails too, this
# script exits non-zero, and the hook in console.nix hands the operator a
# plain shell instead of looping.
if ! "${tm[@]}" has-session -t loom 2> /dev/null; then
    create || true
fi

# "$@" so a caller can pick how it attaches without a second copy of any
# of the above. The only user today is vm-serial.nix, which passes `-d` to
# take the session away from tty1 rather than attach beside it and shrink
# the window for both -- see the reasoning there. tty1 itself passes
# nothing and is unaffected.
# Under the mouse shim, which is a pty between this VT and the tmux
# client (console-mouse.nix). A Linux console emits no mouse reports of
# its own -- console_codes(4) is explicit that they arrive "only when the
# virtual terminal driver receives a mouse update ioctl" from a user-mode
# program -- and gpm, despite being the program that page names, never
# issues that ioctl. So something has to stand in the stream and
# synthesise them, and being in the stream is also the only place the
# pointer can be drawn without leaving stale characters behind.
#
# `--` so the tmux command's own flags are never read as the shim's.
#
# Not conditional on `loom.consoleMouse.enable`, and not conditional on a
# mouse being plugged in: the shim `exec`s this very command unchanged
# whenever it cannot reach gpm, or when it is not on a VT at all -- which
# is the vm-serial.nix path, where the terminal on the far end does its
# own mouse reporting anyway. One code path, always exercised.
exec "${CONSOLE_MOUSE}" -- \
    "${tm[@]}" attach-session "${@}" -t loom
