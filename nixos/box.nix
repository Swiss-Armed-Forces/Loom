# The Loom appliance system.
#
# Everything up.sh mutates on the host imperatively is declared here instead, so
# that a `nixos-rebuild` cannot silently revert it. The appliance therefore runs
# up.sh with those two steps skipped -- see the `loom-up` wrapper below.
{
  config,
  lib,
  pkgs,
  loomHostsJson,
  minikubeIp,
  loomUser,
  loomRepoDir,
  recoveryPassphraseFile,
  tag,
  ...
}:
let
  # How long the box survives the key being pulled, in the same two numbers
  # key-guard.nix multiplies. Restating "10 seconds" in the banner would drift
  # the moment either is tuned.
  keyGuardGrace = config.loom.keyGuard.intervalSec * config.loom.keyGuard.graceTicks;

  # How long after boot loom-banner-repaint keeps watching the console, and how
  # often it looks. The console stops being resized within a few seconds of the
  # last font change; the window is generous against a slow DRM driver, and the
  # unit exits the moment somebody logs in.
  bannerRepaintWindow = 60;
  bannerRepaintInterval = 2;

  # Only run mode ever has an access point -- see wifi.nix -- so first-time setup
  # must not advertise one.
  showWifi = config.loom.wifi.enable && config.loom.mode == "run";

  # What a phone's camera expects, and what Android and iOS both emit from their
  # own "share this network". No escaping here and none needed: wifi.nix asserts
  # that the SSID and the passphrase contain nothing outside [A-Za-z0-9_-], which
  # excludes every character this format reserves. That is not tidiness -- the
  # escape for a reserved character is a backslash, and agetty eats backslashes
  # out of an issue file before anyone gets to see them.
  wifiUri = "WIFI:T:WPA;S:${config.loom.wifi.ssid};P:${config.loom.wifi.psk};;";

  # Ship a wrapper rather than only documenting the flags. Running bare `up.sh`
  # here is actively harmful: `setup_system` writes /etc/sysctl.d/99-loom.conf
  # that NixOS ignores, and `install_host_entries` replaces the /etc/hosts store
  # symlink with a mutable copy (up.sh:963-977) -- undoing the declarative work
  # this module exists to do. writeShellApplication also shellchecks at build
  # time, matching the rest of the repo.
  loom-up = pkgs.writeShellApplication {
    name = "loom-up";
    runtimeInputs = with pkgs; [
      minikube
      coreutils
    ];
    text = ''
      cd ${lib.escapeShellArg loomRepoDir}

      # networking.hosts pins *.loom at a fixed address; if minikube ever lands
      # somewhere else, fail loudly instead of serving a silently broken stack.
      if ip="$(minikube ip 2>/dev/null)" && [ "$ip" != ${lib.escapeShellArg minikubeIp} ]; then
        echo >&2 "[!] minikube is at $ip but *.loom is pinned to ${minikubeIp} in /etc/hosts."
        echo >&2 "[!] Run 'minikube delete' and retry, or rebuild the image with a matching IP."
        exit 1
      fi

      exec ./up.sh --skip-setup_system --skip-install_host_entries "$@"
    '';
  };

  loom-down = pkgs.writeShellApplication {
    name = "loom-down";
    text = ''
      cd ${lib.escapeShellArg loomRepoDir}
      exec ./up.sh --down "$@"
    '';
  };

  # The console banner, as a command. Everything it prints is also what the
  # login screen shows: `loom-issue.service` below captures this output into
  # /run/issue.d. One generator rather than two copies that drift -- and the
  # operator can re-run it by hand once the console session has covered the
  # boot-time copy.
  #
  # Produces no backslashes on purpose: agetty interprets them as issue-file
  # escapes. The passphrase charset (install.sh:225-231) cannot contain one, and
  # neither can the art `loom-eyes` draws. The colour below is not an exception:
  # `$'\033'` is a literal ESC byte by the time it is written, and agetty(8)
  # only ever reads a backslash as the start of an escape of its own.
  # Writing the banner into the issue directory, as a script rather than inline,
  # because two units run it: loom-issue.service at boot, and
  # loom-banner-repaint.service once the console has stopped resizing under it.
  writeIssue = pkgs.writeShellScript "loom-write-issue" ''
    set -euo pipefail
    ${pkgs.coreutils}/bin/mkdir -p /run/issue.d

    # Rendered through a temporary file so agetty can never read a
    # half-written banner from a getty that respawns mid-write.
    #
    # LOOM_INFO_COLOR=vt because the redirection hides the console from
    # loom-info: without it the one screen the colour exists for -- the
    # login prompt nobody has touched yet -- would be the one that renders
    # the eyes plain.
    #
    # Deliberately no measurement of the console here. This used to read
    # `stty size </dev/tty1` and hand loom-info a row budget to trim itself to,
    # and there is no point in the boot at which that reading stays true -- see
    # the banner's own comment. It produced a box with no mark and no QR code on
    # a console with room for both.
    LOOM_INFO_COLOR=vt ${loom-info}/bin/loom-info \
      >/run/issue.d/50-loom.issue.tmp
    ${pkgs.coreutils}/bin/mv /run/issue.d/50-loom.issue.tmp \
      /run/issue.d/50-loom.issue
  '';

  # Sits beside `loom-info` and does an unrelated job: that one draws the banner
  # the login screen shows, this one reports the hardware underneath it.
  #
  # The script is cicd/platform_info.sh, shared verbatim with the devenv command
  # of the same name, because the box it most needs to run on is one that is not
  # running Loom yet -- see the header there. What the appliance adds is the
  # declared half: the platform's own claims, so the report can say where the
  # hardware disagrees with the image rather than leaving somebody to compare two
  # screens by eye. Passed as environment variables through the same `--set`
  # route installer.nix already uses for the stick's scripts.
  #
  # writeShellApplication runs shellcheck at build time, so a mistake in that
  # file fails `nix-build -A box` rather than appearing on a console in the field.
  loom-platform-info = pkgs.writeShellApplication {
    name = "loom-platform-info";
    runtimeInputs =
      with pkgs;
      [
        coreutils
        gnused
        gnugrep
        pciutils # lspci
        usbutils
        iw # the AP-mode probe, which is the whole point on a --wifi box
        nvme-cli
        util-linux # lsblk
        systemd # udevadm, for ID_PATH
        jq # --json only; the text report needs none of this
      ]
      ++ lib.optional (config.loom.platform.gpuVendor == "amd") pkgs.rocmPackages.rocm-smi;
    text = ''
      export LOOM_PLATFORM_ID=${lib.escapeShellArg config.loom.platform.id}
      export LOOM_PLATFORM_DESCRIPTION=${lib.escapeShellArg config.loom.platform.description}
      export LOOM_PLATFORM_NET_MATCH=${
        lib.escapeShellArg (
          lib.concatStringsSep ", " (lib.mapAttrsToList (k: v: "${k}=${v}") config.loom.platform.netMatch)
        )
      }
      export LOOM_PLATFORM_WIFI_MATCH=${
        lib.escapeShellArg (
          lib.optionalString (config.loom.platform.wifiMatch != null) (
            lib.concatStringsSep ", " (lib.mapAttrsToList (k: v: "${k}=${v}") config.loom.platform.wifiMatch)
          )
        )
      }
      export LOOM_PLATFORM_GPU_VENDOR=${
        lib.escapeShellArg (
          lib.optionalString (config.loom.platform.gpuVendor != null) config.loom.platform.gpuVendor
        )
      }

      ${builtins.readFile ../cicd/platform_info.sh}
    '';
  };

  loom-info = pkgs.writeShellApplication {
    name = "loom-info";
    runtimeInputs = [ pkgs.coreutils ] ++ lib.optional showWifi pkgs.qrencode;
    text = ''
      # The eyes in the logo's amber, so the login screen agrees with the boot
      # splash and the installer menu instead of being the one place the mark
      # is monochrome.
      #
      # Two sequences, because they answer to different consoles:
      #
      #   ESC ] P nrrggbb   Redefines a Linux VT palette entry. The only way to
      #                     reach the exact colour -- console_codes(4) shoehorns
      #                     even a 24-bit 38;2;r;g;b into the 16 basic ones, so
      #                     a bare ESC[33m lands on #aa5500. VT only: the same
      #                     page warns that xterm hangs on it until somebody
      #                     presses return.
      #   ESC [ 33m         Selects that entry. Safe on any terminal.
      #
      # Indices 3 and B are both set because bold promotes one to the other,
      # and because branding.nix loads a 512-glyph font: setfont(8) notes that
      # past 256 glyphs the console spends its intensity bit on glyph selection
      # and drops to 8 colours, so which of the two any given VT lands on is
      # not worth predicting. Setting both makes it moot.
      #
      # There is deliberately no reset. The VT looks the palette up when it
      # paints, not when the character was written, so restoring it would
      # recolour the eyes already on screen back to mustard.
      palette=""
      amber=""
      reset=""
      # loom-issue.service sets this: it captures this output into a file, so
      # the checks below cannot see the console, but that file is read only by
      # agetty and agetty is only ever on a VT here.
      if [ "''${LOOM_INFO_COLOR:-auto}" = vt ]; then
        palette=$'\033]P3${config.loom.branding.amberRgb}\033]PB${config.loom.branding.amberRgb}\033]P7ffffff'
      elif [ -t 1 ]; then
        # A pts -- a tmux pane of console.nix's session -- gets the selector but
        # not the redefinition, and still comes out amber: the VT underneath it
        # had its palette rewritten by the banner at boot.
        case "$(tty 2>/dev/null || true)" in
          /dev/tty[0-9]*)
            palette=$'\033]P3${config.loom.branding.amberRgb}\033]PB${config.loom.branding.amberRgb}\033]P7ffffff'
            ;;
          *) ;;
        esac
      fi
      # Keyed on stdout so that `loom-info > banner.txt` stays readable.
      if [ "''${LOOM_INFO_COLOR:-auto}" = vt ] || [ -t 1 ]; then
        amber=$'\033[33m'
        reset=$'\033[0m'
      fi

      # The banner is always printed whole.
      #
      # It used to measure the console and drop the mark, then the QR code, to
      # fit. That was wrong, and wrong in a way worth recording: there is no
      # moment at which the row count can be measured and trusted. The console
      # is resized several times during boot -- the kernel's built-in font, then
      # Cozette, then the DRM driver's reset, then Cozette again -- and a reading
      # taken between any two of them is a reading of a screen that no longer
      # exists by the time agetty paints. Ordering the measurement after the font
      # unit was not enough; it only moved the race. What it produced on the box
      # was a banner with no mark and no QR code on a console with room for both.
      #
      # So: print everything, and fix the geometry problem where it actually is
      # -- loom-banner-repaint.service redraws this once the resizing has
      # stopped. A banner that is genuinely taller than the final screen loses
      # its top rows, which is the mild, visible failure this replaced a silent
      # one with.
      #
      # The mark the boot splash just showed, in the form a console can hold.
      # A command rather than a here-document so that the banner, the issue and
      # the installer menu all draw the same art from one place. See
      # branding.nix.
      printf '\n'
      printf '%s%s' "$palette" "$amber"
      ${lib.getExe config.loom.branding.eyes}
      printf '%s' "$reset"
      printf '\n  Loom appliance -- %s\n' ${lib.escapeShellArg tag}
      printf '  %s\n' ${lib.escapeShellArg config.loom.platform.description}
      ${lib.optionalString (!config.loom.platform.runsAiServices) ''
        printf '  No AI on this box: no summaries, translation or semantic search.\n'
      ''}
      ${lib.optionalString (!config.loom.platform.meetsResourceMinimum) ''
        printf '  Below the documented memory minimum -- running without resource limits.\n'
      ''}
      if [ -r /etc/loom/network.conf ]; then
        # shellcheck disable=SC1091
        . /etc/loom/network.conf
        # The wired port, which is not the same thing as the interface holding
        # the address once the access point bridges the two. See network.nix.
        printf '  Plug a laptop into %s and browse https://frontend.loom\n' \
          "''${LOOM_WIRED_INTERFACE}"
        printf '  This box serves DHCP on %s and answers for *.loom\n' \
          "''${LOOM_SUBNET}"
      fi
      # Read at print time, not baked in: a box booted with the recovery
      # passphrase has no key at all and its guard never arms, and a banner
      # that claimed otherwise would be promising protection the box does not
      # have. key-guard.nix restarts loom-issue.service whenever this changes.
      if [ -r ${config.loom.keyGuard.stateDir}/state ]; then
        case "$(cat ${config.loom.keyGuard.stateDir}/state)" in
          armed)
            printf '\n  USB key guard: armed. Removing the USB key powers this\n'
            printf '  box off after %s seconds.\n' ${toString keyGuardGrace}
            ;;
          disarmed)
            printf '\n  USB key guard: disarmed until the next boot.\n'
            ;;
          *)
            printf '\n  USB key guard: idle -- no USB key present.\n'
            ;;
        esac
      fi
      if [ -r ${recoveryPassphraseFile} ]; then
        printf '\n  LUKS recovery passphrase: %s\n' \
          "$(cat ${recoveryPassphraseFile})"
        printf '  Write it down. Without the USB stick it is the only way\n'
        printf '  to unlock this disk, and nobody else holds a copy.\n'
      fi
      ${lib.optionalString showWifi ''
        # Safe to print for the same reason the recovery passphrase above is:
        # this screen belongs to a VT that opens a root-capable session on the
        # next keypress, so it discloses nothing the console did not already.
        #
        # loom-wifi-check (wifi.nix) writes a warning fragment above this one
        # when the radio never came up, so a box printing these credentials for
        # a network that does not exist says so on the same screen.
        printf '\n  Scan to join -- same network as the cable, same *.loom:\n\n'
        # ANSIUTF8 rather than ASCII, and this is not cosmetic. It draws each
        # row with the half blocks U+2580/U+2584, so a QR module is one cell
        # wide by half a cell tall -- close to square on the 12x26 cell
        # branding.nix selects. Drawn with '#' instead, every module would be
        # twice as tall as it is wide and most phones refuse to decode it.
        # branding.nix already asserts the console font carries those two
        # glyphs plus U+2588, which is why the mark renders at all.
        #
        # The reset matters: the banner deliberately never restores the palette
        # after the eyes (see above), and a QR drawn in amber-on-amber is not a
        # QR. qrencode emits its own SGR pairs, so one reset here is enough.
        #
        # --margin=2 rather than the default 4. The whole banner has to fit one
        # screen -- agetty writes the issue straight to the VT with no paging,
        # so whatever does not fit scrolls off the top, taking the mark with it.
        # Two modules of quiet zone is under the 4 the spec asks for, but the
        # zone here is white against a black console, which is the high-contrast
        # case scanners cope with; checked against a decoder at this margin.
        printf '%s' $'\033[0m'
        # UTF8i, not ANSIUTF8, and the colours are ours rather than qrencode's.
        #
        # qrencode's own ANSI types emit `ESC[40;37;1m` and then draw the *light*
        # modules as white glyphs, so the code comes out as white marks on
        # whatever the console's background happens to be -- a white-on-black QR
        # with no field behind it. The `i` types invert which modules the glyphs
        # stand for, so with a white background and black ink the block becomes
        # a proper white card with black modules: the orientation every scanner
        # is tuned for, and the one people recognise as a QR code.
        #
        # 47, with palette index 7 redefined to ffffff by `palette` above --
        # rather than the bright-background code 107 this used to use.
        #
        # 40-47 are the background codes console_codes(4) lists outright; 100-107
        # are the aixterm extension, and a console that does not take them leaves
        # the background where it was. Here that is black, against ink this sets
        # to black -- an invisible code rather than a wrong-coloured one, which
        # is the worst way for it to fail. 40-47 only reach palette indices 0-7,
        # so the card has to be index 7, and index 7 is plain light grey by
        # default -- too little contrast to scan reliably. Redefining it is the
        # same ESC]P mechanism the amber already depends on, and it also makes
        # the console's ordinary text pure white instead of grey.
        qrencode --type=UTF8i --level=L --margin=2 -- ${lib.escapeShellArg wifiUri} |
          while IFS= read -r qrline; do
            # Indented like every other line of the banner, and the background
            # is re-opened per line so the card is a solid rectangle rather than
            # a run that the terminal resets at the first newline.
            printf '  %s%s%s\n' $'\033[47;30m' "$qrline" $'\033[0m'
          done
        # Below the code, not above it: someone who cannot scan reads them off
        # the same part of the screen they were already looking at, and they
        # stay visible when the code itself is the thing that scrolled.
        printf '  WiFi network: %s\n' ${lib.escapeShellArg config.loom.wifi.ssid}
        printf '  Passphrase:   %s\n' ${lib.escapeShellArg config.loom.wifi.psk}
      ''}
      printf '\n'
    '';
  };
