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
#   * None of those panes is a shell. The middle column used to be, and is now
#     opencode pointed at the cluster's own Ollama -- the box already carries a
#     model, and nothing on the console could reach it. A prompt is Alt-F2 away,
#     on the tty2-tty6 gettys this module has always left alone, and the status
#     line says so.
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
  loomNamespace,
  loomChatModel,
  loomHostsJson,
  ...
}:
let
  cfg = config.loom;

  tmuxSocket = cfg.consoleSocket;

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
    set -g mouse on
    set -g escape-time 10
    # No `main-pane-width`/`select-layout` here: the layout is built by hand in
    # `create` below, because none of tmux's five preset layouts puts the main
    # pane at the BOTTOM -- `main-horizontal` puts it on top -- and the widest
    # pane is the one the operator types into.

    # The status line is the only place these key bindings are written down, and
    # the box ships no manual (documentation.nixos.enable = false in box.nix).
    # Alt-F2 earns its wording: no pane of this session is a shell any more, so
    # that key is the only route to a prompt and has to read as an offer rather
    # than a footnote.
    set -g status-style "bg=colour24,fg=white"
    set -g status-left "  LOOM  "
    set -g status-right " Ctrl-b d detach | Alt-F2 for a shell "
    set -g status-right-length 70
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
  loom-progress = pkgs.writeShellApplication {
    name = "loom-progress";
    runtimeInputs = with pkgs; [
      systemd
      kubectl
      coreutils
    ];
    text = ''
      unit=${lib.escapeShellArg cfg.progressUnit}
      namespace=${lib.escapeShellArg loomNamespace}

      printf '  Following %s. This pane is the live bring-up log,\n' "$unit"
      printf '  and becomes the pod list once Loom is up.\n'
      state="$(systemctl show --property=ActiveState --value "$unit" || echo unknown)"
      case "$state" in
        inactive)
          # Setup mode guards loom-fetch with ConditionPathExists, so on every
          # boot after the first the unit never runs at all.
          if [ -e ${lib.escapeShellArg "${loomRepoDir}/.loom-setup-complete"} ]; then
            printf '  First-time setup already completed -- this mode powers the box\n'
            printf '  off when it finishes. Boot the default "Loom" entry where the\n'
            printf '  appliance is to be used. Below is the log of that run.\n'
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
      # In the background, and deliberately not `exec`ed as it used to be: this
      # script has to outlive the log to notice the moment Loom is up, and exec
      # would replace the very process that watches for it.
      journalctl --no-hostname --lines=500 --follow --unit "$unit" &
      follower=$!

      # Two conditions, and both are needed.
      #
      # ActiveState alone is the honest definition of "up.sh returned": the unit
      # is Type=oneshot with RemainAfterExit (modes.nix), so it reads
      # `activating` for the hours of a bring-up, `active` only once up.sh has
      # exited 0, and `failed` if it did not -- which is exactly when the log
      # must stay on screen rather than being replaced by a pod list.
      #
      # The namespace check is what keeps first-time setup on its log. That mode
      # runs loom-fetch, which also reaches `active`, but it only populates
      # minikube's image store and deploys nothing -- so the namespace never
      # appears, the handover never fires, and the box powers itself off still
      # showing the fetch log. No second option to set, and no way for the two
      # modes to disagree about which pane they get.
      up() {
        [ "$(systemctl show --property=ActiveState --value "$unit")" = active ] \
          && kubectl --request-timeout=5s \
            get namespace "$namespace" >/dev/null 2>&1
      }

      until up; do
        sleep 5
      done

      kill "$follower" 2>/dev/null || true
      wait "$follower" 2>/dev/null || true

      printf '\n  Loom is up. This pane now shows its pods; the log is still\n'
      printf '  there, on an Alt-F2 console:\n\n'
      printf '    journalctl --unit %s --follow\n\n' "$unit"
      # Long enough to read the two lines above before k9s takes the screen: it
      # draws on the alternate buffer, so everything printed here is gone until
      # k9s exits.
      sleep 5

      exec ${lib.getExe loom-k9s}
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

      exec k9s --logoless --namespace "$namespace" --command pods
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
      #   self-signed-cert  The wildcard `CN=*.loom` that
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
      # Asking /v1/models rather than the namespace, because "the cluster is up"
      # is not the interesting condition here: opencode exits when its first
      # request fails, so what this has to wait for is Ollama serving the pinned
      # model over a connection that verifies.
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

      # The two halves are checked separately and named separately. Folded into
      # one predicate they produce the same silence for "the cluster has not
      # issued its certificate yet" and "Ollama is still pulling the model",
      # which are hours apart and fixed by different things.
      #
      # `grep` without -q, deliberately: this runs under `set -o pipefail`, and
      # -q makes grep exit on the first match, which hands the producer on its
      # left an EPIPE and fails the pipeline *because* the match was found. The
      # same trap is documented at length in tests/appliance.nix.
      ready() {
        if ! fetch_ca; then
          note "Waiting for the cluster's TLS certificate."
          return 1
        fi
        if ! curl --silent --fail --max-time 5 --cacert "$ca" "$endpoint/models" \
          | grep --fixed-strings "$model" >/dev/null; then
          note "Waiting for Ollama to serve $model."
          return 1
        fi
        return 0
      }

      until ready; do
        sleep 5
      done

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
      # Panes are addressed by pane ID (`%0`, `%3`, ...) rather than by index.
      # Indices follow layout POSITION and so are rewritten by every later split
      # -- splitting the top-left pane renumbers the bottom pane from 1 to 2 --
      # which makes any fixed `loom:0.N` in the middle of this function a bug
      # waiting for the next edit. IDs are assigned once and never move.
      create() {
        local main chat mon
        main=$("''${tm[@]}" new-session -d -x "$cols" -y "$lines" -s loom -n loom \
          -P -F '#{pane_id}' ${lib.getExe loom-progress})
        # -c so the assistant starts in the checkout: it is what an operator
        # asking about this box would want it looking at, and `respawn-pane`
        # below keeps a pane's start directory.
        chat=$("''${tm[@]}" split-window -v -l 60% -t "$main" \
          -c ${lib.escapeShellArg loomRepoDir} -P -F '#{pane_id}')
        mon=$("''${tm[@]}" split-window -h -t "$main" -P -F '#{pane_id}')

        # Plain shells first, the real commands only once every split is done. A
        # split takes its space from the pane it came from, so a pane created
        # early is resized by each later one -- and both loom-chat and loom-btop
        # draw TUIs that measure their pane once at startup and cannot take that
        # back. Hence the respawns into panes that have stopped moving.
        "''${tm[@]}" respawn-pane -k -t "$chat" ${lib.getExe loom-chat}
        "''${tm[@]}" respawn-pane -k -t "$mon" ${lib.getExe loom-btop}

        # A pane that died keeps its error on screen instead of collapsing the
        # layout, and anything the operator quit deliberately -- k9s with `:q`,
        # opencode with its own exit -- comes back with Ctrl-b `:respawn-pane`.
        # Set after the respawns above, which would otherwise have to kill panes
        # that `remain-on-exit` is keeping around.
        #
        # All three panes now, where it used to be two: the session no longer
        # contains a shell, so there is no pane left whose death is routine.
        "''${tm[@]}" set-option -p -t "$main" remain-on-exit on
        "''${tm[@]}" set-option -p -t "$chat" remain-on-exit on
        "''${tm[@]}" set-option -p -t "$mon" remain-on-exit on
        # Land in the assistant, not in the log.
        "''${tm[@]}" select-pane -t "$chat"
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
      loom-chat
      loom-btop
    ];

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
