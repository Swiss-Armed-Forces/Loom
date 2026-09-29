# The USB key has to stay plugged in.
#
# The root is LUKS2 and its key is 4096 bytes on the stick's `loom-key`
# partition -- under `--lock-key`, 4096 bytes inside a container on that
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
      readonly DEADLINE_FILE="''${STATE_DIR}/deadline"

      readonly KEY_DEVICE=${lib.escapeShellArg cfg.keyDevice}
      readonly ROOT_DEVICE=${lib.escapeShellArg cfg.rootDevice}
      readonly KEY_BYTES=${toString cfg.keyBytes}
      readonly INTERVAL=${toString cfg.intervalSec}
      readonly GRACE_TICKS=${toString cfg.graceTicks}
      readonly GRACE_SECONDS=${toString graceSeconds}
      readonly KEY_ORACLE=${lib.boolToString cfg.requireKeyOracle}
      readonly ACTION=${lib.escapeShellArg cfg.action}
      readonly SOCKET=${lib.escapeShellArg config.loom.consoleSocket}
      readonly WITNESS_FILE=${lib.escapeShellArg cfg.witnessFile}
      readonly ARM_DEADLINE=${toString cfg.armDeadlineSec}
      readonly SETTLE_TICKS=${toString cfg.armSettleTicks}
      readonly BANNER_REFRESH=${lib.getExe config.loom.bannerRefresh}

      # Why the last arm attempt failed, and the last reason logged, so a box
      # stuck on one cause says so once and a flapping one stays visible.
      ARM_REASON=""
      REPORTED_REASON=""
      # The smallest countdown notice already given, 0 for none yet, and
      # whether the deadline is settled for this boot.
      NOTIFIED=0
      DEADLINE_RETIRED=0

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
          # The banner is the only thing an operator who never logs in ever
          # sees, so it has to follow the guard. Rewriting the issue file is
          # half of that: agetty paints it once and then blocks on a keypress,
          # so tty1 has to be redrawn as well, which is what this command does
          # (box.nix). It exits 1 when it declined to redraw over a session.
          "''${BANNER_REFRESH}" >/dev/null 2>&1 || true
      }

      # ---------------------------------------------------------------------
      # Reading the key
      # ---------------------------------------------------------------------
      read_fingerprint() {
          local device="''${1}" digest
          # iflag=direct is not a micro-optimisation. Without O_DIRECT the page
          # cache happily hands the same 4096 bytes back long after the stick
          # has physically left, and the guard never fires at all.
          # Errors are swallowed because the caller reports them: a read that
          # keeps failing is named once, by `ARM_REASON`, rather than every
          # two seconds for the life of the box.
          if ! digest="$(dd if="''${device}" bs="''${KEY_BYTES}" count=1 \
              iflag=direct status=none 2>/dev/null | sha256sum)"; then
              # Not every USB bridge accepts O_DIRECT, and a guard that quietly
              # never armed would be worse than the cache it is avoiding.
              # BLKFLSBUF invalidates this device's buffer cache, which buys the
              # same guarantee the long way round.
              blockdev --flushbufs "''${device}" 2>/dev/null || return 1
              digest="$(dd if="''${device}" bs="''${KEY_BYTES}" count=1 \
                  status=none 2>/dev/null | sha256sum)" || return 1
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
      # linked last (installer/loom_installer/constants.py).
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
          if [[ ! -b "''${node}" ]]; then
              ARM_REASON="no block device at ''${KEY_DEVICE}"
              return 1
          fi

          if ! fingerprint="$(read_fingerprint "''${node}")"; then
              ARM_REASON="''${node} could not be read"
              return 1
          fi

          # A wiped key partition is a missing key. Same rule the installer
          # applies before it will install at all (common.sh `key_state`).
          if [[ "''${fingerprint}" == "$(zero_fingerprint)" ]]; then
              ARM_REASON="''${node} is blank"
              return 1
          fi

          if [[ "''${KEY_ORACLE}" = true ]]; then
              # The LUKS header is the oracle: this proves the stick still
              # unlocks *this* disk. It is why no copy of the key has to be kept
              # anywhere, and why a foreign stick carrying a partition named
              # loom-key cannot keep the box alive. Cheap -- the installer
              # formats with pbkdf2 at 1000 iterations.
              if ! cryptsetup luksOpen --test-passphrase \
                  --key-file "''${node}" \
                  --keyfile-size "''${KEY_BYTES}" \
                  "''${ROOT_DEVICE}" >/dev/null 2>&1; then
                  ARM_REASON="the key on ''${node} does not open ''${ROOT_DEVICE}"
                  return 1
              fi
          else
              # --lock-key: the bytes on the stick are a LUKS2 container, not the
              # key, so the oracle above has nothing to authenticate with and the
              # guard has no plaintext copy to authenticate with either -- by
              # design, since holding one for the life of the box is the thing
              # the flag exists to avoid.
              #
              # Losing it costs less than it looks. The oracle proves "this stick
              # unlocks this disk", and under --lock-key stage 1 proved exactly
              # that a few seconds ago: the box is running, so the container on
              # this stick yielded the key this root was formatted with. What is
              # left to establish here is that the thing plugged in is a key
              # stick at all, and the fingerprint below carries the rest -- a
              # different container has a different header, so a foreign stick
              # still cannot keep the box alive.
              #
              # `--type luks2` rather than a bare isLuks, matching
              # installer/loom_installer/devices.py `is_key_container`: LUKS1
              # would answer yes, and nothing in Loom writes a LUKS1 container,
              # so one here is a stick from somewhere else.
              if ! cryptsetup isLuks --type luks2 "''${node}" >/dev/null 2>&1; then
                  ARM_REASON="''${node} carries no LUKS2 key store"
                  return 1
              fi
          fi

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
          *) printf 'only warns (this --debug image does not power off)' ;;
          esac
      }

      # ---------------------------------------------------------------------
      # The arm deadline
      #
      # A box that cannot arm is a box running an unlocked dm-crypt mapping
      # with nothing watching the key, so it does not get to run indefinitely.
      #
      # It applies only where stage 1 left `WITNESS_FILE` behind, which says
      # the key partition was present when the root was unlocked
      # (box-hardware.nix). A box booted on the recovery passphrase has no
      # stick, never arms by design, and is left up for repairs -- the console
      # is the only way into it.
      # ---------------------------------------------------------------------
      deadline_applies() {
          [[ "''${DEADLINE_RETIRED}" -eq 0 ]] || return 1
          [[ "''${ARM_DEADLINE}" -gt 0 ]] || return 1
          # Same exception as `trip`: a --debug image warns rather than acts.
          [[ "''${ACTION}" == "poweroff" ]] || return 1
          [[ -e "''${WITNESS_FILE}" ]] || return 1
      }

      # Settled for this boot, by arming or by an operator saying the key may
      # be absent. Neither is reopened by anything short of a reboot.
      retire_deadline() {
          DEADLINE_RETIRED=1
          rm --force "''${DEADLINE_FILE}"
      }

      countdown() {
          local now expires left boundary
          deadline_applies || return 0

          now="$(date +%s)"
          # Absolute, and written once: a guard that systemd restarted must not
          # hand the box a fresh window. It is also what `status` reads.
          if [[ ! -e "''${DEADLINE_FILE}" ]]; then
              put "''${DEADLINE_FILE}" 0644 "$((now + ARM_DEADLINE))"
          fi
          expires="$(cat "''${DEADLINE_FILE}")"
          left=$((expires - now))

          if [[ "''${left}" -le 0 ]]; then
              power_off_now \
                  "[loom] No usable USB key ''${ARM_DEADLINE}s after boot. Powering off now."
          fi

          # Loud, and rarely: nobody is watching the screen for the first
          # minute of a boot, and the notice has to arrive while there is
          # still time to act on it.
          for boundary in 120 60 30 10; do
              if [[ "''${left}" -le "''${boundary}" ]] &&
                  [[ "''${NOTIFIED}" -eq 0 || "''${boundary}" -lt "''${NOTIFIED}" ]]; then
                  NOTIFIED="''${boundary}"
                  alarm
                  announce "[loom] No usable USB key -- this box powers off in ''${left}s. Plug the key in, or run 'loom-key-guard disarm'."
                  break
              fi
          done
      }

      # ---------------------------------------------------------------------
      # The loop
      # ---------------------------------------------------------------------
      watch() {
          local misses=0 failures=0

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
                      retire_deadline
                      set_state disarmed
                      announce "[loom] Key guard disarmed. Removing the USB key will not power this box off."
                  fi
              elif [[ "$(current_state)" != "armed" ]]; then
                  if arm_once; then
                      misses=0
                      failures=0
                      REPORTED_REASON=""
                      retire_deadline
                  else
                      failures=$((failures + 1))
                      # Not on the first failure: the key device is still
                      # enumerating for the first seconds after a switch-root,
                      # and publishing `idle` redraws the login screen with it.
                      if [[ "''${failures}" -eq "''${SETTLE_TICKS}" ]]; then
                          REPORTED_REASON="''${ARM_REASON}"
                          set_state idle
                          # Once, not every two seconds for the life of the
                          # box. This is the ordinary state of a box booted
                          # with the recovery passphrase, and it is not an
                          # error.
                          printf '[loom] No usable key at %s; the guard stays idle (%s).\n' \
                              "''${KEY_DEVICE}" "''${ARM_REASON}"
                      elif [[ "''${failures}" -gt "''${SETTLE_TICKS}" && "''${ARM_REASON}" != "''${REPORTED_REASON}" ]]; then
                          REPORTED_REASON="''${ARM_REASON}"
                          printf '[loom] Key guard still cannot arm: %s.\n' "''${ARM_REASON}"
                      fi
                      countdown
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
                      failures=0
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
              # Warn-only, which only a `--debug` image gets: that image has
              # already traded the appliance's guarantees for hands-on access,
              # and a box being driven by hand is one where a pulled stick is
              # usually the operator's own doing.
              set_state idle
              announce "[loom] USB key gone for ''${GRACE_SECONDS}s. This --debug image only warns; the box stays up."
              return 0
          fi

          power_off_now "[loom] USB key gone for ''${GRACE_SECONDS}s. Powering off now."
      }

      power_off_now() {
          announce "''${1}"
          set_state tripped
          # A clean poweroff, not a forced one: unit teardown is bounded by
          # DefaultTimeoutStopSec, and the indexed data is worth more than the
          # seconds a sysrq would save.
          systemctl poweroff
          exit 0
      }

      status() {
          local state device expires left
          state="$(current_state)"
          device="$(cat "''${DEVICE_FILE}" 2>/dev/null || true)"

          printf 'loom-key-guard: %s\n' "''${state}"
          printf '  key device:  %s\n' "''${KEY_DEVICE}"
          if [[ -n "''${device}" ]]; then
              printf '  resolved to: %s\n' "''${device}"
          fi
          printf '  on removal:  %s after %ss\n' "''${ACTION}" "''${GRACE_SECONDS}"
          if [[ -e "''${DEADLINE_FILE}" ]]; then
              expires="$(cat "''${DEADLINE_FILE}")"
              left=$((expires - $(date +%s)))
              [[ "''${left}" -ge 0 ]] || left=0
              printf '  arm deadline: powers off in %ss unless the key arms\n' "''${left}"
          fi
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

        `poweroff` in every mode, first-time setup included: the stick is what
        the box is entitled to run from, and which mode it happens to be in
        does not change that.

        `debug.nix` forces `warn`, and is the only thing that does. Such an
        image has already traded the appliance's guarantees for hands-on
        access, and powering a box off under the operator driving it is not
        protecting anything that image still claims to protect.

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

    armSettleTicks = lib.mkOption {
      type = lib.types.ints.positive;
      default = 5;
      internal = true;
      description = ''
        Consecutive failed arm attempts before the guard publishes `idle`.

        Not zero on purpose: nothing orders this unit after the key's .device
        unit, so the first ticks of a boot routinely run before udev has
        recreated the partlabel link. Publishing `idle` redraws the login
        screen, and a box that armed two seconds later would have left that
        screen contradicting itself until something else repainted it.
      '';
    };

    armDeadlineSec = lib.mkOption {
      type = lib.types.ints.unsigned;
      default = 180;
      internal = true;
      description = ''
        How long a box that booted from the stick may run without the guard
        arming before it powers itself off. `0` disables the deadline.

        Enforced only where `action` is `poweroff` -- so a `--debug` image is
        exempt, as it is on removal -- and only where stage 1 left
        `witnessFile` behind. A box booted on the recovery passphrase has no
        stick to arm on and is left up for repairs.

        `loom-key-guard disarm` settles it for the rest of the boot, and is
        what an operator who means to run without a key reaches for.
      '';
    };

    witnessFile = lib.mkOption {
      type = lib.types.str;
      default = "${cfg.stateDir}/booted-with-key";
      defaultText = lib.literalExpression ''"''${config.loom.keyGuard.stateDir}/booted-with-key"'';
      readOnly = true;
      internal = true;
      description = ''
        Where stage 1 records that the key partition was present when the root
        was unlocked. Written by box-hardware.nix, read by `armDeadlineSec`.

        In /run, which is carried across the switch-root, and an option rather
        than a literal in two files so the initrd and the guard cannot name
        different paths.
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
      default = config.loom.storage.rootDevice;
      defaultText = lib.literalExpression "config.loom.storage.rootDevice";
      internal = true;
      description = ''
        The LUKS container the key belongs to. The guard opens it with
        `--test-passphrase` when arming, which is what proves the stick still
        unlocks this particular disk.

        Taken from storage.nix rather than named here: the container sits on a
        logical volume whose name the installer also has to know, and one of the
        two spellings being wrong produces a box that boots and then powers
        itself off ten seconds later.
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

        Under `--lock-key` the partition holds a LUKS2 container rather than the
        key, and this many bytes of its header are what `read_fingerprint`
        identifies the stick by instead.
      '';
    };

    requireKeyOracle = lib.mkOption {
      type = lib.types.bool;
      default = !config.loom.keyStore.enable;
      defaultText = lib.literalExpression "!config.loom.keyStore.enable";
      internal = true;
      description = ''
        Whether arming has to prove the stick unlocks `rootDevice`, rather than
        only that it carries key material.

        True is the stronger check and the default. It goes false under
        `--lock-key`, where the partition is a passphrase-locked container: the
        guard has no plaintext key to authenticate with, and deliberately keeps
        none. See `arm_once` for why the weaker check is enough there.
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
