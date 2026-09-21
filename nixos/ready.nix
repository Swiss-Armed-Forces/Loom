# Is Loom up yet, and how far along is it.
#
# A bring-up on these boxes is tens of minutes to hours, and until now nothing on the
# console answered that question. The journal says what is happening rather than how much
# is left; k9s appears when up.sh returns -- which is well before the pods are Ready -- and
# shows twenty-five rows with no total; and the pre-login banner said nothing about the
# cluster at all.
#
# So one unit works the answer out and writes it into /run/loom/ready, and three things
# draw it:
#
#   * console.nix's first pane, as a bar pinned below the bring-up log (loom_ready/pane.py).
#   * console.nix's tmux status line, as a segment that outlives the pane -- which is what
#     shows a box that goes degraded on a Tuesday.
#   * box.nix's banner, as one line, repainted when the stage changes.
#
# One publisher rather than three, for two reasons. The status line refreshes on a timer
# out of the tmux server, so it has to be a file read: a `kubectl` there could hang the
# session on a cluster that is not answering. And three pollers would put three times the
# load on an API server during exactly the window the box is at its busiest.
#
# Run mode only. Setup mode is a DHCP client pulling container images for hours with no
# cluster to ask and none coming (modes.nix), which is also why the pane is given no state
# directory there and draws the fetch log alone.
{
  config,
  lib,
  pkgs,
  loomUser,
  loomNamespace,
  ...
}:
let
  cfg = config.loom.ready;

  # Everything the program shells out to, baked into the wrapper rather than left to the
  # unit's PATH. A unit's PATH is its own `path` plus a minimal default and never
  # /run/current-system/sw/bin, which is the drift that once shipped a box whose
  # loom.service died on `awk: command not found` (box.nix, `loom.toolchain`). Here the
  # same list also has to serve the operator typing `loom-ready` at an Alt-F2 prompt and
  # the tmux server spawning it for the status line, neither of which is a unit at all.
  runtimeInputs = with pkgs; [
    kubectl
    systemd # systemctl, for the bring-up unit's ActiveState
    coreutils
  ];

  loom-ready = pkgs.python3Packages.buildPythonApplication {
    pname = "loom-ready";
    version = "0.1.0";
    src = ./ready;
    pyproject = true;

    build-system = [ pkgs.python3Packages.setuptools ];
    # The panel, the bar and the pane (loom_ready/render.py, loom_ready/pane.py).
    dependencies = [ pkgs.python3Packages.rich ];
    nativeCheckInputs = [ pkgs.python3Packages.pytest ];

    # The rules that decide what the bar shows -- which workloads count, what a Job's
    # completion means, when a box is ready -- are pure functions over the documents
    # kubectl produces, precisely so they can be exercised here. A mistake in them fails
    # the image build in seconds rather than at a box somebody has driven to.
    checkPhase = ''
      runHook preCheck
      # Appended rather than assigned, so the paths the python setup hook exported for
      # this package's dependencies survive; `tests` as well, because the suite imports
      # its doubles by module name the way pytest's rootdir insertion would.
      PYTHONPATH=$PWD:$PWD/tests''${PYTHONPATH:+:$PYTHONPATH} pytest tests -q
      runHook postCheck
    '';

    makeWrapperArgs = [
      "--prefix PATH : ${lib.makeBinPath runtimeInputs}"
      # The defaults for a `loom-ready` typed by hand. The units and the console pass
      # these explicitly; what this covers is the operator on an Alt-F2 console, who
      # should not have to know the namespace -- and must not get a stale guess at it if
      # NAMESPACE in vars.sh ever changes.
      "--set LOOM_READY_STATE_DIR ${lib.escapeShellArg cfg.stateDir}"
      "--set LOOM_READY_NAMESPACE ${lib.escapeShellArg loomNamespace}"
      "--set LOOM_READY_UNIT ${lib.escapeShellArg config.loom.progressUnit}"
      "--set LOOM_READY_KUBECONFIG ${lib.escapeShellArg cfg.kubeconfig}"
    ];

    meta.mainProgram = "loom-ready";
  };
