# What the operator meets at the appliance's console.
#
# The box has no remote access (box.nix, `services.openssh.enable = false`), so
# this screen is the entire user interface for whoever is standing in front of
# it. Three things happen here:
#
#   * The banner waits, and nothing logs itself in. agetty prints box.nix's
#     `loom-info` as the issue and then blocks on a keypress.
#   * A keypress opens a three-pane session: the bring-up log and btop side by
#     side along the top, an assistant full width underneath them. The log pane
#     does not stay a log -- once Loom is up it hands over to k9s on the pods,
#     because by then the log is a finished transcript and the pods are the live
#     thing. Both boot modes get the same session; only the unit in that pane
#     differs, which is what `loom.progressUnit` carries over from modes.nix.
#   * A readiness bar is pinned along the bottom of that log pane, and a segment
#     of the status line carries the same answer for the life of the session --
#     which is what is left once the pane becomes k9s and the bar goes with it.
#     ready.nix owns both; what belongs here is the pane's wrapper and the
#     status-left format below.
#   * A fourth pane appears while a USB stick is being copied in, splitting the
#     k9s pane in half and drawing the progress of the copy underneath it. It
#     goes away again when the last stick is unplugged, and k9s has the space
#     back. usb-ingest.nix owns it; what belongs here is the mark on the pane it
#     splits (`@loom-main`, below).
#   * None of those panes is a shell. The middle column is opencode pointed at
#     the cluster's own Ollama -- the box already carries a model, and nothing
#     on the console could reach it. A prompt is Alt-F2 away, on the tty2-tty6
#     gettys this module leaves alone, and the status line says so.
#   * Nothing else writes to that screen. The units log to the journal only --
#     /dev/console, with `console=tty0`, is the VT the operator is looking at --
#     and the first pane is what shows them.
#   * It is driven with a mouse as well as a keyboard, on a console that has no
#     mouse driver behind it. That takes a daemon and a pty shim, both of which
#     live in console-mouse.nix; what belongs here is the other half -- the tmux
#     side. `mouse on` is load-bearing on tty1. The prefix is switched off,
#     since navigation is by clicking, and the two things the prefix would
#     otherwise be needed for -- detach and respawning a dead pane -- are
#     clickable regions in the status line.
#     None of that is a security boundary; see nixos/README.md.
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
  loomNamespace,
  loomChatModel,
  loomHostsJson,
  ...
}:
let
  cfg = config.loom;

  tmuxSocket = cfg.consoleSocket;

  # Whether this box deploys Ollama at all. False on a platform that has not got
  # the memory for it (platforms/nuc12.nix), and then the assistant pane has
  # nothing to dial: modes.nix passes `--disable-ai`, so there is no ollama
  # Service and no ingress behind `ollama.loom`. The session drops to the top row
  # rather than shipping a pane that can only ever print a connection error.
  #
  # It also takes `opencode` out of the closure entirely -- see box.nix -- which
  # is the honest thing to do on an image that cannot use it.
  aiEnabled = cfg.platform.runsAiServices;

  # Whether anything on this box publishes readiness for the pane and the status line to
  # draw. False in setup mode, where ready.nix deploys no publisher because there is no
  # cluster to ask about -- and both readers are built to say nothing at all in that case
  # rather than to show an empty bar.
  readinessPublished = cfg.ready.enable && cfg.mode == "run";

  # The status line's readiness segment, or nothing. Built here rather than inline so the
  # status-left assignment below stays one line with one meaning, whichever mode this is.
  readinessSegment = lib.optionalString readinessPublished (
    "#(${lib.getExe cfg.ready.package} --oneline --state-dir ${cfg.ready.stateDir})  "
  );

  # On a --debug box, the one thing the session must not let anyone forget.
  #
  # The pre-login banner says it at length (box.nix), and the console session is
  # precisely what draws over that banner -- so without this the marker is gone
  # from the moment somebody presses a key, on the screen they then spend all
  # their time looking at. Short, because it shares `status-left-length` with
  # the readiness segment; red, because it is the same signal as a degraded
  # cluster and should read the same way from across a room.
  #
  # A literal rather than a `#()`, so it costs the tmux server nothing per tick
  # and cannot be wrong about the box it is running on.
  #
  # One wording, and it is true in both modes: debug.nix gates
  # `services.openssh` on `loom.debug.enable` alone, so first-time setup runs
  # the sshd too. The marker has to keep following that gate, since the mode
  # that holds the screen for hours is the one an operator actually reads and
  # the one place it must not say something false.
  debugText = "DEBUG -- SSH OPEN";
  debugSegment = lib.optionalString cfg.debug.enable "#[fg=red,bold]${debugText}#[default]  ";

  # What `loom-ready --oneline` can produce, markup included. The longest stage
  # word is `rolling-out` (11), the counts are `NNN/NNN pods` with a colour pair
  # around them, and `text.py` caps the note it appends. 72 is that measured at
  # its widest -- `degraded 91` with markup -- rounded up, and it is a budget
  # rather than a promise: anything shorter simply does not use it.
  readinessBudget = 72;

  # 8 for `"  LOOM  "`, plus the two optional segments. Computed rather than
  # written out, because the thing being budgeted for is invisible: the trim
  # happens before `#[...]` is parsed, so every escape in here counts against it.
  statusLeftLength =
    8 + builtins.stringLength debugSegment + (if readinessPublished then readinessBudget else 0);

  # Taken from the host list rather than written out again, so the name the chat
  # pane dials is by construction one of the names box.nix pins in /etc/hosts.
  # Spelling it "ollama.loom" here instead would be a second copy of the domain,
  # and a box built with a different one would get a pane that cannot resolve.
  ollamaHost = lib.findFirst (h: lib.hasPrefix "ollama." h) "ollama.loom" (
    builtins.fromJSON loomHostsJson
  );

  # The ingress, or the loopback proxy in front of it on a mutual TLS box. See
  # the option's description at the bottom of this file.
  ollamaBaseUrl = config.loom.assistant.ollamaBaseUrl;

  tmuxConf = pkgs.writeText "loom.tmux.conf" ''
    # Panes are deliberately NOT login shells. tmux's default is `bash -l`,
    # which re-sources /etc/profile and would re-enter the hook at the bottom of
    # this file. A non-login shell still reads /etc/bashrc, so the prompt and
    # aliases survive, and PATH plus environment.sessionVariables are inherited
    # from the login shell that started the server.
    set -g default-command "${pkgs.bashInteractive}/bin/bash"

    # Do not shrink every pane to the smallest attached client. Without this a
    # second, smaller client -- someone attaching from tty2 at 80x25, say --
    # squeezes the session the operator is actually looking at, and takes btop
    # below the size it will draw at (loom-btop below).
    set -g window-size largest

    set -g default-terminal "screen-256color"
    set -g history-limit 20000
    # Load-bearing on tty1 as well as over serial. The shim
    # (console-mouse.nix) is the tmux client's terminal and speaks SGR into it,
    # and this is what makes tmux ask for mouse reporting and then route what
    # arrives: focus the pane under the click, translate to pane-relative
    # coordinates, re-encode in whatever protocol each pane asked for, drag
    # borders, scroll. None of that is reimplemented anywhere in this module.
    set -g mouse on
    set -g escape-time 10

    # How long a `display-message` line stays in the status bar, against a default
    # of 750ms -- which is not a message, it is a flicker.
    #
    # Everything that writes here is the box talking to whoever is standing in
    # front of it, and there is nowhere else for it to land: key-guard.nix says the
    # LUKS key has been pulled and the box is about to power off, usb-ingest.nix
    # says a stick has started copying, that a volume is done, or that the disk is
    # nearly full. Those also go to `wall`, which reaches a tty somebody has logged
    # into -- and the tmux client redraws over it a moment later. So this line is
    # the one that is actually read.
    #
    # Eight seconds is a compromise: long enough for a line of prose at a walk-up
    # pace, short enough that a stale notice is not still on screen when the next
    # one arrives. Progress that has to persist belongs in the ingest pane, not
    # here (loom_usb_ingest/watch.py).
    set -g display-time 8000
    # No `main-pane-width`/`select-layout` here: the layout is built by hand in
    # `create` below, because none of tmux's five preset layouts puts the main
    # pane at the BOTTOM -- `main-horizontal` puts it on top -- and the widest
    # pane is the one the operator types into.

    # -------------------------------------------------------------------------
    # No keyboard route into tmux's own command interface.
    #
    # `prefix None` is the instrument, and the choice of instrument matters:
    # `unbind-key -a` would ALSO remove the root key table, and every mouse
    # behaviour tmux has lives in there as an ordinary binding --
    # `MouseDown1Pane { select-pane -t=; send -M }` is literally
    # click-to-focus and forward-into-pane (tmux's key-bindings.c). Unbinding
    # everything would silently destroy the feature this module exists to add.
    # Setting the prefix to None takes out the prefix table and nothing else.
    #
    # This is interaction design, not a security boundary, and nothing here
    # should be mistaken for one: every getty autologins the operator,
    # `wheelNeedsPassword` is false (box.nix), and Alt-F2 reaches a shell that
    # can run `tmux -S ${tmuxSocket}` against this very server.
    # -------------------------------------------------------------------------
    set -g prefix None
    set -g prefix2 None

    # Right-click is a command interface, and an unusually generous one:
    # tmux's default MouseDown3 bindings open `display-menu` with Kill,
    # Respawn, Horizontal/Vertical Split, New Window, New Session and a
    # `command-prompt` for rename. The pane binding only shows that menu for a
    # pane that has NOT asked for mouse reporting -- so on this box it would
    # surface on a dead pane, which is exactly when an operator is most likely
    # to be clicking around. The status ones show it always.
    unbind -n MouseDown3Pane
    unbind -n M-MouseDown3Pane
    unbind -n MouseDown3Status
    unbind -n M-MouseDown3Status
    unbind -n MouseDown3StatusLeft
    unbind -n M-MouseDown3StatusLeft

    # -------------------------------------------------------------------------
    # The status line, which is the only user interface tmux itself has.
    #
    # `#[range=user|X]` marks a clickable region; clicking it fires the
    # `Status` mouse key -- NOT `StatusRight`, however far right it is drawn --
    # with X in `#{mouse_status_range}`. That is the whole mechanism.
    #
    # The glyph is U+00D7, and it is chosen rather than picked. The console
    # font is Cozette's 515-glyph PSF (branding.nix), which has none of the
    # symbols anyone would reach for first -- no U+23FB power sign, no U+2716
    # cross, no U+25CF disc -- and a missing glyph renders as a hole on a
    # screen nobody sees until the box is at a site. branding.nix asserts this
    # codepoint at build time alongside the three the mark is drawn from.
    #
    # `status-right-length` is generous because the `#[...]` markup counts
    # toward it: status-format[0] trims with `#{T;=/#{status-right-length}:...}`
    # before the markup is parsed, so a tight budget cuts a range directive in
    # half and the button stops being clickable rather than looking wrong.
    #
    # Alt-F2 is named here: no pane of this session is a shell, so it is the
    # only route to a prompt -- and with the prefix off it is also the backstop
    # for anything this status line cannot do.
    # -------------------------------------------------------------------------
    set -g status-style "bg=colour24,fg=white"
    # -------------------------------------------------------------------------
    # Readiness, next to the name, for as long as the session lives.
    #
    # The pane's bar is gone the moment that pane becomes k9s, and that is the
    # right trade -- the pod list is what an operator wants once up.sh has
    # returned. What it leaves out is anything saying whether the box ever
    # finished coming up, or whether it stopped being up on a Tuesday. This is
    # that, and it costs a row nothing else was using.
    #
    # Three things about it are load-bearing:
    #
    #   * A file read, never a `kubectl`. This runs from the tmux server on a
    #     timer, and a command here that can block on a cluster that is not
    #     answering is a session that can freeze. ready.nix's unit does the
    #     asking; this only ever opens a file, and prints nothing at all when
    #     there is not a fresh one.
    #   * `#()` output is re-expanded by tmux, which is why loom_ready/text.py
    #     guarantees the segment carries no `#` of its own -- a stray one would
    #     be read as the start of a format directive. The styles it does emit
    #     are re-expanded on purpose: green for up, red for degraded, which is
    #     the fastest thing on this screen to read from across a room.
    #   * `status-left-length` defaults to TEN characters, which is two more
    #     than "  LOOM  " and would silently cut the segment off entirely.
    #
    # `status-interval` is set rather than left at its default of 15 for the
    # same reason: the bar in the pane refreshes four times a second, and a
    # segment beside it running a quarter of a minute behind reads as a bug in
    # one of the two.
    #
    # Both are empty in setup mode -- see `readinessPublished`.
    # -------------------------------------------------------------------------
    ${lib.optionalString readinessPublished "set -g status-interval 5"}
    # Counted, not estimated. `status-format[0]` trims with
    # `#{T;=/#{status-left-length}:...}` *before* the markup is parsed -- this
    # file says so about `status-right-length` a few lines up -- so the budget has
    # to cover the `#[fg=red,bold]` and `#[default]` sequences too. A budget that
    # counts only the visible characters cuts inside the segment's trailing
    # `#[default]`, and the line renders half-complete (`...degraded 24/2`) on the
    # box where the status line is the only persistent indicator.
    #
    # `"  LOOM  "` is 8, the readiness segment is at most
    # `${toString readinessBudget}` including its two trailing spaces, and the
    # debug marker carries ${toString (builtins.stringLength debugSegment)}
    # characters of text and markup on a --debug box. Conditional, so an image
    # built without the flag budgets for neither.
    set -g status-left-length ${toString statusLeftLength}
    set -g status-left "  LOOM  ${debugSegment}${readinessSegment}"
    # The two controls are last, so they sit flush against the right-hand edge
    # of the screen. That is deliberate on two counts: a target in the corner
    # of the display is the easiest one there is to hit with a mouse, and it
    # gives the VM test a position it can reach by slamming the pointer into
    # the corner rather than by calibrating its way to a cell.
    set -g status-right-length 200
    set -g status-right "Alt-F2 for a shell #[range=user|respawn] × restart pane #[norange]#[range=user|detach] × detach #[norange]"

    # Replaces the default `MouseDown1Status { switch-client -t= }`, which
    # exists for the window list and has nothing to select here -- the session
    # has exactly one window.
    #
    # `respawn-pane -k` without a target acts on the active pane, which is the
    # one the operator just clicked to look at. Every pane is `remain-on-exit`
    # (see `create` below), so a pane whose command died stays on screen with
    # its error and this is what brings it back.
    #
    # `detach-client` ends the session cleanly rather than killing it: the tmux
    # client exits, the shim exits with it, `loom-console` returns 0, and the
    # hook at the bottom of this file exits the login shell -- so agetty
    # respawns and the box goes back to the banner and the press-a-key prompt.
    # That is the closest thing this appliance has to a lock screen.
    bind -n MouseDown1Status {
      if -F '#{==:#{mouse_status_range},detach}'  { detach-client }
      if -F '#{==:#{mouse_status_range},respawn}' { respawn-pane -k }
    }
  '';

  # The first pane, in two halves of one life: the bring-up log while Loom comes
  # up, then k9s on the pods once it has. The log is what the operator needs for
  # the minutes or hours the box takes to start, and is dead weight afterwards --
  # up.sh's last line stays on screen for the rest of the boot while the thing it
  # brought up is left unwatched. So the pane hands over instead of splitting,
  # and the widest screen on the box always shows the thing worth looking at.
  #
  # Prints where the unit stands before following it, because a bare
  # `journalctl --follow` on a unit that has not started -- or that a condition
  # skipped -- is an empty screen with no explanation.
  #
  # It also keeps a panel pinned along the bottom of the pane while the log scrolls past
  # above it: how many of the pods the cluster wants are ready, what is blocking, how
  # long it has been since that moved. The log says what is happening and never how much
  # is left, which on a box that takes an hour is the question somebody standing in front
  # of it actually has.
  #
  # The body of it is Python (nixos/ready/, loom_ready/pane.py): pinning a live region
  # below a stream means the stream has to be read line by line rather than left to
  # inherit the pane's stdout, and the handover condition is one definition shared with
  # the status line and the banner.
  #
  # What stays here is this wrapper, deliberately. It is where the unit, the
  # namespace and the k9s path are written down, which is what nixos/tests/scripts/
  # appliance.py reads to prove that both boot modes follow their own unit and that k9s
  # watches the namespace up.sh actually deploys into.
  loom-progress = pkgs.writeShellApplication {
    name = "loom-progress";
    runtimeInputs = [ cfg.ready.package ];
    text = ''
      unit=${lib.escapeShellArg cfg.progressUnit}
      namespace=${lib.escapeShellArg loomNamespace}

      # Empty in setup mode, and that is the whole of how the pane is told there is no
      # readiness to draw: ready.nix publishes nothing there, because that mode is a DHCP
      # client pulling images for hours with no cluster to ask and none coming. The pane
      # is the fetch log alone, and the handover has no state to trigger -- see the
      # namespace note in loom_ready/cluster.py.
      exec loom-ready --pane \
        --unit "$unit" \
        --namespace "$namespace" \
        --state-dir ${lib.escapeShellArg (lib.optionalString readinessPublished cfg.ready.stateDir)} \
        --setup-marker ${lib.escapeShellArg "${loomRepoDir}/.loom-setup-complete"} \
        --k9s ${lib.escapeShellArg (lib.getExe loom-k9s)}
    '';
  };

  # What the first pane turns into, and a command in its own right -- an
  # operator on a plain Alt-F2 console gets the same screen by typing `loom-k9s`.
  #
  # Loom is ~25 pods, and "is it up?" is a question the bring-up log answers only
  # indirectly: up.sh returns long before the last container is ready, and a pod
  # that crash-loops an hour later says nothing there at all. k9s parked on the
  # pod list is that answer, continuously.
  #
  # The namespace is passed explicitly rather than left to the kubeconfig, even
  # though up.sh `use_namespace` (up.sh:775-779) sets the current context to the
  # same value. That context is only set at the END of a bring-up, while this
  # pane can start before it -- it would launch k9s while the context still says
  # `default`, and k9s persists the namespace it started in per context, so the
  # pane would keep showing an empty `default` for the life of the box.
  # `loomNamespace` comes from vars.sh via cicd/build_appliance_image.sh, the
  # same way the *.loom host list does, so there is no second copy of the name to
  # drift.
  #
  # --logoless: the ASCII K9S mark costs the header its right-hand third, and
  # what belongs there is the pod list.
  loom-k9s = pkgs.writeShellApplication {
    name = "loom-k9s";
    runtimeInputs = with pkgs; [
      k9s
      kubectl
      coreutils
    ];
    text = ''
      namespace=${lib.escapeShellArg loomNamespace}

      printf '  Pods in the %s namespace. This pane is the cluster overview.\n' \
        "$namespace"

      # k9s is the one pane that ignores the mouse unless it is told not to.
      # tcell underneath it can do every mouse mode there is -- the binary
      # carries `?1000h`, `?1002h`, `?1003h` and `?1006h` -- but k9s gates them
      # all behind `ui.enableMouse`, which defaults off. Without this the pods
      # list would be the one pane a click does nothing in, which reads as a
      # bug in the shim rather than as a setting.
      #
      # Written at startup into the directory this module already creates,
      # rather than shipped as a store path, for the same reason loom-btop
      # writes its config there: k9s rewrites its own config file on exit, and
      # a store path is read-only. One file rewritten on every start also
      # leaves nothing behind to clean up.
      #
      # Before the wait below rather than after it, which matters on a box that
      # takes an hour to come up: the configuration of this pane has nothing to
      # do with whether the cluster is answering yet, and writing it first is
      # what lets anything -- an operator, the VM test -- see what this command
      # will run with without waiting for a cluster to exist.
      #
      # --logoless is set here too. Leaving it on the command line as well
      # would be two places deciding the same thing.
      conf=${lib.escapeShellArg "${builtins.dirOf tmuxSocket}/k9s"}
      mkdir -p "$conf"
      cat > "$conf/config.yaml" <<'EOF'
      k9s:
        ui:
          enableMouse: true
          logoless: true
      EOF
      # K9S_CONFIG_DIR, not the K9SCONFIG of older releases: that name is gone
      # from k9s 0.51 and setting it would be silently ignored, leaving the
      # pods pane as the one place the mouse does nothing.
      export K9S_CONFIG_DIR="$conf"
      # Logs beside it rather than on the encrypted root, for the same reason
      # loom-chat keeps opencode's state on tmpfs: this appliance is built for
      # ephemeral deployments and should not leave a transcript of what an
      # operator looked at on the disk by accident.
      export K9S_LOGS_DIR="$conf"

      # k9s exits when it cannot reach a cluster. Coming from the pane above
      # there always is one -- that is what the handover waits for -- but typed
      # by hand on a box that is still starting there is not, and a command that
      # quits on the spot is one nobody runs twice. So wait for the namespace to
      # exist. That one check covers both: kubectl cannot list a namespace on a
      # cluster it cannot talk to.
      #
      # --request-timeout, because the interesting failure is not "no
      # kubeconfig" -- which returns at once -- but a kubeconfig pointing at a
      # minikube that is not running, where the default is a two-minute hang per
      # attempt, and a pane that prints nothing for two minutes reads as frozen.
      reachable() {
        kubectl --request-timeout=5s get namespace "$namespace" >/dev/null 2>&1
      }

      if ! reachable; then
        printf '  Waiting for it. This pane fills in once the cluster answers.\n'
        until reachable; do
          sleep 5
        done
      fi

      exec k9s --namespace "$namespace" --command pods
    '';
  };

  # What this particular image is, for the skills below to read. Generated whole
  # rather than substituted into the prose, so the hand-written markdown is
  # byte-identical in the repository and on the box -- ./skills is inside
  # loomSrc, so the sources land at /home/loom/loom/nixos/skills as well, and the
  # agent has `read` and `grep` over that checkout. Two copies of the same
  # sentence that disagree is worse than one copy plus a table.
  #
  # Only facts with no runtime authority are in here. The GPU, the addresses and
  # the interface are deliberately absent: `loom-platform-info` and `loom-info`
  # answer those on the running box, and a skill that says "run the command" is
  # right on every image where one that names a value is right on one.
  applianceFacts = pkgs.writeText "loom-appliance-facts.md" ''
    # What this box is

    Generated when this image was built. Everything here is fixed for this
    image; anything that can change while the box runs is not in this file, so
    read it with `loom-info` or `loom-platform-info` instead.

    | Fact | Value |
    | --- | --- |
    | Platform | `${cfg.platform.id}` -- ${cfg.platform.description} |
    | GPU offload | ${
      if cfg.platform.gpuVendor == null then "none" else "`${cfg.platform.gpuVendor}`"
    } |
    | AI services (Ollama, summarisation, RAG) | ${
      if cfg.platform.runsAiServices then "deployed" else "not deployed"
    } |
    | Boot mode | `${cfg.mode}` |
    | Kubernetes namespace | `${loomNamespace}` |
    | Assistant model | `${loomChatModel}` |
    | Loom checkout | `${loomRepoDir}` |
    | WiFi access point | ${
      if cfg.wifi.enable then "enabled" else "not built in -- radios are blocked"
    } |
    | Remote access (ssh) | ${
      if cfg.debug.enable then
        "**ENABLED** -- this is a `--debug` image, not a production one"
      else
        "none, by design"
    } |
    | Stick key passphrase (`--lock-key`) | ${
      if cfg.keyStore.enable then "required at boot" else "not used"
    } |
    | Client certificate (`--require-client-cert`) | ${
      if cfg.mtls.enable then
        "**required** -- every route the chart renders refuses a client without one, and only `https` is served"
      else
        "not required -- `http` and `https` both reach Loom"
    } |

    ## Names this box resolves

    Every name below is pinned in `/etc/hosts` and served by this box. Not all
    of them serve a web page -- see `${loomRepoDir}/charts/values.yaml`, where
    `hostnames.ingress` are the routed ones and `hostnames.extra` are protocol
    endpoints with nothing to browse.

    ${lib.concatMapStringsSep "\n" (h: "- `${h}`") (builtins.fromJSON loomHostsJson)}
  '';

  # The skills the assistant pane can load: what this box is, and how to operate
  # it. opencode puts only each skill's name and description in the system
  # prompt and loads the body on demand, so this costs a handful of lines per
  # skill until one is actually needed.
  #
  # A store path reached through `skills.paths` rather than a directory inside
  # the config: the config is re-seeded onto tmpfs on every pane start (see
  # loom-chat below) because opencode writes into it, and skills are read-only.
  # Keeping them in the store also keeps them off a RAM disk, out of the
  # operator's reach, and assertable by the appliance test.
  #
  # Every reference file ships on every image. Each SKILL.md names its reference
  # files, so dropping the ones that do not apply would leave the router pointing
  # at something that is not there.
  # `facts.md` above is what says which of them this box can act on.
  #
  # The glob opencode applies to a `skills.paths` entry is `**/SKILL.md` -- not
  # the `{*.md,**/SKILL.md}` the newer in-tree engine uses, which is not the one
  # that reads this key -- so every skill has to be `<name>/SKILL.md`, and a
  # stray markdown file at the root of this tree is ignored rather than
  # registered as a nameless skill.
  # ./skills holds the suite that checks it as well as the skills themselves, and
  # neither that nor the bytecode a local pytest run leaves beside it belongs on
  # an appliance. Filtered here rather than deleted in the builder, so a stray
  # __pycache__ cannot change this derivation's hash either.
  skillSources = lib.cleanSourceWith {
    src = ./skills;
    name = "loom-skill-sources";
    filter =
      path: type:
      let
        base = baseNameOf path;
      in
      !(type == "directory" && (base == "tests" || base == "__pycache__"));
  };

  skillsDir = pkgs.runCommand "loom-skills" { } ''
    mkdir -p "$out"
    cp --recursive ${skillSources}/. "$out/"
    chmod -R u+w "$out"
    cp ${applianceFacts} "$out/loom-appliance/facts.md"

    # opencode registers a skill only if its frontmatter parses and carries a
    # string `name`, and drops it silently otherwise -- no log line, no error,
    # the skill simply never appears. The same is true of a `description` that
    # YAML reads as a map because it was left unquoted around a colon. Catch
    # both here, where the build can fail, rather than on a box where the only
    # symptom is an assistant that has never heard of Loom.
    for skill in "$out"/*/SKILL.md; do
      name="$(basename "$(dirname "$skill")")"
      grep -q "^name: $name\$" "$skill" \
        || { echo "$skill: frontmatter name is not '$name'" >&2; exit 1; }
      grep -q '^description: "' "$skill" \
        || { echo "$skill: description must be a quoted string" >&2; exit 1; }
    done
  '';

  # Always in context, unlike the skills. This exists because the failure mode of
  # a model this size is not picking the wrong skill, it is never reaching for one
  # and answering from priors instead -- which on a box like this produces
  # confident, generic and wrong Linux advice. Nothing in opencode's stock prompt
  # says what kind of machine it is on.
  #
  # Deliberately short, and about procedure rather than content: it is paid for
  # on every turn of a model whose context window is small. The catalogue, the
  # hostnames and the unit list are what the skills are for.
  #
  # It also replaces something. opencode walks up from its working directory for
  # AGENTS.md, then CLAUDE.md -- and the seeded checkout has the repository's
  # own CLAUDE.md, 500-odd lines of instructions about worktrees, GitLab merge
  # requests and poetry lockfiles, which would otherwise be the first thing in
  # this pane's context. `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` in loom-chat is
  # what stops that; this is what goes in its place.
  loomInstructions = pkgs.writeText "loom-agent-instructions.md" ''
    # This machine

    You are running on a Loom appliance: a single-node, air-gapped NixOS box
    serving Loom from a one-node minikube cluster. The person talking to you is
    at its physical console. There is no browser here, no remote access, and no
    route off this box -- do not suggest downloading, installing or fetching
    anything.

    ## How to answer

    Before answering anything about this box, this cluster, or Loom itself, load
    a skill with the `skill` tool. Do not answer from general knowledge about
    Linux, NixOS or Kubernetes: the commands here are specific to this
    appliance, and a plausible-sounding command that does not exist on it is
    worse than no answer. `loom-appliance` is for the box; `loom-usage` is for
    working with documents.

    ## Facts you do not need a skill for

    - The Kubernetes namespace is `${loomNamespace}`.
    - Loom's own source and documentation are at `${loomRepoDir}`.
    - `loom-info` prints what this box is; `loom-ready` prints how far the
      bring-up got.

    ## Rules

    - Use absolute paths. Your working directory is not the same one the
      operator gets at an `Alt-F2` prompt.
    - Never propose `kubectl edit`, `helm upgrade`, or editing anything under
      `/nix/store`. The store is read-only, and this box is reconfigured by
      being brought down and up, not in place.
    - Before anything destructive, say what it will do and let the operator
      decide. Say so plainly rather than refusing.
  '';

  # The assistant pane's config, in the store rather than generated at runtime
  # like loom-btop's: btop rewrites its config on exit and so needs a writable
  # copy, opencode only ever reads this one. A store path also means the appliance
  # test can assert what the image actually ships.
  #
  # `npm` names the adapter opencode loads for this provider.
  # "@ai-sdk/openai-compatible" is deliberate and load-bearing on an air-gapped
  # box: it is one of the packages in opencode's BUNDLED_PROVIDERS table, which
  # provider.ts consults BEFORE falling back to `Npm.add()` -- a fetch from the
  # npm registry, which this box has no route to. Any other adapter name would be
  # looked up there the first time the operator asks a question.
  #
  # https, not http. The appliance serves both -- modes.nix passes up.sh's
  # --enable-http, which widens every ingress to `web, websecure` so the captive
  # portal has a page it can reach without TLS (portal.nix) -- but that exists
  # for visitors, whose phones cannot be handed a CA. This pane runs on the box,
  # where the certificate is verifiable, so it stays on the path that is
  # authenticated. The certificate is cert-manager's, from a selfSigned
  # ClusterIssuer (charts/templates/common/certificate.yaml), which is why
  # loom-chat below has to hand Bun the CA.
  #
  # apiKey restates backend/common/common/settings.py's LLMClientSettings. The
  # endpoint deliberately does NOT: settings.py's `http://ollama.loom/v1/` is a
  # development default that the chart always overrides with the in-cluster
  # Service (settings-configMap.yaml), so the workers never use this route at
  # all. The console is outside the cluster and the ingress is the way in.
  #
  # `lsp` and `mcp` are emptied rather than left out: both default to sets that
  # download servers on demand.
  #
  # `permission` is the whole ruleset in one word. opencode's resolver is
  # `findLast(rule => matches(action) && matches(resource))` over the defaults
  # followed by this file, so a bare "allow" -- which normalises to `{"*":
  # "allow"}` -- lands last and takes back the three prompts the stock build
  # agent still raises: `doom_loop`, `external_directory` (anything outside the
  # pane's cwd) and reading a `.env`. The `--auto` flag is the other way to get
  # here and is not taken: it leaves nothing for the appliance test to read, and
  # every other thing this pane pins lives in the config rather than the exec
  # line. What it costs is real -- the agent edits and runs without asking on a
  # box whose console has no authentication -- but the pane is already a root-
  # adjacent shell's neighbour on tty1, and a prompt the operator cannot
  # meaningfully adjudicate is not a control.
  #
  # `share` is "disabled", not left at its "manual" default: `/share` uploads the
  # session to opencode's own servers. There is no route for it here and the
  # transcript is of an evidence set, so the command is taken away rather than
  # left to fail.
  #
  # `snapshot` off because the pane's cwd is not a git checkout, and the
  # filesystem snapshots only exist to back undo/redo of file edits.
  opencodeConfig = pkgs.writeText "opencode.json" (
    builtins.toJSON {
      autoupdate = false;
      permission = "allow";
      share = "disabled";
      snapshot = false;
      # Loaded on demand; only the names and descriptions are in the system
      # prompt until the model asks for one. An entry that does not resolve is a
      # log line and nothing else -- opencode warns `skill path not found` and
      # carries on -- so the appliance test checks the directory on the running
      # box rather than trusting this string.
      skills.paths = [ "${skillsDir}" ];
      # Always in context. An absolute path is taken verbatim here; the
      # alternative spelling, a bare AGENTS.md discovered from the working
      # directory, resolves differently for the pane and for `loom-chat` typed
      # at a prompt, which have different ones.
      instructions = [ "${loomInstructions}" ];
      model = "ollama/${loomChatModel}";
      lsp = { };
      mcp = { };
      provider.ollama = {
        npm = "@ai-sdk/openai-compatible";
        name = "Loom Ollama";
        options = {
          baseURL = "${ollamaBaseUrl}/v1";
          apiKey = "ollama";
        };
        models.${loomChatModel} = {
          name = "Loom chat model";
        };
      };
    }
  );

  # The pane's colours, which are not a matter of taste here.
  #
  # opencode's own themes are written for a terminal with millions of colours.
  # This one has sixteen, and everything between the pane and the screen is
  # lossy: the pane sends 24-bit, tmux reduces it against a `TERM=linux` client
  # that declares `colors#8`, and what lands is mostly the dim half of the
  # palette. Measured on an appliance by reading /dev/vcsa, 2.4% of the pane's
  # cells came out bright and 5% had a BLACK foreground -- the same failure
  # `loom-btop` has below, for the same reason.
  #
  # `system` is opencode's name for "use the sixteen the terminal already has",
  # and its own help text says so: `Use "theme": "system" to match your
  # terminal's colors`. Those sixteen are Loom's palette on this box, because
  # branding.nix sets `console.colors` from the frontend's tokens -- so the pane
  # comes out in the same amber, green and red as the web UI rather than in
  # whatever opencode shipped, and nothing has to be approximated on the way.
  #
  # A second file rather than a key in the one above: opencode 1.15 moved TUI
  # settings out of `opencode.json` into a `tui.json` beside it, and warns about
  # `tui keys in opencode config are deprecated`. Hence the directory -- the two
  # files have to be siblings, which two `writeText` store paths are not.
  #
  # `plugin_enabled` turns off one of opencode's own built-in TUI plugins, which
  # are registered in the same table as external ones and carry the same ids --
  # `which-key` ships disabled by the same mechanism. `internal:sidebar-context`
  # draws four lines, and the fourth is `$0.00 spent`: unlike the session bar,
  # which renders cost only `if (cost > 0)`, the sidebar block formats it
  # unconditionally through `Intl.NumberFormat(…, "USD")`. There is no key that
  # hides that line on its own, so the block goes. The readout it was worth
  # keeping does not: the session bar carries the same token count, and the same
  # percentage once `limit.context` is known -- see `loom-chat` below, which asks
  # Ollama for it at startup.
  #
  # A price in dollars is not merely noise on this box. It is wrong: the models
  # are local, the figure is always zero because opencode has no cost table for
  # the `ollama` provider this file invents, and an operator reading it has been
  # told something about Loom that is not true.
  opencodeTuiConfig = pkgs.writeText "tui.json" (
    builtins.toJSON {
      theme = "system";
      plugin_enabled."internal:sidebar-context" = false;
    }
  );

  opencodeConfigDir = pkgs.runCommand "loom-opencode-config" { } ''
    mkdir -p "$out"
    cp ${opencodeConfig} "$out/opencode.json"
    cp ${opencodeTuiConfig} "$out/tui.json"
  '';

  # The full-width pane along the bottom: an agent pointed at the Ollama the rest
  # of Loom already uses. No pane of this session is a shell; the shell lives on
  # Alt-F2..Alt-F6, which console.nix leaves as ordinary prompts (see
  # `loginShellInit` at the bottom of this file) and which the status line names.
  #
  # The model is pinned rather than chosen at runtime. An air-gapped box only has
  # what ollama/Dockerfile.models baked in, and pointing the pane at a tag the workers do
  # not use would make Ollama load a second model and evict the one mid-index.
  # `loomChatModel` comes from vars.sh via cicd/build_appliance_image.sh, the same
  # route as the namespace and the host list, so there is no second copy to drift.
  #
  # Also a command in its own right, like loom-k9s: an operator on a plain Alt-F2
  # console gets the same agent by typing `loom-chat`.
  loom-chat = pkgs.writeShellApplication {
    name = "loom-chat";
    runtimeInputs = with pkgs; [
      opencode
      coreutils
      curl
      jq
      kubectl
    ];
    text = ''
      LOOM_CHAT_MODEL=${lib.escapeShellArg loomChatModel}
      LOOM_OLLAMA_ENDPOINT=${lib.escapeShellArg "${ollamaBaseUrl}/v1"}
      LOOM_OLLAMA_PROBE=${lib.escapeShellArg "${ollamaBaseUrl}/"}
      LOOM_OLLAMA_API=${lib.escapeShellArg "${ollamaBaseUrl}/api"}
      LOOM_NAMESPACE=${lib.escapeShellArg loomNamespace}
      LOOM_OPENCODE_STATE=${lib.escapeShellArg "${builtins.dirOf tmuxSocket}/opencode"}
      LOOM_OPENCODE_CONFIG_DIR=${lib.escapeShellArg opencodeConfigDir}

      ${builtins.readFile ./scripts/loom_chat.sh}'';
  };

  # The top-right pane. btop refuses to draw anything but "Terminal size too
  # small" below a minimum that grows with the boxes it shows, and its stock set
  # -- cpu, mem, net and proc -- needs 80x24. The pane it runs in is half the
  # width of the screen and the shorter 40% of its height (`create` below), so on
  # anything but a large monitor that minimum is simply not there, and the
  # operator gets a pane with nothing in it. Hence a box set chosen from the
  # pane's real size at startup:
  #
  #   80x24  cpu mem net proc   the full set
  #   60x18  cpu mem
  #   60x8   cpu                the smallest thing btop will draw
  #
  # `stty size` rather than `tput`, to keep the pane working on a VT whose TERM
  # has no terminfo entry on the box. Inside tmux this reports the pane, not the
  # terminal: every pane gets its own pty, sized to the pane.
  #
  # The measurement happens once, at startup, and btop keeps the box set for the
  # life of the pane -- a later resize redraws the same boxes. So the pane has
  # to be at its final size before this runs, which is what the ordering in
  # `create` below is for.
  #
  # The net box is pinned to the appliance interface for a similar reason: left
  # to itself btop sorts every interface by CUMULATIVE bytes and takes the
  # busiest one that is running, which on this box is `lo` -- minikube's
  # apiserver traffic, and every in-cluster hop that resolves back to the node,
  # all land there. The wired port sees nothing at all until a visitor plugs in,
  # so it never wins that sort, and the choice is sticky: btop only reconsiders
  # if the interface it picked disappears. An operator therefore gets a net box
  # graphing loopback, which answers no question anyone standing at the box has.
  #
  # `net_iface` is the starting interface, not a lock -- `b`/`n` still cycle, and
  # neither key writes the config back -- and an interface named here that does
  # not exist is silently ignored in favour of the same auto-pick, so this is
  # safe in every build. It also puts the box address in the net box's header,
  # which is the number a walk-up operator actually wants.
  #
  # `gpu0` is deliberately NOT in any of those box sets, on the platform whose
  # btop can read a GPU (`loom.btopPackage`). btop shows the GPU two ways and
  # they are mutually exclusive: as its own box, or as a line inside the cpu box
  # under `show_gpu_info`, whose default "Auto" means "show it here unless a
  # dedicated box already has it" -- `gpus.size() > 0 and (gpu_always or
  # (gpu_auto and Gpu::shown < Gpu::count))` in btop_draw.cpp. Naming `gpu0`
  # would therefore *remove* the GPU from the cpu box and spend a whole box of a
  # pane that is half the screen wide and 40% of it tall on it. Leaving it out
  # keeps the GPU on screen at every rung of the ladder above, the 60x8 cpu-only
  # one included, and costs no space at all. Nothing is written for it: "Auto"
  # is the default, and this config sets only the two keys above.
  loom-btop = pkgs.writeShellApplication {
    name = "loom-btop";
    runtimeInputs = [
      # Built for this platform's GPU; see loom.btopPackage below.
      cfg.btopPackage
      pkgs.coreutils
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
      {
        printf 'shown_boxes = "%s"\n' "$boxes"
        printf 'net_iface = "%s"\n' ${lib.escapeShellArg cfg.serviceInterface}
      } > "$conf"

      # --force-utf: a Linux VT with no locale set otherwise drops btop back to
      # ASCII box drawing. Spelled --utf-force before btop 1.4, where it is now
      # an unknown argument and btop exits non-zero.
      #
      # --tty: the pane is on a Linux console, and btop cannot tell. It decides
      # by looking at its own tty name -- `Auto detect real TTY`, matching
      # /dev/tty* -- which is true on an Alt-F2 shell and false for every pane
      # here, because a pane is a /dev/pts/N. So the same btop that draws itself
      # for a console on tty2 draws itself for a graphical terminal in this
      # pane, and both halves of that are wrong on this box:
      #
      #   * The theme. Non-tty btop paints its Default theme in 24-bit colour,
      #     which tmux -- whose client is `TERM=linux`, `colors#8` -- flattens
      #     with `colour_256to16`. Measured by reading /dev/vcsa, the VT's
      #     attribute plane, on an appliance: 40% of the pane's inked cells came
      #     out with a BLACK foreground, i.e. invisible, and only 5.6% were
      #     bright. The TTY theme is sixteen named colours instead, which tmux
      #     passes through unchanged, and the same measurement reads 49.1%
      #     bright and 36.9% carrying a hue -- within a point of what that btop
      #     draws unaided on tty2.
      #
      #     Handing tmux the original colour instead is worse:
      #     `terminal-features linux*:RGB` lets the kernel do the reduction, and
      #     the kernel thresholds r/g/b, so btop's near-grey Default gradient
      #     goes to white. 65.7% bright, 3.0% hued -- a brighter screen with the
      #     colour gone out of it. What makes tty2 readable was never colour
      #     depth; it is that its palette is named rather than approximated.
      #
      #   * The graph symbols. Non-tty btop draws with braille (U+28xx), which
      #     is a way of getting sub-cell resolution out of a small font. This
      #     console's font is 12x26 (branding.nix), where the dots are far apart
      #     and the bars read as dotted rather than drawn. TTY mode uses the
      #     three shaded blocks instead, which are solid at any cell size.
      #
      # It costs the serial client (vm-serial.nix, `TERM=xterm-256color`) the
      # 24-bit theme it could have had. That is the right way round: those tools
      # exist to show what the operator at the box sees, and a VM that looks
      # better than the hardware is a VM that hides this exact bug.
      exec btop --tty --force-utf --config "$conf"
    '';
  };

  # Keeps a pane's program running.
  #
  # Every pane of this session is a single application, and quitting one -- k9s
  # with `:q`, btop with `q`, opencode with its own exit -- would otherwise
  # leave a dead pane that stays dead. On a box whose console is the entire user
  # interface that is a trap: the operator presses the wrong key once and loses
  # a third of the screen until they find the restart control.
  #
  # So the panes are supervised rather than run directly. This is deliberately
  # NOT a bare `while true`: a command that fails instantly -- a missing
  # binary, a TUI that will not start in the pane it was given -- would spin as
  # fast as the kernel can fork, flooding the pane, pinning a core and making
  # the box less usable than the dead pane it replaced.
  #
  # Hence a backoff, and a floor under what counts as success. A program that
  # ran for a while and then exited is something the operator quit, and comes
  # straight back. A program that exits immediately, twice, is broken, and the
  # gap between attempts grows until it is slow enough to read the error.
  loom-pane = pkgs.writeShellApplication {
    name = "loom-pane";
    runtimeInputs = [ pkgs.coreutils ];
    # No prologue: the command to supervise arrives as "$@", so the file is
    # the whole of it. The header there says why it is a file.
    text = builtins.readFile ./scripts/loom_pane.sh;
  };

  loom-console = pkgs.writeShellApplication {
    name = "loom-console";
    runtimeInputs = with pkgs; [
      tmux
      coreutils
    ];
    text = ''
      LOOM_TMUX_SOCKET=${lib.escapeShellArg tmuxSocket}
      LOOM_TMUX_CONF=${tmuxConf}
      LOOM_REPO_DIR=${lib.escapeShellArg loomRepoDir}
      LOOM_PANE=${lib.escapeShellArg (lib.getExe loom-pane)}
      LOOM_PROGRESS=${lib.escapeShellArg (lib.getExe loom-progress)}
      LOOM_BTOP=${lib.escapeShellArg (lib.getExe loom-btop)}
      LOOM_CONSOLE_MOUSE=${lib.escapeShellArg (lib.getExe cfg.consoleMouse.package)}
      LOOM_AI_ENABLED=${lib.boolToString aiEnabled}
      LOOM_CHAT=${lib.escapeShellArg (lib.optionalString aiEnabled (lib.getExe loom-chat))}

      ${builtins.readFile ./scripts/loom_console.sh}'';
  };
in
{
  # Published so tests/appliance-skills.nix can read what this image shipped.
  # `opencodeConfig` and the two paths it names are `let` bindings, and an
  # evaluation-time check has no other way to reach them -- the alternative is
  # grepping the generated JSON out of the store, which asserts the spelling of
  # the config rather than the thing it points at.
  #
  # Null on a platform with no Ollama: box.nix leaves `opencode` out of the
  # closure there, console.nix builds no assistant pane, and shipping skills for
  # an assistant that does not exist would be dead weight the test should catch
  # rather than tolerate.
  options.loom.assistant.skillsDir = lib.mkOption {
    type = lib.types.nullOr lib.types.path;
    default = if aiEnabled then skillsDir else null;
    defaultText = lib.literalExpression "the assembled skills, when the platform runs Ollama";
    readOnly = true;
    internal = true;
    description = ''
      The skill tree the assistant pane loads from, or null on a box with no
      assistant.
    '';
  };

  options.loom.assistant.instructionsFile = lib.mkOption {
    type = lib.types.nullOr lib.types.path;
    default = if aiEnabled then loomInstructions else null;
    defaultText = lib.literalExpression "the generated instructions, when the platform runs Ollama";
    readOnly = true;
    internal = true;
    description = ''
      The always-in-context instructions the assistant pane is given, or null on
      a box with no assistant.
    '';
  };

  # An option rather than a literal in the two places that dial Ollama, because
  # one of them is a JSON file and the other a shell script, and a box behind
  # its own mutual TLS has to move both at once (mtls.nix).
  options.loom.assistant.ollamaBaseUrl = lib.mkOption {
    type = lib.types.str;
    default = "https://${ollamaHost}";
    defaultText = lib.literalExpression "\"https://\${ollamaHost}\"";
    internal = true;
    description = ''
      Where the assistant pane reaches Ollama, without a trailing slash.

      The ingress by default, over https: the appliance serves plain http as
      well (modes.nix passes up.sh's --enable-http, for the captive portal), but
      that exists for visitors who cannot be handed a CA, and this pane runs on
      the box where the certificate is verifiable.

      mtls.nix points it at the loopback proxy instead, which is http -- one
      hop, on this machine, in front of the certificate that opencode has
      nowhere to put.
    '';
  };

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

  options.loom.btopPackage = lib.mkOption {
    type = lib.types.package;
    default = pkgs.btop.override {
      cudaSupport = cfg.platform.gpuVendor == "nvidia";
      rocmSupport = cfg.platform.gpuVendor == "amd";
    };
    defaultText = lib.literalExpression "pkgs.btop, built for loom.platform.gpuVendor";
    internal = true;
    description = ''
      The btop the box carries, built to reach this platform's GPU.

      Neither flag adds a compute stack. Stock btop already has GPU support
      compiled in -- it dlopens libnvidia-ml.so.1 and librocm_smi64.so at
      runtime -- and the derivation has no CUDA or ROCm entry in buildInputs at
      all. What the flags change is the RUNPATH, so that dlopen finds something:
      `cudaSupport` prepends /run/opengl-driver/lib via autoAddDriverRunpath,
      and `rocmSupport` patchelfs ${"\${rocmPackages.rocm-smi}"}/lib on. So the
      cuda build is byte-for-byte the same size as the plain one, and the rocm
      build differs by rocm-smi alone -- which on the one platform that asks for
      it (evo-x2) is already in `loom.toolchain` for up.sh's preflight, and is
      the same store path rather than a second copy. Both are in the binary
      cache, so neither is a source rebuild either.

      Keyed on `loom.platform.gpuVendor` rather than on a second notion of
      "has a GPU", which also means `--no-gpu` gets the plain build for free
      (nixos/default.nix forces gpuVendor to null there). A platform that
      declares a vendor therefore gets the matching build with no edit here: on
      the Spark the dlopen resolves because platforms/spark.nix keeps
      `nvidia_x11.out` in `hardware.graphics.extraPackages`, which is what
      populates /run/opengl-driver/lib.

      On the EVO-X2 the rocm path works despite that platform forcing
      `hardware.graphics.extraPackages` empty, because btop reaches
      librocm_smi64.so through its own rpath rather than through
      /run/opengl-driver. The two platforms therefore differ on purpose: the
      Spark needs that directory populated and the EVO-X2 does not.

      An option rather than a literal in each place because there are two
      readers -- box.nix puts it on PATH, and loom-btop below runs it in the
      console pane. Picking the package separately would let a shell `btop` show
      a GPU row while the pane the operator is actually looking at did not.
    '';
  };

  config = {
    # -------------------------------------------------------------------------
    # Nothing logs in unattended.
    #
    # `--login-pause` makes agetty print the issue -- box.nix's banner -- then
    # `[press ENTER to login]`, then block on a single keypress before running
    # `login -f loom`. The operator types no username and no password, and the
    # box does not open a session for nobody at boot.
    #
    # `--autologin` is what performs the login (agetty adds `-f <user>` to the
    # login command line for it), so PAM bypasses the account's locked shadow
    # entry. Removing `autologinUser` instead would not produce a passwordless
    # Enter -- agetty re-prompts on empty input and would simply demand the
    # username.
    #
    # Both options apply to every getty, tty2-tty6 included; on NixOS tty1's
    # getty runs as `autovt@tty1.service`, an alias of the `getty@` template, so
    # per-instance overrides of `getty@tty1` are not consulted and scoping these
    # would not work anyway.
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
    # /dev/console is the active VT, so every `StandardOutput = "journal+console"`
    # line would land on tty1 -- on top of the login prompt, and on top of the
    # session below. That is handled where it belongs: the units in modes.nix and
    # network.nix log to the journal only, and the first pane follows them
    # instead.
    #
    # `tty0` and nothing else. The three cases are genuinely different, and only
    # one of them is safe:
    #
    #   * A NUMBERED VT is a trap. Naming one does not merely redirect output to
    #     it, it makes that VT the foreground console: `console=tty12` leaves the
    #     box showing the kernel log, with the banner and the press-a-key prompt
    #     rendered on a tty1 nobody is looking at and nobody's keystrokes reach.
    #     tests/scripts/loom_tests/appliance/modes.py forbids `console=tty<N>`
    #     for exactly this, and asserts `fgconsole` is 1.
    #   * A SERIAL PORT is the same trap pointed at a cable. It makes the port
    #     the primary console, so a panic on a box with nothing plugged in goes
    #     nowhere at all instead of onto the monitor somebody is standing in
    #     front of.
    #   * `tty0` is neither: it is whatever VT is currently foreground, so it
    #     cannot move the console off the screen the operator is using -- which
    #     is what the paragraph above means by /dev/console being "the active
    #     VT".
    #
    # Naming it is load-bearing rather than cosmetic, because that behaviour
    # only holds where the kernel registers tty0 by itself. Firmware that
    # publishes an ACPI SPCR table names a serial console the appliance has no
    # driver for, that UART never registers, and -- with nothing on the command
    # line to override it -- neither does anything else. `/proc/consoles` comes
    # out EMPTY and /dev/console is ENODEV, which silently costs two things that
    # have no other way to reach an operator: key-store.nix's `give_up`, whose
    # whole job is to say the next prompt wants the recovery passphrase rather
    # than the stick's, and systemd's own emergency and rescue shells.
    # -------------------------------------------------------------------------
    boot.kernelParams = [ "console=tty0" ];

    # -------------------------------------------------------------------------
    # The session
    # -------------------------------------------------------------------------
    systemd.tmpfiles.rules = [
      "d /run/loom 0700 ${loomUser} users -"
    ];

    environment.systemPackages = [
      loom-console
      loom-progress
      loom-k9s
      loom-btop
    ]
    # Pointless on a box with no Ollama, and it drags opencode's Bun binary and
    # baked model catalogue along with it.
    ++ lib.optional aiEnabled loom-chat;

    # Only tty1. tty2-tty6 deliberately get an ordinary shell, so a session that
    # will not start is never the only thing between the operator and a prompt.
    environment.loginShellInit = ''
      if [ -z "''${LOOM_SESSION:-}" ] \
        && [ "$(id -un)" = ${lib.escapeShellArg loomUser} ] \
        && [ "$(tty)" = /dev/tty1 ]; then
        export LOOM_SESSION=1

        # Deliberately not `exec`: a loom-console that died on startup would
        # take the login shell with it, agetty would respawn, and the operator
        # would be left in a loop with nowhere to type. Run it as a child and
        # only leave the shell when it actually worked.
        if ${lib.getExe loom-console}; then
          exit 0
        fi
        echo "[!] loom-console failed -- dropping to a plain shell." >&2
      fi
    '';
  };
}
