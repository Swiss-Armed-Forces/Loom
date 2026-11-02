# The USB key has to stay plugged in.
#
# The root is LUKS2 and its key is 4096 bytes on the stick's `loom-key`
# partition -- under `--lock-key`, 4096 bytes inside a container on that
# partition -- but that key is read exactly once, by systemd-cryptsetup in stage
# 1 (box-hardware.nix). After switch-root nothing touches the stick again: the
# ESP is on the internal disk, and the installer moves its own loader off the
# removable-media path. So pulling the stick arms only the *next* boot; without
# this module the box goes on running indefinitely on an unlocked dm-crypt
# mapping with no key present.
#
# That is the gap this module closes, and it is the gap the threat model in
# Documentation/appliance.md assumes is closed: "the design assumes the stick is
# removed, or travels separately, whenever the box is unattended".
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
    # The values the script needs, and nothing else: the names derived from them
    # are declared in the file itself, where the linter can see them. The header
    # there says why the body is a file rather than a string.
    text = ''
      LOOM_STATE_DIR=${lib.escapeShellArg cfg.stateDir}
      LOOM_KEY_DEVICE=${lib.escapeShellArg cfg.keyDevice}
      LOOM_ROOT_DEVICE=${lib.escapeShellArg cfg.rootDevice}
      LOOM_KEY_BYTES=${toString cfg.keyBytes}
      LOOM_INTERVAL=${toString cfg.intervalSec}
      LOOM_GRACE_TICKS=${toString cfg.graceTicks}
      LOOM_GRACE_SECONDS=${toString graceSeconds}
      LOOM_KEY_ORACLE=${lib.boolToString cfg.requireKeyOracle}
      LOOM_ACTION=${lib.escapeShellArg cfg.action}
      LOOM_SOCKET=${lib.escapeShellArg config.loom.consoleSocket}
      LOOM_WITNESS_FILE=${lib.escapeShellArg cfg.witnessFile}
      LOOM_ARM_DEADLINE=${toString cfg.armDeadlineSec}
      LOOM_SETTLE_TICKS=${toString cfg.armSettleTicks}
      LOOM_BANNER_REFRESH=${lib.getExe config.loom.bannerRefresh}

      ${builtins.readFile ./scripts/loom_key_guard.sh}'';
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
        # Journal only. console.nix keeps /dev/console off tty1 so that units do
        # not paint over the operator's session; the guard reaches a human
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
