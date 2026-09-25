# The appliance's two boot modes, as a NixOS specialisation.
#
# A specialisation produces a second system closure and a second systemd-boot
# entry, sharing almost the whole store closure with the default. So the two
# modes cost a boot menu entry rather than a second image.
#
#   `Loom`                    (default) offline. Serves DHCP and *.loom, starts
#                             Loom with --offline, and publishes it on the
#                             appliance address so visitors can reach it
#                             (network.nix's loom-expose).
#   `Loom (first-time-setup)` DHCP client. Builds and pulls every container
#                             image into minikube, once, then powers the box
#                             off -- after which it never needs the internet
#                             again.
#
# Those are the titles as they appear in the menu: NixOS builds each from
# branding.nix's `distroName` plus the specialisation's own attribute name, so
# renaming the specialisation below is what renames the entry.
#
# First-time setup is what removes the ~60 GB of container images from the USB
# stick: it writes them into minikube's store on the encrypted root, and run
# mode inherits them.
#
# The section banners below say "setup mode" because they mark branches keyed on
# `loom.mode`, which stays `setup` internally -- only the boot entry is renamed.
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

  # Offload Ollama to the GPU this box actually has. Named, not `--gpus all`:
  # up.sh takes `amd` or `nvidia` and rejects anything else, and the vendor is
  # what picks the values file, the device-plugin addon and the runtime image.
  #
  # Empty on a platform that declares no vendor, and on any image built with
  # --no-gpu -- nixos/default.nix forces the option to null for those, so this
  # is the only place either question is asked.
  gpuArgs = lib.optionalString (cfg.platform.gpuVendor != null) " --gpus ${cfg.platform.gpuVendor}";

  # What the platform says about this particular box, turned into up.sh flags.
  #
  # --disable-ai drops Ollama and open-webui *and* the indexing steps that call
  # them. Every platform without a GPU gets it, which today is all of them but
  # the EVO-X2: runsAiServices defaults to `gpuVendor != null`, because the
  # embedding step runs over every indexed file and a CPU never drains the
  # queue. The NUC 12 also says it outright, for memory.
  #
  # --scaling is the other two: it defaults to `meetsResourceMinimum`, and up.sh
  # refuses the two together (see the assertion below). It installs KEDA and
  # lets worker and reaper follow the queue depth instead of sitting at one
  # replica each on a box with twenty cores. It goes in both modes because the
  # KEDA images only reach minikube's store if the first-time fetch deployed
  # them -- run mode is air-gapped and cannot fetch what setup mode skipped.
  #
  # --no-resources is the NUC 12 alone.
  #
  # --no-resources rather than --skip-check_host_resources, and the difference
  # matters: the host check is not what actually stops an undersized box. Even
  # with the AI services gone the chart asks for ~19.4 GiB of memory *requests*,
  # so on a box with ~12 GiB allocatable the scheduler simply leaves most pods
  # Pending. Skipping the check would get past up.sh and then stall in
  # Kubernetes, which is a far more confusing failure than the one it replaced.
  # --no-resources strips the requests and limits, and skips the host check on
  # the way past (up.sh's check_host_resources returns early on it), so it is one
  # flag rather than two.
  #
  # What it costs is real and is documented on the console: with no limits,
  # nothing stops one container starving the rest, and a heavy indexing run on
  # this much memory ends in OOM kills rather than orderly eviction.
  platformArgs =
    lib.optionalString (!cfg.platform.runsAiServices) " --disable-ai"
    + lib.optionalString cfg.platform.runsAutoscaling " --scaling"
    + lib.optionalString (!cfg.platform.meetsResourceMinimum) " --no-resources";

  # How long setup mode leaves its closing message on screen before powering the
  # box off. Long enough for whoever walks past to read why the box is going
  # down and to cancel it if they want the box up, short enough that nobody
  # waits for it. The run is already marked complete by then, so a cancel costs
  # nothing but the poweroff.
  setupPoweroffGrace = 60;

  # Hand the boot menu back to run mode, and take first-time setup out of it.
  #
  # Run once, at the end of a successful fetch. After it the menu has a single
  # Loom entry, so no boot of this box ever needs the operator to choose again --
  # which is the point: the default entry serves DHCP and wildcard *.loom on the
  # appliance NIC, and the wrong pick puts that on somebody else's network.
  #
  # Root-only, because it writes the ESP. loom-fetch below runs as the operator
  # and calls this through sudo, the same way it reaches `systemctl poweroff`.
  loom-promote-boot-entry = pkgs.writeShellApplication {
    name = "loom-promote-boot-entry";
    runtimeInputs = with pkgs; [
      coreutils
      findutils
      gawk
    ];
    text = ''
      entries=/boot/loader/entries
      conf=/boot/loader/loader.conf

      # -----------------------------------------------------------------------
      # 1. Point `default` back at run mode.
      #
      # This half can go through the bootloader builder, unlike the installer's
      # own selection (install.sh `select_setup_entry`), and the asymmetry is
      # worth knowing: the builder decides which entry is default by comparing
      # DEFAULT-CONFIG against the *main* toplevel only, and calls
      # write_loader_conf() with no specialisation. The run closure is that main
      # toplevel, so handing it over works and writes
      # `default nixos-generation-<N>.conf` itself. Handing it a specialisation
      # would match nothing and leave loader.conf untouched, which is exactly why
      # the installer has to write that line by hand.
      #
      # It also rewrites every entry, including the specialisation one that step
      # 2 removes -- hence this order. Reversed, a power cut between the two
      # would leave `default` naming a file that no longer exists.
      #
      # NIXOS_INSTALL_BOOTLOADER=1 keeps it on the `bootctl install` path rather
      # than the version-comparing `update` path, matching what the installer
      # already did to this ESP. It cannot disturb the NVRAM order fix_boot_order
      # set: box-hardware.nix sets canTouchEfiVariables = false, and that is what
      # puts --no-variables on every bootctl call the builder makes.
      # -----------------------------------------------------------------------
      NIXOS_INSTALL_BOOTLOADER=1 \
        /nix/var/nix/profiles/system/bin/switch-to-configuration boot

      # -----------------------------------------------------------------------
      # 2. Remove the first-time-setup entry.
      #
      # The glob is deliberately narrow -- it carries both `nixos-generation-`
      # and `-specialisation-`, so nothing else living in this directory can be
      # caught by it. systemd-boot's own `Reboot Into Firmware Interface` is
      # synthesised by the loader rather than stored here, so it survives
      # regardless; the scoping is what makes that true by construction.
      #
      # None is not an error: this runs by hand as well as from loom-fetch (see
      # systemPackages below), and a re-run after a successful promotion should
      # report that rather than fail. The state check in step 3 is what decides
      # whether "nothing to remove" means "already done" or "something is wrong",
      # so it runs either way.
      #
      # Several *is* an error -- it means the entry layout changed under us, and
      # guessing which to delete is not a decision to make on an appliance.
      # -----------------------------------------------------------------------
      mapfile -t setup_entries < <(
        find "$entries" -maxdepth 1 -type f \
          -name 'nixos-generation-*-specialisation-*.conf' | sort
      )
      case "''${#setup_entries[@]}" in
        0) echo "[-] No first-time-setup entry to remove; checking the menu anyway." ;;
        1) rm -- "''${setup_entries[0]}" ;;
        *)
          echo >&2 "[!] Found ''${#setup_entries[@]} specialisation entries in $entries, expected one."
          echo >&2 "[!] Leaving the boot menu alone rather than guessing which to remove."
          exit 1
          ;;
      esac

      # -----------------------------------------------------------------------
      # 3. Check the menu is what it now claims to be: one entry, and `default`
      #    names it. Nothing else verifies this, and the failure it guards
      #    against -- a box that boots to a menu with no valid default -- is one
      #    nobody would enjoy meeting in the field.
      # -----------------------------------------------------------------------
      remaining="$(find "$entries" -maxdepth 1 -type f -name 'nixos-*.conf' | wc -l)"
      default="$(awk '$1 == "default" { print $2 }' "$conf")"
      if [ "$remaining" -ne 1 ] || [ ! -f "$entries/$default" ]; then
        echo >&2 "[!] Boot menu is not in the expected state: $remaining entries, default '$default'."
        exit 1
      fi

      echo "[*] Boot menu promoted: one entry, $default."
    '';
  };

  # Loom takes a long time to come up; skaffold's own offline profile allows
  # six hours (skaffold.yaml:384). Never let systemd shoot it in the head.
  commonService = {
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      User = loomUser;
      Group = "users";
      WorkingDirectory = loomRepoDir;
      TimeoutStartSec = "infinity";
      # Journal only. These used to also go to /dev/console, which -- with no
      # `console=` on the command line -- meant the active VT, so hours of
      # bring-up log painted over the login screen. The first pane of
      # console.nix's session follows this journal instead, which is where it is
      # actually readable.
      StandardOutput = "journal";
      StandardError = "journal";
    };
    after = [
      "docker.service"
      "loom-seed-repo.service"
      "network-online.target"
    ];
    requires = [
      "docker.service"
      "loom-seed-repo.service"
    ];
    wants = [ "network-online.target" ];
    # Where minikube and skaffold keep their state.
    #
    # box.nix sets both in `environment.sessionVariables`, which is written into
    # /etc/profile and therefore reaches login shells and nothing else -- so the
    # units below ran without them and minikube fell back to `$HOME/.minikube`.
    # The result was two state directories for one box: the cluster these units
    # built lived in /home/loom/.minikube, while every `minikube` command an
    # operator typed at the console addressed the empty repo-relative one and
    # reported no cluster at all.
    #
    # Inherited from the session variables rather than restated, because the
    # whole point is that the two agree; the values themselves belong next to
    # the comment in box.nix explaining why they are repo-relative.
    environment = {
      inherit (config.environment.sessionVariables) MINIKUBE_HOME SKAFFOLD_HOME;
    };
    path = [
      # `sudo` is a setuid wrapper in /run/wrappers/bin rather than a package, so
      # no entry in `loom.toolchain` can supply it. A login shell gets this
      # directory for free; a unit does not. up.sh's `validate_environment`
      # refuses to run without it (up.sh:407), and setup mode's loom-fetch below
      # calls it twice directly.
      "/run/wrappers"
      # Not in `loom.toolchain`: the docker module already puts a client in
      # systemPackages, and taking the package from the module rather than from
      # `pkgs` guarantees the unit's client matches the daemon it talks to.
      config.virtualisation.docker.package
    ]
    ++ cfg.toolchain
    ++ cfg.entrypoints;
  };
