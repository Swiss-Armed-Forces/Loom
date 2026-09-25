# The optional passphrase over the stick's LUKS key.
#
# Off unless the image was built with `build-appliance-image --lock-key`. With
# it, the 4096 key bytes are no longer written raw onto the stick's `loom-key`
# partition: the partition becomes a LUKS2 container of its own, and the bytes
# live inside it. Getting at them costs a word passphrase that the build script
# generated and printed, and that exists nowhere on the stick.
#
# What that buys is the one thing the stick could not do before. Unlocked, it is
# a bearer token: whoever holds it unlocks the box, which is why the threat model
# (Documentation/appliance.md) has to assume the stick "is removed, or travels
# separately, whenever the box is unattended". Locked, the stick is one factor of
# two -- something you have plus something you know -- so a stick found in a
# drawer, a stick stolen together with the box, and a leaked `--key-backup` file
# all stop being enough on their own.
#
# What it costs is unattended boot. The box stops at a passphrase prompt in stage
# 1, so it does not come back on its own after a power cut, and the key guard's
# poweroff now needs a human to undo. That is the whole reason this is opt-in.
#
# Two things it deliberately does NOT change:
#
#   * The recovery passphrase. It stays a second keyslot on the *root*, enrolled
#     by the installer and printed on every console login, so it remains a
#     single-factor way in for anyone who saw it. Removing it would make a dead
#     stick unrecoverable, which is a worse failure than the one it leaves open.
#   * What the key guard watches. It keeps reading the physical partition rather
#     than anything unlocked -- see key-guard.nix's `arm_once`.
#
# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------
#
# Everything downstream wants the same thing: a path holding the 4096 plaintext
# key bytes at offset 0. Today that path is the partition. Under this flag it
# becomes something unlocked from it, and *only the path changes*:
#
#   initrd     -> `plainKeyFile` on a ramfs, written by the unit below
#   installer  -> /dev/mapper/${mapping}, opened by loom_installer/keystore.py
#   key guard  -> still the partition itself
#
# That is what keeps install.py's `encrypt`, `enroll_recovery_passphrase` and
# storage.py's `pool_claimed_by_key` untouched by this feature: all three already
# take the key device as a parameter.
#
# ---------------------------------------------------------------------------
# Why a unit of our own rather than a second luks.devices entry
# ---------------------------------------------------------------------------
#
# The obvious spelling is to declare the key partition as a second
# `boot.initrd.luks.devices` entry and point `cryptroot`'s `keyFile` at the
# mapping it produces. It does not work reliably: nixpkgs renders every entry
# into one flat /etc/crypttab (luksroot.nix `stage1Crypttab`) with no ordering
# between the lines, and systemd-cryptsetup-generator derives dependencies from
# the *device* column, not the key file column. `cryptroot` would race the
# mapping it depends on, and the fix would be a drop-in overriding a unit the
# generator produces.
#
# So this takes the shape nixpkgs already ships for the same problem: clevis
# (luksroot.nix, `cryptsetup-clevis-${name}`) runs a unit of its own before
# `systemd-cryptsetup@` and leaves a decrypted key file on a ramfs for it to
# find. Same ordering, same ramfs, same one-line change at the `keyFile` end --
# and it is a path nixpkgs keeps working rather than one we have to defend.
{
  config,
  lib,
  pkgs,
  utils,
  lockKey,
  ...
}:
let
  cfg = config.loom.keyStore;
  guard = config.loom.keyGuard;

  # The .device unit stage 1 has to wait for before there is anything to unlock.
  # Escaped by systemd's rules rather than by hand: the path carries two dashes,
  # each of which becomes \x2d, and getting that wrong produces a unit name that
  # never becomes active and a boot that hangs until the device timeout.
  keyDeviceUnit = "${utils.escapeSystemdPath guard.keyDevice}.device";

  keyDirectory = builtins.dirOf cfg.plainKeyFile;
