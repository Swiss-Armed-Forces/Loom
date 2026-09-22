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
#   * None of those panes is a shell. The middle column used to be, and is now
#     opencode pointed at the cluster's own Ollama -- the box already carries a
#     model, and nothing on the console could reach it. A prompt is Alt-F2 away,
#     on the tty2-tty6 gettys this module has always left alone, and the status
#     line says so.
#   * Nothing else writes to that screen. The units that used to log to
#     /dev/console -- which, with no `console=` on the command line, meant the
#     VT the operator is looking at -- log to the journal only now, and the
#     first pane is what shows them.
#   * It is driven with a mouse as well as a keyboard, on a console that has no
#     mouse driver behind it. That takes a daemon and a pty shim, both of which
#     live in console-mouse.nix; what belongs here is the other half -- the tmux
#     side. `mouse on` was always set and was inert on tty1; it is now
#     load-bearing there. The prefix is switched off, since navigation is by
#     clicking, and the two things the prefix used to be needed for -- detach
#     and respawning a dead pane -- are clickable regions in the status line.
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
  # rather than to show an empty bar, so that console is byte-for-byte the one this box
  # shipped with before the bar existed.
  readinessPublished = cfg.ready.enable && cfg.mode == "run";

  # The status line's readiness segment, or nothing. Built here rather than inline so the
  # status-left assignment below stays one line with one meaning, whichever mode this is.
  readinessSegment = lib.optionalString readinessPublished (
    "#(${lib.getExe cfg.ready.package} --oneline --state-dir ${cfg.ready.stateDir})  "
  );

  # Taken from the host list rather than written out again, so the name the chat
  # pane dials is by construction one of the names box.nix pins in /etc/hosts.
  # Spelling it "ollama.loom" here instead would be a second copy of the domain,
  # and a box built with a different one would get a pane that cannot resolve.
  ollamaHost = lib.findFirst (h: lib.hasPrefix "ollama." h) "ollama.loom" (
    builtins.fromJSON loomHostsJson
  );

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
    # Load-bearing on tty1 now, not just over serial. The shim
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
    # The status line, which is now the only user interface tmux itself has.
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
    # Alt-F2 keeps its wording: no pane of this session is a shell, so it is
    # still the only route to a prompt -- and with the prefix gone it is also
    # the backstop for anything this status line cannot do.
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
    # Both are empty in setup mode -- see `readinessPublished` -- so that
    # console is exactly the one this box shipped with before any of this.
    # -------------------------------------------------------------------------
    ${lib.optionalString readinessPublished "set -g status-interval 5"}
    set -g status-left-length 60
    set -g status-left "  LOOM  ${readinessSegment}"
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
    # its error and this is what brings it back -- the job `Ctrl-b
    # :respawn-pane` used to do.
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
  # And, since the readiness bar went in, it keeps a panel pinned along the bottom of the
  # pane while the log scrolls past above it: how many of the pods the cluster wants are
  # ready, what is blocking, how long it has been since that moved. The log has always
  # said what is happening and never how much is left, which on a box that takes an hour
  # is the question somebody standing in front of it actually has.
  #
  # That is why the body of this moved into Python (nixos/ready/, loom_ready/pane.py):
  # pinning a live region below a stream means the stream has to be read line by line
  # rather than left to inherit the pane's stdout, and the handover condition is now one
  # definition shared with the status line and the banner instead of a `case` here.
  #
  # What stays is this wrapper, and it stays deliberately. It is where the unit, the
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
      # is the fetch log alone, exactly as it was, and the handover it has no state to
      # trigger is the same handover that never fired there before -- see the namespace
      # note in loom_ready/cluster.py.
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
      # --logoless moves in here with it. Leaving it on the command line as
      # well would be two places deciding the same thing.
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
  # https, not http. Every ingress in charts/values.yaml is annotated
  # `router.entrypoints: websecure` and nothing else -- only values-development
  # widens that to `web, websecure` -- so on a box running production values
  # there is no router on port 80 for this host and plain HTTP gets a Traefik
  # 404 without ever reaching TLS. The certificate is cert-manager's, from a
  # selfSigned ClusterIssuer (charts/templates/common/certificate.yaml), which
  # is why loom-chat below has to hand Bun the CA.
  #
  # apiKey restates backend/common/common/settings.py's LLMClientSettings. The
  # endpoint deliberately does NOT: settings.py's `http://ollama.loom/v1/` is a
  # development default that the chart always overrides with the in-cluster
  # Service (settings-configMap.yaml), so the workers never use this route at
  # all. The console is outside the cluster and the ingress is the way in.
  #
  # `lsp` and `mcp` are emptied rather than left out: both default to sets that
  # download servers on demand.
  opencodeConfig = pkgs.writeText "loom-opencode.json" (
    builtins.toJSON {
      autoupdate = false;
      model = "ollama/${loomChatModel}";
      lsp = { };
      mcp = { };
      provider.ollama = {
        npm = "@ai-sdk/openai-compatible";
        name = "Loom Ollama";
        options = {
          baseURL = "https://${ollamaHost}/v1";
          apiKey = "ollama";
        };
        models.${loomChatModel} = {
          name = "Loom chat model";
        };
      };
    }
  );

  # The full-width pane along the bottom: an agent pointed at the Ollama the rest
  # of Loom already uses. The pane it replaced was a plain shell; the shell now lives on
  # Alt-F2..Alt-F6, which console.nix has always left as ordinary prompts (see
  # `loginShellInit` at the bottom of this file) and which the status line names.
  #
  # The model is pinned rather than chosen at runtime. An air-gapped box only has
  # what ollama/Dockerfile baked in, and pointing the pane at a tag the workers do
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
      kubectl
    ];
    text = ''
      model=${lib.escapeShellArg loomChatModel}
      endpoint=${lib.escapeShellArg "https://${ollamaHost}/v1"}
      # Ollama's root route, which answers "Ollama is running" and nothing else.
      # What the wait below gates on -- see `ready`.
      probe=${lib.escapeShellArg "https://${ollamaHost}/"}
      namespace=${lib.escapeShellArg loomNamespace}

      export OPENCODE_CONFIG=${lib.escapeShellArg opencodeConfig}

      # Both are runtime flags (packages/core/src/flag/flag.ts), and neither is
      # set by the binary's wrapper: nixpkgs bakes models.dev's catalogue into the
      # closure and sets OPENCODE_DISABLE_MODELS_FETCH while *building*, which
      # does nothing for the process the operator runs.
      #
      # Not a hang fix -- measured, opencode falls back to the baked-in catalogue
      # in about two seconds when the network is simply absent. It is a policy:
      # this box makes no outbound connection it was not asked to make, and
      # "fails fast" depends on how the failure arrives. A refused route answers
      # immediately; a silently dropped packet does not, and the appliance's own
      # dnsmasq plus whatever the site does upstream is exactly the shape where
      # that difference shows up.
      export OPENCODE_DISABLE_MODELS_FETCH=1
      export OPENCODE_DISABLE_AUTOUPDATE=1

      # Sessions, logs and caches land on tmpfs, not on the encrypted root. This
      # appliance is built for ephemeral, task-specific deployments, and the
      # transcript of what an operator asked about an evidence set is not
      # something to leave on the disk by accident. /run/loom is created by the
      # tmpfiles rule below and is 0700 loom.
      state=${lib.escapeShellArg "${builtins.dirOf tmuxSocket}/opencode"}
      mkdir -p "$state"
      export XDG_DATA_HOME="$state/data"
      export XDG_STATE_HOME="$state/state"
      export XDG_CACHE_HOME="$state/cache"

      printf '  Loom assistant on %s.\n' "$model"

      # The ingress serves a cert-manager certificate from a selfSigned issuer,
      # so the chain ends at a root nothing has heard of and Bun refuses it with
      # "unable to verify the first certificate". Trust it explicitly rather than
      # switching verification off: NODE_TLS_REJECT_UNAUTHORIZED=0 would disable
      # it for every connection the process makes, not just this one.
      #
      # Read through the API rather than off the wire: pulling the chain from the
      # server and then trusting it would verify nothing at all.
      #
      # Two secrets, because which one Traefik presents depends on how the chart
      # was deployed, and a bundle costs nothing:
      #
      # Trusting the certificate is only half of it: it also has to name the
      # host. The chart's Job puts every `*.loom` host in the subjectAltName one
      # by one, because a wildcard cannot do it -- `*.loom` has one dot, and
      # OpenSSL (so also Bun, and curl in `ready` below) will not expand a
      # wildcard under a single-label parent. A release whose chart predates
      # `hostnames` in charts/values.yaml serves a certificate that cannot
      # verify no matter what is in this bundle, and `ready` says so.
      #
      #   self-signed-cert  The `CN=*.loom` certificate that
      #                     charts/templates/pre-install/generate-self-signed-certificate.yaml
      #                     makes with `openssl req -x509` on every install, and
      #                     that traefik/tls-store.yaml sets as the DEFAULT
      #                     certificate. This is what actually answers on a stock
      #                     box, because charts/values.yaml has
      #                     `certificate.enabled: false`.
      #   <release>-certificate  cert-manager's, named by the Ingress, and
      #                     present only when that value is turned on.
      #
      # Both are tried for `ca.crt` first and `tls.crt` second: a `kubectl create
      # secret tls` secret -- which is how the pre-install Job stores its cert --
      # has no `ca.crt` at all. Trusting the leaf is right here rather than a
      # fudge: `openssl req -x509` emits basicConstraints CA:TRUE, so that
      # certificate genuinely is its own root.
      ca="$state/ollama-ca.crt"
      append_cert() {
        local secret key pem
        secret="$1"
        [ -n "$secret" ] || return 0
        for key in 'ca\.crt' 'tls\.crt'; do
          pem="$(kubectl --request-timeout=5s --namespace "$namespace" \
            get secret "$secret" --output "jsonpath={.data.$key}" 2>/dev/null \
            | base64 --decode 2>/dev/null)" || continue
          case "$pem" in
            *"BEGIN CERTIFICATE"*)
              printf '%s\n' "$pem" >> "$ca.tmp"
              return 0
              ;;
            *) ;;
          esac
        done
        return 0
      }

      fetch_ca() {
        : > "$ca.tmp"
        append_cert self-signed-cert
        append_cert "$(kubectl --request-timeout=5s --namespace "$namespace" \
          get ingress --selector app.kubernetes.io/component=ollama \
          --output jsonpath='{.items[0].spec.tls[0].secretName}' 2>/dev/null || true)"
        # An empty bundle would make every request fail with a less obvious error
        # than the one this exists to fix, so only publish something that has at
        # least one certificate in it.
        grep --fixed-strings "BEGIN CERTIFICATE" "$ca.tmp" >/dev/null || return 1
        mv "$ca.tmp" "$ca"
      }

      # Same shape, and the same reason, as loom-k9s's wait: this pane can start
      # long before the cluster answers. `ollama.loom` is pinned in /etc/hosts
      # from the first boot (box.nix), so a premature start does not fail fast
      # with NXDOMAIN -- it hangs against a Traefik that is not listening yet, and
      # a pane that prints nothing reads as frozen.
      #
      # What this waits for is that Ollama answers over a connection that
      # verifies, and nothing more. Whether the pinned model is in its inventory
      # used to be part of the same condition, on the grounds that opencode exits
      # when its first request fails -- but a model that never arrives is then a
      # pane that waits forever and says only that it is waiting, which is a
      # worse failure than the one it was avoiding. A missing model is now a
      # warning below and opencode's own error afterwards: the pane is
      # `remain-on-exit` and supervised by loom-pane, so that error stays on
      # screen, comes back on a backoff and offers "× restart pane".
      #
      # Said once per change rather than once per attempt, so a pane that waits
      # an hour for a bring-up does not scroll one line every five seconds.
      wait_reason=""
      note() {
        if [ "$1" != "$wait_reason" ]; then
          wait_reason="$1"
          printf '  %s\n' "$1"
        fi
      }

      # The halves are checked separately and named separately. Folded into one
      # predicate they produce the same silence for "the cluster has not issued
      # its certificate yet", "nothing is listening on 443 yet" and "the name
      # resolves to something that is not Ollama", which are fixed by different
      # things.
      #
      # curl's own message is carried into the wait line rather than dropped.
      # This is the whole reason that was worth changing: --silent without
      # --show-error, plus a discarded body, meant one line stood for a cert that
      # does not verify, a route that 404s and a model that is not there, and an
      # operator looking at the pane could not tell which. `2>&1 >"$body"`
      # duplicates stderr onto the substitution's pipe *before* stdout goes to
      # the file, so the status is curl's and the message is curl's.
      #
      # The body is matched too, and not only for tidiness: the appliance answers
      # wildcard *.loom from its own dnsmasq (network.nix), so a misrouted name
      # lands on some other Loom service that is only too happy to return 200 on
      # `/`. --fail catches Traefik's 404 for a host it does not route; it cannot
      # catch that.
      ready() {
        local err body
        if ! fetch_ca; then
          note "Waiting for the cluster's TLS certificate."
          return 1
        fi
        body="$state/ollama-probe"
        if ! err="$(curl --silent --show-error --fail --max-time 5 \
          --cacert "$ca" "$probe" 2>&1 >"$body")"; then
          # Folded onto one line: curl's cert diagnostics run to several, and
          # this is a status line in a pane, not a report.
          note "Waiting for Ollama at $probe: ''${err//$'\n'/ }"
          return 1
        fi
        if ! grep --fixed-strings "Ollama is running" "$body" >/dev/null; then
          note "Waiting for Ollama at $probe: something else answered."
          return 1
        fi
        return 0
      }

      until ready; do
        sleep 5
      done

      # Said once, and not waited on. An air-gapped box only has the models
      # ollama/Dockerfile baked in, and the one thing that cannot be fixed from
      # this pane is a model that is not on the box -- so name it here, where the
      # operator is already looking, rather than let opencode's first failure be
      # the only clue. /api/ps is what the chart probes, and it answers 200 on an
      # empty model store, so a Ready ollama pod proves nothing about this.
      #
      # `grep` without -q, deliberately -- this one is a pipeline, unlike the
      # probe above: the script runs under `set -o pipefail`, and -q makes grep
      # exit on the first match, which hands the producer on its left an EPIPE
      # and fails the pipeline *because* the match was found. The same trap is
      # documented at length in tests/appliance.nix.
      if ! curl --silent --fail --max-time 5 --cacert "$ca" "$endpoint/models" \
        | grep --fixed-strings "$model" >/dev/null; then
        printf '  Warning: Ollama does not list %s.\n' "$model"
        printf '  Starting anyway; the first question will fail until it does.\n'
        printf '  What is on the box: ollama list, in the ollama pod.\n'
      fi

      # Bun honours this the same way Node does -- measured against a self-signed
      # server: the fetch fails with "self signed certificate" without it and
      # succeeds with it.
      export NODE_EXTRA_CA_CERTS="$ca"

      exec opencode
    '';
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
      exec btop --force-utf --config "$conf"
    '';
  };

  # Keeps a pane's program running.
  #
  # Every pane of this session is a single application, and quitting one -- k9s
  # with `:q`, btop with `q`, opencode with its own exit -- used to leave a dead
  # pane that stayed dead. On a box whose console is the entire user interface
  # that is a trap: the operator presses the wrong key once and loses a third of
  # the screen until they find the restart control.
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
    text = ''
      # How long a run has to last before it is treated as "it worked, the
      # operator just quit". Both TUIs here take well under a second to draw,
      # so anything above a few seconds means it really did run.
      settled=5
      # First wait, and the ceiling it doubles up to. 30s is short enough that
      # a box recovering from a transient failure comes back on its own, and
      # long enough that a permanently broken command is not a busy loop.
      delay=1
      max_delay=30

      # The program's own name, for the notice below: the full argument is a
      # store path and would wrap the pane on its own.
      name=$(basename "$1")

      while true; do
        started=$SECONDS
        # Deliberately not `exec`: this loop has to outlive the program. And
        # `|| true` because writeShellApplication sets `set -e`, under which a
        # TUI exiting non-zero would take the supervisor with it.
        "$@" || true
        ran=$(( SECONDS - started ))

        if [ "$ran" -ge "$settled" ]; then
          # It ran, so whatever ended it was a decision rather than a fault.
          # Start again at once, and from a clean backoff.
          delay=1
          printf '\n  [%s exited after %ss -- restarting]\n' "$name" "$ran"
        else
          printf '\n  [%s exited after %ss -- restarting in %ss]\n' \
            "$name" "$ran" "$delay"
        fi

        sleep "$delay"

        # Grow the wait only for runs that did not settle. Written as an `if`
        # rather than `[ ... ] && delay=...`, because a false test there is a
        # non-zero exit status, and under `set -e` that would end the loop at
        # the ceiling instead of staying on it.
        if [ "$ran" -lt "$settled" ]; then
          delay=$(( delay * 2 ))
          if [ "$delay" -gt "$max_delay" ]; then
            delay=$max_delay
          fi
        fi
      done
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

      # The size of the VT this script was started on. The session below is
      # created detached, and a detached session takes its window size from
      # tmux's `default-size` -- 80x24 -- however big the console actually is.
      # Panes split out of that are tiny, and loom-btop, which picks its box set
      # from the pane it starts in, would measure around 39x11 and draw one box
      # on a console with room for four. The attach at the bottom resizes the
      # window afterwards, but by then btop has already written its config.
      # Nothing else knows the real size: this script runs on the VT, so it asks
      # the VT and hands the answer to `new-session`.
      read -r lines cols < <(stty size 2>/dev/null || echo "24 80")

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
      supervise=${lib.escapeShellArg (lib.getExe loom-pane)}

      create() {
        local main mon${lib.optionalString aiEnabled " chat"}
        main=$("''${tm[@]}" new-session -d -x "$cols" -y "$lines" -s loom -n loom \
          -P -F '#{pane_id}' "$supervise" ${lib.getExe loom-progress})
      ${lib.optionalString aiEnabled ''
        # -c so the assistant starts in the checkout: it is what an operator
        # asking about this box would want it looking at, and `respawn-pane`
        # below keeps a pane's start directory.
        chat=$("''${tm[@]}" split-window -v -l 60% -t "$main" \
          -c ${lib.escapeShellArg loomRepoDir} -P -F '#{pane_id}')
      ''}
        mon=$("''${tm[@]}" split-window -h -t "$main" -P -F '#{pane_id}')

        # Plain shells first, the real commands only once every split is done. A
        # split takes its space from the pane it came from, so a pane created
        # early is resized by each later one -- and both loom-chat and loom-btop
        # draw TUIs that measure their pane once at startup and cannot take that
        # back. Hence the respawns into panes that have stopped moving.
      ${lib.optionalString aiEnabled ''
        "''${tm[@]}" respawn-pane -k -t "$chat" "$supervise" ${lib.getExe loom-chat}
      ''}
        "''${tm[@]}" respawn-pane -k -t "$mon" "$supervise" ${lib.getExe loom-btop}

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
        "''${tm[@]}" set-option -p -t "$main" remain-on-exit on
        "''${tm[@]}" set-option -p -t "$mon" remain-on-exit on

        # How usb-ingest.nix finds the pane to split while a stick is being
        # copied: k9s stays in the top half and the copy is drawn underneath it.
        # A user option rather than an index, because indices follow layout
        # position and are rewritten by every split -- including that one. See
        # nixos/usb-ingest/loom_usb_ingest/pane.py.
        "''${tm[@]}" set-option -p -t "$main" @loom-main 1
      ${
        if aiEnabled then
          ''
            "''${tm[@]}" set-option -p -t "$chat" remain-on-exit on
                    # Land in the assistant, not in the log.
                    "''${tm[@]}" select-pane -t "$chat"''
        else
          ''
            # No assistant to land in, so land on the log -- which is the pane
                    # that becomes k9s, and the one an operator watches on this box.
                    "''${tm[@]}" select-pane -t "$main"''
      }
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
      exec ${lib.getExe cfg.consoleMouse.package} -- \
        "''${tm[@]}" attach-session "''${@}" -t loom
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
      (nixos/default.nix forces gpuVendor to null there). That is what happened
      when the Spark gained its GPU: platforms/spark.nix set the vendor and
      brought `hardware.nvidia` along with it, and the cuda build followed here
      with no edit -- the dlopen resolves because that file keeps
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
    # `login -f loom`. The operator types no username and no password, but the
    # box no longer opens a session for nobody at boot.
    #
    # `--autologin` is still what performs the login (agetty adds `-f <user>` to
    # the login command line for it), so PAM sees exactly what it saw before:
    # the account's locked shadow entry is bypassed the same way it always was.
    # Removing `autologinUser` instead would not produce a passwordless Enter --
    # agetty re-prompts on empty input and would simply demand the username.
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
    # The appliance named no console at all, so /dev/console was the active VT
    # and every `StandardOutput = "journal+console"` line from modes.nix and
    # network.nix landed on tty1 -- on top of the login prompt, and on top of
    # the session below. That is fixed where it belongs: those units log to the
    # journal only now, and the first pane follows them instead.
    #
    # There is deliberately NO `console=` here at all -- neither a VT nor a
    # serial port. Naming a VT on the kernel command line does not merely
    # redirect output to it, it makes that VT the foreground console:
    # `console=tty12` leaves the box showing the kernel log, with the banner and
    # the press-a-key prompt rendered on a tty1 nobody is looking at and
    # nobody's keystrokes reach. The test asserts `fgconsole` is 1 so this
    # cannot come back. `console=ttyS0` is the same trap pointed at a cable: it
    # makes the serial port the primary console, so a panic on a box with
    # nothing plugged in goes nowhere at all instead of onto the monitor
    # somebody is standing in front of.
    # -------------------------------------------------------------------------

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
