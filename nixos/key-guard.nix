# The USB key has to stay plugged in.
#
# The root is LUKS2 and its key is 4096 bytes on the stick's `loom-key`
# partition -- but that key is read exactly once, by systemd-cryptsetup in stage
# 1 (box-hardware.nix). After switch-root nothing touches the stick again: the
# ESP is on the internal disk, and the installer moves its own loader off the
# removable-media path. So pulling the stick used to do nothing at all; the box
# went on running for weeks on an unlocked dm-crypt mapping with no key present,
# and the removal only armed the *next* boot.
#
# That is the gap this module closes, and it is the gap the threat model in
# Documentation/appliance.md already assumed was closed: "the design assumes the
# stick is removed, or travels separately, whenever the box is unattended".
#
# The guard polls rather than binding to the key's .device unit. A device unit
# would fire instantly instead of within two seconds -- irrelevant against a
# human pulling a stick -- and `ExecStopPost` on a `BindsTo=` unit also fires on
# every ordinary shutdown, which on a box with no remote access is a far worse
# failure than two seconds of latency. Polling also gets the identity check for
# free, which presence alone cannot give at any price.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.loom.keyGuard;
  graceSeconds = cfg.intervalSec * cfg.graceTicks;

  loom-key-guard = pkgs.writeShellApplication {
    name = "loom-key-guard";
    runtimeInputs = with pkgs; [
      coreutils
      cryptsetup
      systemd # `systemctl`
      tmux # best-effort notices into the operator's session
      util-linux # `wall`
    ];
    text = ''
      readonly STATE_DIR=${lib.escapeShellArg cfg.stateDir}
      readonly STATE_FILE="''${STATE_DIR}/state"
      readonly DEVICE_FILE="''${STATE_DIR}/device"
      readonly FINGERPRINT_FILE="''${STATE_DIR}/fingerprint"
      readonly DISARM_FILE="''${STATE_DIR}/disarmed"

      readonly KEY_DEVICE=${lib.escapeShellArg cfg.keyDevice}
      readonly ROOT_DEVICE=${lib.escapeShellArg cfg.rootDevice}
      readonly KEY_BYTES=${toString cfg.keyBytes}
      readonly INTERVAL=${toString cfg.intervalSec}
      readonly GRACE_TICKS=${toString cfg.graceTicks}
      readonly GRACE_SECONDS=${toString graceSeconds}
      readonly ACTION=${lib.escapeShellArg cfg.action}
      readonly SOCKET=${lib.escapeShellArg config.loom.consoleSocket}

      main() {
          local command="''${1:-watch}"

          case "''${command}" in
          watch)
              require_root
              ensure_state_dir
              watch
              ;;
          status)
              status
              ;;
          arm)
              require_root
              ensure_state_dir
              # Deliberately does not arm here: the watcher owns the state
              # files, and a second writer would race it. Clearing the flag is
              # enough -- the next tick picks the key up.
              rm --force "''${DISARM_FILE}"
              printf 'Key guard re-enabled; it arms within %ss if the key is present.\n' \
                  "''${INTERVAL}"
              ;;
          disarm)
              require_root
              ensure_state_dir
              : >"''${DISARM_FILE}"
              printf 'Key guard disarmed until the next boot. The USB key can be removed.\n'
              ;;
          *)
              printf >&2 'usage: loom-key-guard [watch|status|arm|disarm]\n'
              exit 1
              ;;
          esac
      }

      require_root() {
          if [[ "''${EUID}" -ne 0 ]]; then
              printf >&2 'loom-key-guard: must run as root.\n'
              exit 1
          fi
      }

      ensure_state_dir() {
          mkdir --parents "''${STATE_DIR}"
          chmod 0755 "''${STATE_DIR}"
      }

      # ---------------------------------------------------------------------
      # State
      #
      # `state` is world-readable because box.nix's login banner reads it as the
      # operator; `fingerprint` is not, and is the only file here worth hiding.
      # Both are written through a temporary file, so a banner rendered while
      # the guard is mid-write can never read half a word.
      # ---------------------------------------------------------------------
      put() {
          local path="''${1}" mode="''${2}" content="''${3}"
          printf '%s\n' "''${content}" >"''${path}.tmp"
          chmod "''${mode}" "''${path}.tmp"
          mv "''${path}.tmp" "''${path}"
      }

      current_state() {
          cat "''${STATE_FILE}" 2>/dev/null || printf 'idle'
      }

      set_state() {
          put "''${STATE_FILE}" 0644 "''${1}"
          # The banner is generated once per boot into /run/issue.d and is the
          # only thing an operator who never logs in ever sees, so it has to
          # follow the guard rather than report whatever was true at boot.
          systemctl restart loom-issue.service >/dev/null 2>&1 || true
      }

      # ---------------------------------------------------------------------
      # Reading the key
      # ---------------------------------------------------------------------
      read_fingerprint() {
          local device="''${1}" digest
          # iflag=direct is not a micro-optimisation. Without O_DIRECT the page
          # cache happily hands the same 4096 bytes back long after the stick
          # has physically left, and the guard never fires at all.
          if ! digest="$(dd if="''${device}" bs="''${KEY_BYTES}" count=1 \
              iflag=direct status=none | sha256sum)"; then
              # Not every USB bridge accepts O_DIRECT, and a guard that quietly
              # never armed would be worse than the cache it is avoiding.
              # BLKFLSBUF invalidates this device's buffer cache, which buys the
              # same guarantee the long way round.
              blockdev --flushbufs "''${device}" 2>/dev/null || return 1
              digest="$(dd if="''${device}" bs="''${KEY_BYTES}" count=1 \
                  status=none | sha256sum)" || return 1
          fi
          printf '%s' "''${digest%% *}"
      }

      zero_fingerprint() {
          local digest
          digest="$(head --bytes="''${KEY_BYTES}" /dev/zero | sha256sum)"
          printf '%s' "''${digest%% *}"
      }

      # True while the key recorded at arm time is still readable somewhere.
      #
      # The *bytes* are the identity, not the path. A stick that is pulled and
      # put back inside the grace window can come back on a different /dev node,
      # so the node seen at arm time is only a fast path -- what the label
      # resolves to right now is tried as well, and either answer is accepted
      # only if it hashes to what was recorded. That is also what makes
      # /dev/disk/by-partlabel safe to consult here at all: it is not unique,
      # and with a second Loom stick attached it resolves to whichever one udev
      # linked last (installer-scripts/common.sh).
      key_present() {
          local expected pinned resolved node fingerprint
          expected="$(cat "''${FINGERPRINT_FILE}" 2>/dev/null)" || return 1
          pinned="$(cat "''${DEVICE_FILE}" 2>/dev/null || true)"
          resolved="$(readlink --canonicalize "''${KEY_DEVICE}" 2>/dev/null || true)"

          for node in "''${pinned}" "''${resolved}"; do
              [[ -b "''${node}" ]] || continue
              fingerprint="$(read_fingerprint "''${node}")" || continue
              [[ "''${fingerprint}" == "''${expected}" ]] || continue
              if [[ "''${node}" != "''${pinned}" ]]; then
                  put "''${DEVICE_FILE}" 0644 "''${node}"
              fi
              return 0
          done
          return 1
      }

      arm_once() {
          local node fingerprint

          node="$(readlink --canonicalize "''${KEY_DEVICE}" 2>/dev/null || true)"
          [[ -b "''${node}" ]] || return 1

          fingerprint="$(read_fingerprint "''${node}")" || return 1
          # A wiped key partition is a missing key. Same rule the installer
          # applies before it will install at all (common.sh `key_state`).
          [[ "''${fingerprint}" != "$(zero_fingerprint)" ]] || return 1

          # The LUKS header is the oracle: this proves the stick still unlocks
          # *this* disk. It is why no copy of the key has to be kept anywhere,
          # and why a foreign stick carrying a partition named loom-key cannot
          # keep the box alive. Cheap -- the installer formats with pbkdf2 at
          # 1000 iterations.
          cryptsetup luksOpen --test-passphrase \
              --key-file "''${node}" \
              --keyfile-size "''${KEY_BYTES}" \
              "''${ROOT_DEVICE}" >/dev/null 2>&1 || return 1

          put "''${DEVICE_FILE}" 0644 "''${node}"
          put "''${FINGERPRINT_FILE}" 0600 "''${fingerprint}"
          set_state armed
          printf '[loom] Key guard armed on %s; removing the key %s.\n' \
              "''${node}" "$(action_phrase)"
      }

      # ---------------------------------------------------------------------
      # Telling whoever is standing at the box
      #
      # The unit logs to the journal only, like every other Loom unit, so that
      # nothing paints over the operator's screen. `wall` and tmux are what
      # actually reach a human, and both are best-effort: there may be no
      # session and no terminal at all.
      # ---------------------------------------------------------------------
      announce() {
          printf '%s\n' "''${1}"
          wall --nobanner "''${1}" 2>/dev/null || true
          tmux -S "''${SOCKET}" display-message "''${1}" 2>/dev/null || true
      }

      alarm() {
          tmux -S "''${SOCKET}" set-option -g status-style "bg=colour124,fg=white" \
              2>/dev/null || true
      }

      clear_alarm() {
          # The value console.nix's tmux.conf sets. Restated rather than shared
          # because a tmux option can only be restored by naming it again.
          tmux -S "''${SOCKET}" set-option -g status-style "bg=colour24,fg=white" \
              2>/dev/null || true
      }

      action_phrase() {
          case "''${ACTION}" in
          poweroff) printf 'powers this box off after %ss' "''${GRACE_SECONDS}" ;;
          *) printf 'only warns (first-time setup does not power off)' ;;
          esac
      }

      # ---------------------------------------------------------------------
      # The loop
      # ---------------------------------------------------------------------
      watch() {
          local misses=0 idle_logged=0

          trap 'exit 0' TERM INT

          while :; do
              # A reboot or poweroff the operator asked for stops this unit as
              # part of the same transaction that tears the rest of the box
              # down. Without this the guard would race it and act on a box
              # that was already on its way down.
              if [[ "$(systemctl is-system-running 2>/dev/null || true)" == "stopping" ]]; then
                  exit 0
              fi

              if [[ -e "''${DISARM_FILE}" ]]; then
                  if [[ "$(current_state)" != "disarmed" ]]; then
                      misses=0
                      clear_alarm
                      set_state disarmed
                      announce "[loom] Key guard disarmed. Removing the USB key will not power this box off."
                  fi
              elif [[ "$(current_state)" != "armed" ]]; then
                  if arm_once; then
                      misses=0
                      idle_logged=0
                  elif [[ "''${idle_logged}" -eq 0 ]]; then
                      # Once, not every two seconds for the life of the box.
                      # This is the ordinary state of a box booted with the
                      # recovery passphrase, and it is not an error.
                      idle_logged=1
                      set_state idle
                      printf '[loom] No usable key at %s; the guard stays idle.\n' "''${KEY_DEVICE}"
                  fi
              elif key_present; then
                  if [[ "''${misses}" -gt 0 ]]; then
                      misses=0
                      clear_alarm
                      announce "[loom] USB key is back. Shutdown cancelled."
                  fi
              else
                  misses=$((misses + 1))
                  if [[ "''${misses}" -ge "''${GRACE_TICKS}" ]]; then
                      trip
                      misses=0
                      idle_logged=0
                  else
                      alarm
                      announce "[loom] USB KEY REMOVED -- $(((GRACE_TICKS - misses) * INTERVAL))s left. Plug it back in to cancel."
                  fi
              fi

              sleep "''${INTERVAL}"
          done
      }

      trip() {
          clear_alarm

          if [[ "''${ACTION}" != "poweroff" ]]; then
              # Warn-only, which is what first-time setup gets: that mode pulls
              # every container image over hours, on a box that is still in the
              # lab with nothing secret on it yet.
              set_state idle
              announce "[loom] USB key gone for ''${GRACE_SECONDS}s. First-time setup only warns; the box stays up."
              return 0
          fi

          announce "[loom] USB key gone for ''${GRACE_SECONDS}s. Powering off now."
          set_state tripped
          # A clean poweroff, not a forced one: unit teardown is bounded by
          # DefaultTimeoutStopSec, and the indexed data is worth more than the
          # seconds a sysrq would save.
          systemctl poweroff
          exit 0
      }

      status() {
          local state device
          state="$(current_state)"
          device="$(cat "''${DEVICE_FILE}" 2>/dev/null || true)"

          printf 'loom-key-guard: %s\n' "''${state}"
          printf '  key device:  %s\n' "''${KEY_DEVICE}"
          if [[ -n "''${device}" ]]; then
              printf '  resolved to: %s\n' "''${device}"
          fi
          printf '  on removal:  %s after %ss\n' "''${ACTION}" "''${GRACE_SECONDS}"
      }

      main "''${@}"
    '';
  };