in
{
  # ---------------------------------------------------------------------------
  # Host tuning -- mirrors up.sh `setup_system` (up.sh:616-684).
  #
  # up.sh additionally persists these to /etc/sysctl.d/99-loom.conf; NixOS writes
  # its own /etc/sysctl.d/60-nixos.conf from the values below, so that file is
  # redundant here and `--skip-setup_system` keeps up.sh from creating it.
  # ---------------------------------------------------------------------------
  boot.kernel.sysctl = {
    "vm.max_map_count" = 1677720; # NixOS default 1048576 -> raised
    "vm.overcommit_memory" = 1;
    "fs.inotify.max_user_watches" = 655360; # NixOS default 524288 -> raised
    # Deliberately LOWER than the NixOS default of 524288. up.sh forces this
    # value with an equality test rather than a floor, so 1280 is what every
    # Loom deployment is actually tested against. Keep the two in sync.
    "fs.inotify.max_user_instances" = 1280;
    "fs.file-max" = 2097152;
    "vm.swappiness" = 1;
    "vm.dirty_background_ratio" = 10;
    "vm.dirty_ratio" = 40;
  };

  # ---------------------------------------------------------------------------
  # Name resolution -- mirrors up.sh `install_host_entries` (up.sh:936-996).
  #
  # The host list is generated from vars.sh by the build script, so vars.sh stays
  # the single source of truth and the 22 names are never duplicated in Nix.
  #
  # Declaring them here also avoids up.sh's `sudo cp --remove-destination` hack
  # (up.sh:963-977), which breaks /etc/hosts out of the Nix store on immutable
  # distributions -- it names NixOS in its own comment.
  # ---------------------------------------------------------------------------
  networking.hosts."${minikubeIp}" = builtins.fromJSON loomHostsJson;

  networking.hostName = "loom";
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [
      80
      443
    ];
  };

  # ---------------------------------------------------------------------------
  # Toolchain -- every binary up.sh needs, in one list.
  #
  # `validate_environment` checks most of them (up.sh:402-428), but not all: it
  # pipes through `awk` at up.sh:380, *above* its own checks, and `cicd/skaffold`
  # reaches for `tar` and `mktemp`. So this list is wider than the check list.
  #
  # It is deliberately a shared option rather than a literal here, because the
  # units in modes.nix need exactly the same set on their PATH and a unit's PATH
  # has nothing to do with systemPackages -- `/run/current-system/sw/bin` is
  # never on it. The two used to be maintained separately and drifted, which
  # shipped a box whose loom.service died on `awk: command not found`.
  #
  # devenv is deliberately not used on the appliance: once we are building a
  # NixOS closure anyway, this carries the toolchain for free, with no nix store
  # pre-seeding and no direnv trust step.
  # ---------------------------------------------------------------------------
  loom.toolchain =
    with pkgs;
    [
      bash # `sh` (up.sh:415, and `sudo sh -c` at up.sh:927)
      # `cp` `mkdir` `nproc` `df` `tee` `realpath` `mktemp`
      coreutils
      diffutils # `diff`
      gnugrep # `grep`
      procps # `sysctl` `pidwait` `pkill` -- pidwait needs procps-ng >= 4
      gawk # `awk`
      curl # also `is_offline` (up.sh:216-221), which runs every invocation
      util-linux
      kubectl
      kubernetes-helm # `helm`
      minikube
      skaffold
      # Must be the kislyuk wrapper, NOT yq-go: up.sh:359 calls
      # `yq -y -s 'reduce .[] as $item ({}; . * $item)'`, which is jq syntax.
      yq

      # Not in up.sh's check list, but bring-up fails without them:
      git
      git-lfs # the embedded checkout configures filter.lfs.*
      gnutar # cicd/skaffold untars the vendored traefik chart
      gzip
      jq # the kislyuk `yq` shells out to it
    ]
    # The vendor's SMI tool, on a box that offloads Ollama to a GPU. up.sh wants
    # it twice: `validate_environment` refuses to run without it whenever --gpus
    # is set, and `check_host_resources` counts the GPUs by parsing its output.
    # Both run inside loom.service, so PATH here is what matters rather than the
    # operator's shell -- though it lands in both, as the whole toolchain does.
    #
    # Nothing else comes with it: the ROCm userspace Ollama needs is inside
    # ollama/ollama:rocm, not out here. And there is no nvidia branch, because no
    # platform declares that vendor yet -- nvidia-smi arrives with the driver
    # rather than as a standalone package, so the platform that wants it brings
    # `hardware.nvidia` along too.
    ++ lib.optional (config.loom.platform.gpuVendor == "amd") pkgs.rocmPackages.rocm-smi;

  environment.systemPackages =
    config.loom.toolchain
    ++ (with pkgs; [
      # `EDITOR` above. Also supplies `vi`, `view` and `xxd`, which is why this
      # is the plain `vim` and not `neovim`: neovim costs ~200 MiB of closure
      # that nothing else here shares -- perl, glib, libx11, libxcb, luajit,
      # tree-sitter -- on a box with no X at all, against ~43 MiB for vim, whose
      # only other dependencies (gawk, bash-interactive, readline) are already
      # in this closure.
      vim
      # Kept alongside vim deliberately, for 2.6 MiB. These boxes are given
      # away, the console is the whole user interface, and there is no remote
      # access to rescue anyone -- so an operator who does not know vim needs a
      # modeless editor to fall back to.
      nano

      # Field diagnosis on a box with no remote access. Interactive only -- a
      # unit has no use for any of these, so they stay out of `loom.toolchain`.
      cryptsetup
      gptfdisk
      nvme-cli
      pciutils
      usbutils
      htop
      less
      # Not for the daemon -- console-mouse.nix names its own store path for
      # that -- but for the three client tools in the same package, which are
      # the only way to debug a console mouse on a box with no remote access:
      # `mev` prints the events gpm is delivering, `mouse-test` identifies the
      # protocol a device speaks, and `hltest` exercises the console highlight
      # the pointer is drawn with.
      gpm

      # The operator's console session (console.nix). Plain btop, not devenv's
      # `btop.override { cudaSupport = true; rocmSupport = true; }`. So no GPU
      # row on the EVO-X2, and that is the trade: the override carries CUDA and
      # the ROCm stack into an image that is already ~60 GB of container
      # layers, to decorate a monitoring pane. `rocm-smi` is in the toolchain
      # above on that platform and answers the same question.
      tmux
      btop
      # What the top-left pane becomes once Loom is up. Listed here as well so
      # that an operator on a plain Alt-F2 console, or one who closed the pane,
      # still has it.
      k9s
    ])
    # The assistant pane, same reasoning as k9s above. console.nix's loom-chat is
    # what wires it to the cluster's Ollama and pins the model; bare `opencode`
    # here is for the operator who wants it pointed somewhere else.
    #
    # nixpkgs builds only the CLI -- one Bun-compiled binary, not the desktop app
    # in the same repo -- and bakes models.dev's catalogue into the closure,
    # which is what makes it usable on a box with no route off the network.
    #
    # Omitted entirely on a platform that does not deploy Ollama: there would be
    # nothing for it to talk to, and it is not a small closure to carry for that.
    ++ lib.optional config.loom.platform.runsAiServices pkgs.opencode
    # Both interactive, and neither belongs in `loom.toolchain`: no unit runs
    # either. loom-platform-info is field diagnosis in the same sense as the
    # pciutils/nvme-cli block above -- it is what somebody runs when the box
    # does not behave, or when the values in platforms/<id>.nix need checking
    # against the hardware for the first time.
    ++ [
      loom-info
      loom-platform-info
    ]
    ++ config.loom.entrypoints;

  # Also handed to the units in modes.nix, which need them on their PATH rather
  # than merely in the operator's shell.
  loom.entrypoints = [
    loom-up
    loom-down
  ];

  virtualisation.docker = {
    enable = true;
    daemon.settings = {
      log-driver = "json-file";
      log-opts = {
        max-size = "100m";
        max-file = "3";
      };
      storage-driver = "overlay2";
    };
  };

  # ---------------------------------------------------------------------------
  # Operator account
  # ---------------------------------------------------------------------------
  users.mutableUsers = true;
  users.users.${loomUser} = {
    isNormalUser = true;
    description = "Loom operator";
    createHome = true;
    extraGroups = [
      "wheel"
      "docker"
      # Reading `journalctl --unit` as a non-root user only reaches that user's
      # own journal. The messages console.nix's first pane exists to surface --
      # PID 1's "Condition check resulted in loom-fetch.service being skipped",
      # above all -- are _UID=0 and would be invisible without this. It grants
      # nothing new: `wheel` plus `wheelNeedsPassword = false` below already
      # hands this account root.
      "systemd-journal"
    ];
  };
  # No direct root login; the appliance is reached through the operator account.
  users.users.root.hashedPassword = "!";

  # The operator account has no password, so the console can log into it without
  # asking for one. A password would buy nothing: `wheelNeedsPassword = false`
  # below already hands out root without one, there is no sshd, and the disk is
  # LUKS-encrypted with the key on the USB stick -- physical possession is the
  # whole trust boundary. A user with no declared password gets a locked shadow
  # entry, and `users.mutableUsers` is true, which switches off the assertion
  # that would otherwise catch it.
  #
  # console.nix is what turns that into a usable login: it keeps agetty's
  # `--autologin`, which is what bypasses the locked entry, but pairs it with
  # `--login-pause` so nothing opens a session until somebody presses a key.

  security.sudo = {
    enable = true; # up.sh:406 requires `sudo` to exist
    # up.sh backgrounds `sudo minikube tunnel` for --expose (up.sh:924-933), and
    # the appliance starts Loom unattended, so this cannot prompt. Acceptable
    # only because the box has no sshd and is reachable from the console alone.
    wheelNeedsPassword = false;
  };

  # Appliance policy: no remote access at all.
  services.openssh.enable = false;

  # ---------------------------------------------------------------------------
  # Loom entry point
  # ---------------------------------------------------------------------------
  environment.sessionVariables = {
    # Mirrors devenv.nix:273,276 -- the layout every Loom code path is tested
    # against. Both directories are already in .gitignore, so the working tree
    # of the embedded checkout stays clean.
    MINIKUBE_HOME = "${loomRepoDir}/.minikube";
    SKAFFOLD_HOME = "${loomRepoDir}/.skaffold";

    # Nothing on this box sets an editor otherwise, and the fallbacks that step
    # in are worse than a choice: git's is `vi`, which the appliance did not
    # carry at all, so `git commit` on the console died with "not found". Set
    # here rather than only in up.sh, because the operator's shell never sources
    # that script -- up.sh's own `export` only reaches what up.sh starts.
    EDITOR = "vim";
  };

  # ---------------------------------------------------------------------------
  # Console banner.
  #
  # These boxes are given away, and have no remote access, so the console is the
  # only place this information can reach anyone. It is therefore shown before
  # anyone logs in, as the agetty issue -- console.nix's `--login-pause` then
  # holds the screen there until somebody presses a key.
  #
  # Shown there and nowhere else. The login shell used to reprint it, which on
  # tty2-tty6 put the same screen up twice with nothing between the two copies
  # but the keypress: agetty renders the issue on every VT, not just tty1. The
  # only console where the banner really is covered is tty1, where the tmux
  # session draws over it -- and an operator who wants it back there types
  # `loom-info`, which is on the PATH for exactly that.
  #
  # The recovery passphrase is part of it, which is safe here for the same
  # reason the file itself is: reading it requires the box to have booted, which
  # requires the stick -- and the console hands out a root-capable shell without
  # a password anyway, so the issue exposes nothing the VT did not already.
  # ---------------------------------------------------------------------------

  # /run rather than /etc: the issue is regenerated on every boot, and 26.05 may
  # mount /etc read-only through the etc overlay. NixOS points agetty at
  # `/etc/issue:/etc/issue.d:/run/issue:/run/issue.d` (getty.nix:13-18), and
  # util-linux 2.42 reads every one of them.
  #
  # getty-pre.target is the ordering hook for exactly this, but it is a passive
  # target: systemd.special(7) requires its users to pull it into the boot
  # transaction themselves. Hence `wants` as well as `before` -- and
  # `wantedBy = multi-user.target`, because being wanted *by* a target that
  # nothing starts would leave this unit unreachable and the banner missing.
  # getty@ is After=getty-pre.target upstream, so this lands before any getty
  # renders the issue.
  systemd.services.loom-issue = {
    description = "Loom console banner for the login screen";
    wantedBy = [ "multi-user.target" ];
    wants = [ "getty-pre.target" ];
    before = [ "getty-pre.target" ];
    # After the font, not merely before the getty.
    #
    # Both units are only `before getty-pre.target`, which orders each against
    # the getty and neither against the other -- and this one used to win by
    # about two seconds. That mattered once the banner started measuring the
    # console to decide what fits: the font is what sets the row count, so
    # measuring first meant measuring the kernel's 16x32 grid and then shedding
    # the mark and the QR code to fit a screen that was about to become three
    # times taller. Ordering here is the whole fix; the measurement was never
    # wrong about the console it was handed.
    after = [ "loom-console-font.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = writeIssue;
    };
  };

  # ---------------------------------------------------------------------------
  # Redraw the banner once the console has stopped resizing under it.
  #
  # tty1 is painted *during* the boot's console churn, and the other VTs are
  # not: logind spawns autovt@tty2 and up only when somebody switches to one, by
  # which time the geometry is final. That is the whole of why tty1 shows a
  # cropped banner while tty2 shows a correct one.
  #
  # What churns is the font, and with it the row count. fbcon starts on the
  # kernel's built-in 16x32, branding.nix's loom-console-font puts Cozette on
  # (many more rows), the DRM driver takes the console and resets it back to the
  # built-in (far fewer), and loom-console-font-reapply puts Cozette on again.
  # Every one of those is a VT resize, and when a VT shrinks the kernel keeps
  # the bottom of the screen and discards the top -- so a banner drawn before
  # the shrink loses exactly its first rows, which is where the mark is.
  #
  # Shrinking the banner to fit the smallest grid would be guesswork about a
  # panel nobody has seen. Drawing it again after the last resize is not: the
  # issue is re-measured against the geometry that is now final, and agetty
  # repaints it from a clean VT.
  # ---------------------------------------------------------------------------
  systemd.services.loom-banner-repaint = {
    description = "Redraw the login banner while the console is still settling";
    # Pulled in by the boot rather than by the font units. Those fire from udev
    # coldplug, which is before any getty exists -- so the repaint they asked for
    # found nothing on screen to redraw and never ran again, which is exactly how
    # tty1 kept its cropped banner while tty2 looked right.
    wantedBy = [ "multi-user.target" ];
    after = [ "getty.target" ];
    serviceConfig = {
      Type = "simple";
      # One pass through the window below, then done. A failure here costs the
      # banner its redraw and nothing else, so never take the boot down with it.
      Restart = "no";
    };
    path = [
      pkgs.coreutils
      config.systemd.package
    ];
    script = ''
      # Watch the console instead of guessing when it stops moving.
      #
      # The row count changes several times during boot -- the kernel's built-in
      # font, Cozette, the DRM driver's reset, Cozette again -- and agetty paints
      # tty1 somewhere in the middle of that. A VT that shrinks keeps the bottom
      # of the screen and discards the top, which is why the mark goes first and
      # why the surviving banner starts partway down. tty2 and up never show it:
      # logind spawns them on demand, long after the last resize.
      #
      # So: poll, and redraw whenever the geometry is not the one the banner on
      # screen was drawn for. Bounded, because this is a boot-time phenomenon and
      # a poller that outlives it would be a poller nobody ever accounts for.
      deadline=$(( SECONDS + ${toString bannerRepaintWindow} ))

      # `seen` is the last geometry observed, `dirty` whether the screen has been
      # disturbed since it was last drawn.
      #
      # Tracking the change rather than the current value is the whole point. A
      # resize discards screen content, and it does that whether or not the size
      # ends up back where it started -- the DRM takeover drops the console to
      # the kernel's font and loom-console-font-reapply puts Cozette back, so the
      # row count an operator finally sees is often exactly the one the banner
      # was drawn at, with the top of that banner thrown away in between.
      # Comparing "is it different now" would see nothing wrong and leave the
      # screen broken, which is precisely what it did.
      #
      # `dirty` starts set, so the banner is drawn once for the geometry that is
      # current when the getty first appears, whatever happened before that.
      seen=""
      dirty=yes

      measure() {
        stty size </dev/tty1 2>/dev/null | cut --delimiter=' ' --fields=1 || true
      }

      # The banner is only ours to redraw while it is still the thing on screen.
      # `--login-pause` holds agetty at the issue until a keypress, and
      # `--autologin` then has it exec login and the operator's shell in the same
      # process -- so a main PID that is still agetty is the signal that nobody
      # has pressed a key yet.
      #
      # Echoes the unit name in that case and nothing in every other, and
      # "nothing" is deliberately not interpreted. A logged-in operator, a getty
      # between lives after we restarted it ourselves, and a getty that has not
      # exec'd agetty yet are indistinguishable from here and do not need to be
      # told apart: the caller simply does not redraw this round. An earlier
      # version tried to read one of those as "logged in, stop watching", and
      # since it hit that state on its very first pass it stopped before it had
      # done anything at all.
      #
      # tty1's getty is autovt@tty1.service on NixOS (an alias of the getty@
      # template, see console.nix); both names are tried, and a miss on the first
      # moves on to the second rather than deciding the question.
      banner_getty() {
        local unit pid
        for unit in autovt@tty1.service getty@tty1.service; do
          pid="$(systemctl show --property=MainPID --value "$unit" 2>/dev/null || true)"
          if [ -z "$pid" ] || [ "$pid" = 0 ]; then
            continue
          fi
          if [ "$(cat "/proc/$pid/comm" 2>/dev/null || true)" != agetty ]; then
            continue
          fi
          printf '%s' "$unit"
          return
        done
      }

      while [ "$SECONDS" -lt "$deadline" ]; do
        rows="$(measure)"

        if [ "$rows" != "$seen" ]; then
          # Something moved. Note it and wait for it to stop, so a redraw lands
          # once per resize rather than once per intermediate state.
          seen="$rows"
          dirty=yes
          sleep ${toString bannerRepaintInterval}
          continue
        fi

        unit="$(banner_getty)"
        if [ "$dirty" = yes ] && [ -n "$unit" ] && [ -n "$rows" ]; then
          ${writeIssue}
          # getty@ clears the VT on start (TTYVTDisallocate), so this lands on a
          # clean screen rather than under the old copy. --no-block: never wait
          # on a job from inside a queue this unit is itself in.
          systemctl restart --no-block "$unit"
          dirty=no
        fi
        sleep ${toString bannerRepaintInterval}
      done
    '';
  };

  # The installer writes the recovery passphrase here. wheel-readable so the
  # operator can see it without sudo; the disk it sits on is encrypted anyway.
  systemd.tmpfiles.rules = [
    "d /var/lib/loom 0750 root wheel -"
  ];

  system.stateVersion = "26.05";

  documentation.nixos.enable = false;
}
