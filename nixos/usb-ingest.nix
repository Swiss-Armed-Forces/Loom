# Automatic ingest of USB media.
#
# Plug a stick into a running appliance and its contents are mounted read-only,
# copied into the `loom-intake` bucket under `usb-crawled/<name>-<id>/`, and
# indexed. This is the only way data reaches a box that has no remote access and
# whose operator arrives carrying media rather than a laptop.
#
# Two properties this module exists to hold:
#
#   * The LUKS key stick is never touched. key-guard.nix powers the box off ten
#     seconds after the key stops reading, so this is not a cosmetic concern. The
#     exclusion uses the guard's own `device` file -- the node it armed on, proven
#     against the LUKS header -- and NOT /dev/disk/by-partlabel/loom-key, which
#     key-guard.nix documents as non-unique when two Loom sticks are attached.
#
#   * Media is never written to. Read-only mounts, `blockdev --setro` underneath
#     them, and per-filesystem options that suppress journal replay -- because a
#     dirty ext4/xfs/btrfs volume mounted with plain `-o ro` still writes.
#
# THIS CHANGES THE BOX'S THREAT MODEL and is on in every image. A USB port becomes
# an unauthenticated data-injection path, and filesystem drivers parse media
# supplied by whoever is standing at the box. See Documentation/appliance.md.
{
  config,
  lib,
  pkgs,
  loomUser,
  loomNamespace,
  ...
}:
let
  cfg = config.loom.usbIngest;

  # Everything the service shells out to. A unit's PATH is built from its own
  # `path` plus a minimal default -- /run/current-system/sw/bin is never on it --
  # which is the drift that once shipped a box whose loom.service died on
  # `awk: command not found` (box.nix, `loom.toolchain`). Here the list is baked
  # into the wrapper instead, so it cannot be out of step with the unit.
  runtimeInputs = with pkgs; [
    coreutils
    util-linux # lsblk, blkid, mount, umount, findmnt, blockdev, wall
    systemd # udevadm
    minio-client # mc
    kubectl # reads the cluster CA out of the k8s secret
    tmux # notices into the operator's console session

    # Filesystem drivers and helpers. The in-kernel ones need no package; these
    # are the userspace halves.
    ntfs3g # mount.ntfs-3g -- NTFS in FUSE, deliberately not kernel ntfs3
    exfatprogs
    dosfstools
    e2fsprogs
    xfsprogs
    btrfs-progs
    f2fs-tools
    udftools
    fuse3

    # Best effort, and the only way to read a modern Mac volume at all: there is
    # no in-kernel APFS driver. Listed unconditionally rather than behind a
    # `pkgs ? apfs-fuse` guard, so that losing it from nixpkgs fails the build
    # instead of quietly shipping a box that skips every Mac disk it is handed.
    apfs-fuse
  ];

  loom-usb-ingest = pkgs.python3Packages.buildPythonApplication {
    pname = "loom-usb-ingest";
    version = "0.1.0";
    src = ./usb-ingest;
    pyproject = true;

    build-system = [ pkgs.python3Packages.setuptools ];
    # The console pane the copy is drawn in (loom_usb_ingest/watch.py).
    dependencies = [ pkgs.python3Packages.rich ];
    nativeCheckInputs = [ pkgs.python3Packages.pytest ];

    # The pure logic -- the name sanitiser, the filesystem table and the
    # exclusion rules -- is tested here rather than in the VM test, so a mistake
    # in it fails the build in seconds instead of at boot.
    checkPhase = ''
      runHook preCheck
      # Appended rather than assigned: an assignment would drop the paths the
      # python setup hook exported for this package's own dependencies, and the
      # suite would fail to import them.
      PYTHONPATH=$PWD''${PYTHONPATH:+:$PYTHONPATH} pytest tests -q
      runHook postCheck
    '';

    makeWrapperArgs = [
      "--prefix PATH : ${lib.makeBinPath runtimeInputs}"
    ];

    meta.mainProgram = "loom-usb-ingest";
  };

  ingestArgs = lib.concatStringsSep " " [
    "--bucket ${lib.escapeShellArg cfg.bucket}"
    "--endpoint ${lib.escapeShellArg cfg.endpoint}"
    "--prefix ${lib.escapeShellArg cfg.prefix}"
    "--namespace ${lib.escapeShellArg loomNamespace}"
    "--kubeconfig ${lib.escapeShellArg cfg.kubeconfig}"
    "--mount-root ${lib.escapeShellArg cfg.mountRoot}"
    "--state-dir ${lib.escapeShellArg cfg.stateDir}"
    "--key-guard-state-dir ${lib.escapeShellArg config.loom.keyGuard.stateDir}"
    "--console-socket ${lib.escapeShellArg config.loom.consoleSocket}"
    "--progress-dir ${lib.escapeShellArg cfg.progressDir}"
    "--owner ${lib.escapeShellArg loomUser}"
  ];

  loom-usb-status = pkgs.writeShellApplication {
    name = "loom-usb-status";
    runtimeInputs = with pkgs; [
      coreutils
      jq
    ];
    text = ''
      state=${lib.escapeShellArg "${cfg.stateDir}/state.json"}
      if [ ! -e "''${state}" ]; then
        printf 'loom-usb-ingest: nothing ingested since boot.\n'
        exit 0
      fi
      jq --raw-output '
        "loom-usb-ingest: \(.status)",
        "  device:   \(.device)",
        "  prefix:   \(.prefix)",
        "  objects:  \(.objects)",
        "  failures: \(.failures)"
      ' <"''${state}"
    '';
  };