in
{
  options.loom.keyGuard = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      internal = true;
      description = ''
        Whether the appliance shuts itself down when the USB key is removed.

        Only ever false for debugging a box by hand. The installer image never
        imports this module at all.
      '';
    };

    action = lib.mkOption {
      type = lib.types.enum [
        "poweroff"
        "warn"
      ];
      default = "poweroff";
      internal = true;
      description = ''
        What happens once the key has been gone for the whole grace window.

        Set by modes.nix, beside the mode it describes, for the same reason as
        `loom.progressUnit`: `poweroff` in run mode, `warn` in first-time setup,
        where a trip would throw away hours of container pulls on a box that is
        still in the lab with nothing secret on it.

        The default is the safe one, so a new mode that forgets to set this
        gets the protection rather than silently losing it.
      '';
    };

    intervalSec = lib.mkOption {
      type = lib.types.ints.positive;
      default = 2;
      internal = true;
      description = "Seconds between checks of the key.";
    };

    graceTicks = lib.mkOption {
      type = lib.types.ints.positive;
      default = 5;
      internal = true;
      description = ''
        Consecutive failed checks before the guard acts.

        Not zero on purpose: USB re-enumerates spuriously, and a single missed
        read must not hard-stop a box that is mid-index. Five ticks at two
        seconds rides out a glitch and still leaves a ten-second window for an
        operator who pulled the wrong stick to put it back.
      '';
    };

    keyDevice = lib.mkOption {
      type = lib.types.str;
      default = "/dev/disk/by-partlabel/loom-key";
      internal = true;
      description = ''
        The stick's key partition, as written by cicd/build_appliance_image.sh.

        Declared here rather than in box-hardware.nix so that the initrd and
        the guard cannot name different devices, and so the VM test can point
        both at a loop device.
      '';
    };

    rootDevice = lib.mkOption {
      type = lib.types.str;
      default = "/dev/disk/by-partlabel/loom-root-luks";
      internal = true;
      description = ''
        The LUKS container the key belongs to. The guard opens it with
        `--test-passphrase` when arming, which is what proves the stick still
        unlocks this particular disk.
      '';
    };

    keyBytes = lib.mkOption {
      type = lib.types.ints.positive;
      default = 4096;
      internal = true;
      description = ''
        How many bytes of the key partition are the key. Must match what
        cicd/build_appliance_image.sh writes and what install.sh formatted
        with (`LOOM_KEY_BYTES`).
      '';
    };

    stateDir = lib.mkOption {
      type = lib.types.str;
      default = "/run/loom/key-guard";
      readOnly = true;
      internal = true;
      description = ''
        Where the guard keeps what it learned when it armed. Read by box.nix's
        login banner, which is why it is an option rather than a literal in two
        places.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ loom-key-guard ];

    # 0755 inside console.nix's 0700 /run/loom: the operator's banner reads
    # `state` from here, and only the fingerprint is worth hiding.
    systemd.tmpfiles.rules = [
      "d ${cfg.stateDir} 0755 root root -"
    ];

    systemd.services.loom-key-guard = {
      description = "Shut down when the LUKS USB key is removed";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${lib.getExe loom-key-guard} watch";
        # Journal only. console.nix moved /dev/console off tty1 so that units
        # stop painting over the operator's session; the guard reaches a human
        # through `wall` and tmux instead.
        StandardOutput = "journal";
        StandardError = "journal";
        # on-failure, not always. The two clean exits are "the system is
        # shutting down" and "the guard tripped and the poweroff is enqueued",
        # and restarting into either of those would only spawn instances that
        # immediately exit again. A crash still comes back.
        Restart = "on-failure";
        RestartSec = 2;
      };
      # A guard that rate-limited itself out of existence after a crash loop
      # would leave the box unprotected with nothing on screen to say so.
      startLimitIntervalSec = 0;
    };
  };
}