in
{
  options.loom.entrypoints = lib.mkOption {
    type = lib.types.listOf lib.types.package;
    internal = true;
    default = [ ];
    description = ''
      The `loom-up` / `loom-down` wrappers, as set by box.nix.

      They have to be on the PATH of the units below explicitly. Being in
      `environment.systemPackages` puts them in the operator's interactive
      shell but not in a systemd unit's environment, so without this the
      appliance boots and `loom.service` dies immediately with
      "exec: loom-up: not found".
    '';
  };

  options.loom.toolchain = lib.mkOption {
    type = lib.types.listOf lib.types.package;
    internal = true;
    default = [ ];
    description = ''
      Every package up.sh needs at runtime, as set by box.nix.

      Shared with `environment.systemPackages` rather than restated here. A
      unit's PATH is built solely from its `path` list plus a minimal default
      (coreutils, findutils, gnugrep, gnused, systemd); `/run/current-system/sw/bin`
      is never on it. So a package that is only in systemPackages is absent from
      the units below, and the failure looks like a broken up.sh rather than a
      broken PATH.
    '';
  };

  options.loom.mode = lib.mkOption {
    type = lib.types.enum [
      "run"
      "setup"
    ];
    default = "run";
    description = ''
      Which appliance mode this system closure is. `run` is the default boot
      entry; `setup` is generated as a specialisation of it.

      Internal, and deliberately not renamed alongside the boot entry: this is
      what network.nix and the branches below switch on, and no operator ever
      sees it. The menu says `Loom (first-time-setup)`.
    '';
  };

  config = lib.mkMerge [
    # -------------------------------------------------------------------------
    # Both modes
    # -------------------------------------------------------------------------
    {
      assertions = [
        {
          assertion = !(cfg.platform.runsAutoscaling && !cfg.platform.meetsResourceMinimum);
          message =
            "nixos: platform '${cfg.platform.id}' sets runsAutoscaling with "
            + "meetsResourceMinimum = false. up.sh rejects --scaling alongside "
            + "--no-resources: the scaling values file enables a resource quota that "
            + "requires requests on every pod, and --no-resources removes them. The "
            + "box would fail bring-up with no remote access to see it. Drop one.";
        }
      ];

      # Keep Ollama at one replica on a box whose GPU there is only one of.
      #
      # charts/values-scaling.yaml turns on Ollama's HPA -- two replicas at 80%
      # CPU -- which is written for a cluster with more than one GPU node. Here
      # `--gpus <vendor>` makes the pod request `<vendor>.com/gpu: 1`
      # (charts/values-amd-gpu.yaml), the node advertises exactly one, and the
      # second replica is unschedulable for as long as the HPA wants it. It
      # never arrives, so it cannot help; and because Ollama requests only half
      # a core, any inference at all puts it over the threshold, so this is the
      # normal case rather than an edge one.
      #
      # What it costs beyond the wasted pod is the console. loom-ready counts
      # ready against desired over workloads (ready/loom_ready/cluster.py), and
      # `Unschedulable` is a pod condition rather than one of the container
      # waiting reasons it can name -- so the bar would sit short of the end
      # through every indexing run with nothing on screen saying why.
      #
      # Only the HPA goes. Worker, reaper, tika and gotenberg scale as the
      # values file intends; they are bound by cores and memory, which this box
      # has.
      loom.chartOverrides =
        lib.mkIf
          (cfg.platform.runsAutoscaling && cfg.platform.runsAiServices && cfg.platform.gpuVendor != null)
          {
            ollama.hpa.enabled = false;
          };
    }

    # -------------------------------------------------------------------------
    # Run mode
    # -------------------------------------------------------------------------
    (lib.mkIf (cfg.mode == "run") {
      specialisation.first-time-setup.configuration = {
        loom.mode = lib.mkForce "setup";
        # The specialisation's *name* is the boot entry: NixOS builds the title
        # as distroName + specialisation, so this attribute is what an operator
        # reads in the menu. The tag only shows up in the entry's second line
        # and in `nixos-version`; it matches so the two cannot drift.
        system.nixos.tags = [ "first-time-setup" ];
      };

      loom.progressUnit = "loom.service";

      # Normal operation: the box holds indexed data and is expected to be left
      # alone, so pulling the key is a deliberate act and must act on it.
      loom.keyGuard.action = "poweroff";

      # Run mode has nothing to say on its way up: the disk unlocks from the
      # stick without a prompt, everything an operator needs is on the login
      # screen afterwards (box.nix's `loom-info`), and bring-up itself is
      # readable in the first pane of console.nix's session. So let
      # branding.nix's splash own the screen instead of a scroll of kernel
      # messages -- the plymouth module contributes `splash` itself, `quiet` is
      # what silences the log.
      #
      # Deliberately here rather than in box-hardware.nix: a specialisation
      # *adds* to its parent's kernel command line and cannot subtract from it,
      # so a `quiet` set for both modes could never be taken back for setup.
      #
      # The same asymmetry is why --debug has to be asked about *here* rather
      # than answered in debug.nix: a list element cannot be removed by a later
      # module either, so a debug build has to never acquire these in the first
      # place. debug.nix adds `plymouth.enable=0` on top, which is the other
      # half of taking the splash off a boot that is going wrong.
      boot.kernelParams = lib.mkIf (!cfg.debug.enable) [
        "quiet"
        "udev.log_level=3"
      ];

      systemd.services.loom = lib.mkMerge [
        commonService
        {
          description = "Loom (offline)";
          wantedBy = [ "multi-user.target" ];
          after = [ "dnsmasq.service" ];
          # Deliberately no --expose. That flag runs `minikube tunnel`, which
          # on the docker driver forwards each service port over the system
          # `ssh` client; network.nix's loom-expose does the same job with a
          # DNAT rule instead. The two are alternatives rather than layers --
          # DNAT happens in nat PREROUTING, ahead of the routing decision that
          # would hand a packet to a local listener, so a tunnel socket on the
          # appliance address would never see one.
          script = ''
            exec loom-up --offline${gpuArgs}${platformArgs}
          '';
        }
      ];
    })

    # -------------------------------------------------------------------------
    # Setup mode
    # -------------------------------------------------------------------------
    (lib.mkIf (cfg.mode == "setup") {
      loom.progressUnit = "loom-fetch.service";

      # Only meaningful in this mode, and only ever run by hand after the
      # automatic call below failed -- see the comment there. Run mode has no
      # setup entry left to promote.
      environment.systemPackages = [ loom-promote-boot-entry ];

      # Warn only. This mode runs once, in the lab, with internet and nothing
      # secret on the box yet, and loom-fetch below takes hours -- a trip on a
      # glitching USB port would throw all of it away for no security gain.
      loom.keyGuard.action = "warn";

      # No splash in this mode, and no `quiet` either (the run-mode branch above
      # is what sets that). Fetching every container image takes hours, and a
      # still logo over all of it would be actively misleading. What actually
      # reports progress is the first pane of console.nix's session, which
      # follows loom-fetch below; this keeps the boot itself honest as well.
      boot.kernelParams = [ "plymouth.enable=0" ];

      systemd.services.loom-fetch = lib.mkMerge [
        commonService
        {
          description = "Loom setup: build and pull all container images";
          wantedBy = [ "multi-user.target" ];

          # Hours of work. Do not silently redo it because someone rebooted.
          unitConfig.ConditionPathExists = "!${loomRepoDir}/.loom-setup-complete";

          script = ''
            echo "[*] Loom setup mode: populating minikube's image store."
            echo "[*] This needs internet and takes a long time. Press a key at"
            echo "[*] the console; the first pane of the session is this log."

            # --delete tears the deployment down again afterwards: the goal here
            # is a warm image store, not a running stack. Documentation/
            # installation.md:107 prescribes exactly this before going offline.
            loom-up --offline --delete${gpuArgs}${platformArgs}

            touch ${loomRepoDir}/.loom-setup-complete

            # Marked complete *before* the promotion below, and the order is
            # deliberate. A failed promotion must not throw away hours of fetch:
            # the box reboots into setup mode, skips the fetch on the marker, and
            # an operator can re-run the promotion by hand from an Alt-F2 console
            # -- which is why it is in systemPackages below as well.
            #
            # sudo for the same reason the poweroff below needs it: this unit
            # runs as the operator, and a service has no logind session for
            # polkit's allow_active to key on. An absolute path rather than the
            # bare name, because sudo does not carry this unit's PATH through to
            # the child it starts.
            sudo ${lib.getExe loom-promote-boot-entry}

            echo "[*] Image store populated. This box never needs the internet again."
            echo "[*] The boot menu now holds one entry, and it is run mode."
            echo "[*] Powering off in ${toString setupPoweroffGrace}s. Move the box to where it will"
            echo "[*] be used before powering it on again: run mode serves DHCP and *.loom"
            echo "[*] on the appliance NIC, and that must not land on the network this"
            echo "[*] fetch ran over."
            echo "[*] To keep it up instead, from an Alt-F2 console:"
            echo "[*]   sudo systemctl stop loom-fetch"
            sleep ${toString setupPoweroffGrace}

            # `sudo`, because this unit runs as the loom user and a systemd
            # service has no logind session -- polkit's allow_active never
            # applies to one, so a bare `systemctl poweroff` here fails with
            # "Interactive authentication required". box.nix already sets
            # `wheelNeedsPassword = false` for up.sh, which needs the same thing.
            #
            # --no-block: the shutdown transaction stops this very unit, so a
            # blocking call would be waiting on itself.
            #
            # Only reached on success. NixOS runs `script` under `set -e`, so a
            # failed fetch exits non-zero long before this and leaves the box up
            # with its log on screen, which is the whole point of a failure.
            sudo systemctl --no-block poweroff
          '';
        }
      ];
    })
  ];
}