in
{
  options.loom.bannerRefresh = lib.mkOption {
    type = lib.types.package;
    internal = true;
    description = ''
      `loom-banner-refresh`: rewrite the pre-login banner and redraw it, if and only if
      the console is still showing it.

      Declared here and set in box.nix, the way `loom.progressUnit` is declared in
      console.nix and set in modes.nix. The publisher below runs it whenever the
      bring-up reaches a new stage; box.nix owns what it does, including the check that
      keeps it from blanking the screen under somebody who has logged in.
    '';
  };

  options.loom.ready = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      internal = true;
      description = ''
        Publish readiness on this box.

        On in every run-mode image. An option rather than a literal so the VM tests can
        build a box without it, and so that a box being debugged by hand can be told to
        stop polling its own cluster.

        It does not gate the readers. The status line and the banner print nothing when
        there is no record to read, and the pane falls back to the log alone -- which is
        the same path setup mode takes, so switching this off leaves the console exactly
        as it was before any of this existed rather than leaving a hole in it.
      '';
    };

    package = lib.mkOption {
      type = lib.types.package;
      internal = true;
      readOnly = true;
      description = ''
        `loom-ready`: the publisher, the pane, the status segment and the one-shot.

        An option rather than a literal in console.nix, for the same reason
        `loom.consoleMouse.package` is one: the thing is defined beside the unit that
        runs it, and console.nix names it once.
      '';
    };

    stateDir = lib.mkOption {
      type = lib.types.str;
      default = "/run/loom/ready";
      internal = true;
      description = ''
        Where readiness is published, for the pane, the status line and the banner.

        0755 rather than console.nix's 0700 /run/loom, and deliberately: two of the three
        readers are spawned by the operator's tmux server and the third is a shell script
        in the banner's closure, so none of them can be handed a root-only file. What is
        in here is replica counts and workload names -- see loom_ready/state.py.

        On tmpfs, so no claim about a cluster survives the boot that made it.
      '';
    };

    interval = lib.mkOption {
      type = lib.types.numbers.positive;
      default = 5;
      internal = true;
      description = ''
        Seconds between polls.

        Fast enough that the bar moves while somebody is watching it, slow enough to be
        nothing next to a bring-up. Every call carries `--request-timeout=5s`, so a
        cluster that is not answering costs a timeout per tick rather than a wedged loop.
      '';
    };

    kubeconfig = lib.mkOption {
      type = lib.types.str;
      default = "/home/${loomUser}/.kube/config";
      internal = true;
      description = ''
        The operator's kubeconfig, borrowed by a unit that runs as root -- the same
        arrangement usb-ingest.nix uses to read the cluster CA. minikube writes its client
        certificates into the operator's home and root can read them.
      '';
    };
  };

  config = lib.mkMerge [
    {
      loom.ready.package = loom-ready;
    }

    (lib.mkIf (cfg.enable && config.loom.mode == "run") {
      environment.systemPackages = [ loom-ready ];

      # Readable by the operator, unlike the rest of /run/loom: see `stateDir`.
      systemd.tmpfiles.rules = [
        "d ${cfg.stateDir} 0755 root root -"
      ];

      systemd.services.loom-ready = {
        description = "Publish how far Loom's bring-up has got";
        wantedBy = [ "multi-user.target" ];

        # Deliberately NOT `after = [ "loom.service" ]`. That unit is Type=oneshot with
        # RemainAfterExit, so ordering after it means waiting for up.sh to *finish* --
        # which is the entire window this exists to describe. The publisher starts with
        # the box and reports `waiting` until there is a cluster to ask.
        serviceConfig = {
          Type = "simple";
          ExecStart = lib.concatStringsSep " " [
            (lib.getExe loom-ready)
            "--publish"
            "--state-dir ${lib.escapeShellArg cfg.stateDir}"
            "--namespace ${lib.escapeShellArg loomNamespace}"
            "--unit ${lib.escapeShellArg config.loom.progressUnit}"
            "--kubeconfig ${lib.escapeShellArg cfg.kubeconfig}"
            "--interval ${toString cfg.interval}"
            # What gets the login screen redrawn when the stage changes. box.nix owns the
            # guard that keeps it from repainting over somebody's session.
            "--on-change ${lib.getExe config.loom.bannerRefresh}"
          ];

          # Journal only, like every other Loom unit: with no `console=` on the kernel
          # command line, "console" is the VT the operator is looking at, and this would
          # paint over the session drawing its own output.
          StandardOutput = "journal";
          StandardError = "journal";

          # A display that has stopped is worse than no display -- the readers drop a
          # record they have not seen updated in three polls, so a dead publisher takes
          # the bar, the segment and the banner line with it rather than freezing them.
          Restart = "always";
          RestartSec = 5;
        };
      };
    })
  ];
}