in
{
  options.loom.usbIngest = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      internal = true;
      description = ''
        Mount and ingest USB media automatically.

        On in every image. It is an option rather than a literal so that the VM
        test can exercise a box without it, and so that a box being debugged by
        hand can be told to leave media alone.
      '';
    };

    bucket = lib.mkOption {
      type = lib.types.str;
      default = "loom-intake";
      internal = true;
      description = ''
        The bucket the crawler watches. Must match `intake_storage.bucket_name`
        in backend/common/common/settings.py, which charts/values.yaml leaves at
        its default.
      '';
    };

    endpoint = lib.mkOption {
      type = lib.types.str;
      default = "https://s3.loom";
      internal = true;
      description = ''
        SeaweedFS's S3 gateway, through the appliance's own ingress. https
        because every ingress in charts/values.yaml is annotated
        `router.entrypoints: websecure` and nothing answers on port 80.
      '';
    };

    prefix = lib.mkOption {
      type = lib.types.str;
      default = "usb-crawled";
      internal = true;
      description = ''
        Key prefix for everything ingested from USB. The crawler renders an
        object's key as the file's path, so this is what an operator sees in the
        frontend.
      '';
    };

    mountRoot = lib.mkOption {
      type = lib.types.str;
      default = "/run/loom/usb";
      internal = true;
      description = ''
        Where media is mounted. On tmpfs under console.nix's /run/loom, so no
        mount of somebody else's filesystem survives a reboot.
      '';
    };

    stateDir = lib.mkOption {
      type = lib.types.str;
      default = "/run/loom/usb";
      internal = true;
      description = "Where the lock, the mc configuration and state.json live.";
    };

    progressDir = lib.mkOption {
      type = lib.types.str;
      default = "/run/loom/usb-progress";
      internal = true;
      description = ''
        Where the copy publishes what it is doing, for the console pane.

        Deliberately not under `stateDir`: that is 0700 root, and the pane is drawn
        by a process the operator's tmux server spawns, which therefore runs as the
        operator. What is in here is byte counts and device paths -- see
        loom_usb_ingest/progress.py.
      '';
    };

    kubeconfig = lib.mkOption {
      type = lib.types.str;
      default = "/home/${loomUser}/.kube/config";
      internal = true;
      description = ''
        Used only to read the cluster CA out of its secret, the same way
        console.nix's loom-chat does. The unit runs as root, which can read the
        operator's minikube client certificates.
      '';
    };
  };

  # Run mode only. Setup mode is a DHCP client on somebody else's network pulling
  # container images for hours, with no cluster to ingest into and no business
  # touching media.
  config = lib.mkIf (cfg.enable && config.loom.mode == "run") {
    environment.systemPackages = [
      loom-usb-ingest
      loom-usb-status
    ];

    # The userspace halves of the filesystems above: mount helpers and fsck
    # binaries, wired into system.fsPackages by this option.
    #
    # Note this is the *system* set, not boot.initrd.supportedFilesystems --
    # box-hardware.nix owns the initrd, and tests/appliance-usb-ingest.nix
    # asserts this does not grow it.
    boot.supportedFilesystems = {
      vfat = true;
      exfat = true;
      ntfs = true;
      ext4 = true;
      xfs = true;
      btrfs = true;
      f2fs = true;
      hfs = true;
      hfsplus = true;
      iso9660 = true;
      udf = true;
    };

    # 0700 root inside console.nix's 0700 /run/loom. Nothing here is for the
    # operator to read directly -- loom-usb-status is.
    systemd.tmpfiles.rules = [
      "d ${cfg.mountRoot} 0700 root root -"
      "d ${cfg.stateDir} 0700 root root -"
      # Readable by the operator, unlike the two above: see `progressDir`.
      "d ${cfg.progressDir} 0755 root root -"
    ];

    # Whole disks, not partitions. The service enumerates volumes itself, which
    # is what lets one stick produce one prefix and one provenance manifest
    # however many partitions it carries.
    #
    # %k rather than $env{DEVNAME}: the kernel name (`sdb`) needs no unit-name
    # escaping, where a path (`/dev/sdb`) would.
    services.udev.extraRules = ''
      ACTION=="add", SUBSYSTEM=="block", ENV{ID_BUS}=="usb", ENV{DEVTYPE}=="disk", \
        TAG+="systemd", ENV{SYSTEMD_WANTS}+="loom-usb-ingest@%k.service"
    '';

    systemd.services."loom-usb-ingest@" = {
      description = "Ingest USB media at /dev/%i into Loom";

      # The guard has to have had its say before anything decides what the key
      # stick is; the service itself waits on the state file as well, because
      # ordering after the unit only guarantees it started.
      after = [
        "loom-key-guard.service"
        "loom.service"
      ];

      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${lib.getExe loom-usb-ingest} ${ingestArgs} /dev/%i";

        # Unmount whatever this device left behind, including when the operator
        # pulled it mid-copy, and take its line out of the console pane. Unlike the
        # ExecStopPost case key-guard.nix warns about, firing these on an ordinary
        # shutdown is harmless.
        ExecStopPost = [
          "-${pkgs.util-linux}/bin/umount --recursive --lazy ${cfg.mountRoot}/%i"
          "-${lib.getExe loom-usb-ingest} ${ingestArgs} --release /dev/%i"
        ];

        # A 2 TB drive is a long copy, and so is waiting for the cluster to come
        # up. Same stance modes.nix takes for loom.service.
        TimeoutStartSec = "infinity";

        # Journal only. modes.nix and network.nix both explain why: with no
        # `console=` on the kernel command line, "console" means the active VT,
        # and this would paint over the operator's session.
        StandardOutput = "journal";
        StandardError = "journal";

        # Failures are reported to the console and to the journal, not retried
        # into a loop against media that is probably unreadable.
        Restart = "no";

        # Deliberately light. The mount itself needs CAP_SYS_ADMIN and the FUSE
        # helpers need /dev/fuse, so the sandboxing that would actually matter
        # here is not available; pretending otherwise would only break mounts.
        ProtectHome = "read-only";
        PrivateTmp = true;
      };
    };
  };
}