in
{
  options.loom.keyStore = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = lockKey;
      internal = true;
      description = ''
        Whether the stick's key partition is a LUKS2 container holding the key
        bytes, rather than the bytes themselves. Set by
        `build-appliance-image --lock-key`; off in every other image.
      '';
    };

    mapping = lib.mkOption {
      type = lib.types.str;
      default = "loom-keystore";
      readOnly = true;
      internal = true;
      description = ''
        The device-mapper name the key container is opened under, by the initrd
        unit below and by the installer.

        Dash-free requirements do not apply here the way they do to
        `loom.storage.volumeGroup`: this is a plain dm name with no volume group
        in front of it, so /dev/mapper/${cfg.mapping} is exactly this string.
      '';
    };

    plainKeyFile = lib.mkOption {
      type = lib.types.str;
      default = "/loom-keystore/key";
      readOnly = true;
      internal = true;
      description = ''
        Where stage 1 leaves the unlocked key bytes for systemd-cryptsetup to
        read. On a ramfs, which is never swapped and never written back, and
        which the switch-root frees along with the rest of the initrd.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    # The `cryptsetup` CLI, which the initrd does not otherwise carry. Declaring
    # a LUKS device gets systemd-cryptsetup and libcryptsetup in
    # (luksroot.nix's `storePaths`), but not the command -- and this unit needs
    # the command, because what it is doing is not a crypttab entry.
    boot.initrd.systemd.initrdBin = [ pkgs.cryptsetup ];

    # Not `systemd.services`: this exists only inside the initrd, which is the
    # only place the key is ever plaintext on this box.
    boot.initrd.systemd.services.loom-keystore = {
      description = "Unlock the Loom key store on the USB stick";

      # The ordering that makes this work at all, copied from nixpkgs' clevis
      # unit deliberately -- see the header. `wantedBy` + `before` pull this in
      # ahead of the root's own cryptsetup unit; naming the two shutdown targets
      # in both `before` and `conflicts` is what keeps a DefaultDependencies=no
      # unit from being left running into a switch-root.
      wantedBy = [ "systemd-cryptsetup@cryptroot.service" ];
      before = [
        "systemd-cryptsetup@cryptroot.service"
        "initrd-switch-root.target"
        "shutdown.target"
      ];
      conflicts = [
        "initrd-switch-root.target"
        "shutdown.target"
      ];

      # `requires` rather than `wants`, and on the .device unit rather than on a
      # timer: a stick that has not enumerated yet is the normal case on USB,
      # and this is what makes stage 1 wait for it instead of failing straight
      # into the recovery prompt. box-hardware.nix's DefaultDeviceTimeoutSec is
      # the budget; when it runs out, the recovery prompt is the right answer.
      requires = [ keyDeviceUnit ];
      after = [ keyDeviceUnit ];

      unitConfig.DefaultDependencies = "no";
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStop = "${config.boot.initrd.systemd.package.util-linux}/bin/umount ${keyDirectory}";
      };

      # PATH is /bin:/sbin in the initrd, which carries coreutils and systemd
      # (`systemd-ask-password`) by default, `mount` through `extraBin`, and
      # `cryptsetup` through the `initrdBin` above.
      script = ''
        mkdir --parents ${lib.escapeShellArg keyDirectory}
        # ramfs, not tmpfs: tmpfs pages can be swapped, and while the installed
        # box has no swap (box-hardware.nix) that is a property of the system
        # this is about to boot, not of the initrd doing the booting.
        mount -t ramfs none ${lib.escapeShellArg keyDirectory}
        umask 277

        # The same password-agent protocol systemd-cryptsetup itself speaks, so
        # the box asks for this exactly the way it asks for the recovery
        # passphrase -- through plymouth when run mode's splash is up, and on
        # the console when it is not (setup mode, --debug).
        passphrase="$(systemd-ask-password --id=loom-keystore \
          "Loom key stick passphrase:")"

        # Through a pipe, so the passphrase is never a path in /proc and never
        # an argument any other process can read.
        printf '%s' "$passphrase" | cryptsetup open \
          --type luks2 \
          --key-file - \
          ${lib.escapeShellArg guard.keyDevice} ${lib.escapeShellArg cfg.mapping}

        dd if=/dev/mapper/${lib.escapeShellArg cfg.mapping} \
          of=${lib.escapeShellArg cfg.plainKeyFile} \
          bs=${toString guard.keyBytes} count=1 status=none

        # Closed immediately. Stage 1 has what it needs, and leaving the mapping
        # open would carry a second route to the key bytes across the switch-root
        # and keep it there for the life of the box.
        cryptsetup close ${lib.escapeShellArg cfg.mapping}
      '';
    };

    assertions = [
      {
        # The guard reads the container's header as the stick's identity, and
        # the header is only as long as the read. Nothing sets keyBytes today,
        # but a future value under 512 would read less than one LUKS2 header
        # sector and start fingerprinting a constant.
        assertion = guard.keyBytes >= 512;
        message =
          "nixos: loom.keyGuard.keyBytes is ${toString guard.keyBytes}, which is too small to "
          + "identify a LUKS2 container by its header. --lock-key needs at least 512.";
      }
    ];
  };
}
