# What the installer lays down on the internal disks, and whether the box could
# ever find it again.
#
# The layout is the one thing in this directory with no second chance. A box
# whose pool does not come up has no sshd, no nixos-rebuild and no console
# session -- stage 1 simply stops, and the way back is a reinstall that destroys
# the data. So the assertions here are one question asked from several angles:
# does what install.sh creates match what box-hardware.nix waits for?
#
# `rootDevice` and the two names behind it are passed in from default.nix, taken
# off the *appliance's* evaluated configuration rather than restated here. A test
# that spelled the path itself could agree with neither side and still pass.
#
# The installer image is deliberately not booted. It wants an NVMe the test
# framework cannot supply -- `target_disks` accepts nothing else, on purpose --
# and a whole box closure to copy. What is worth testing is the layout, and the
# layout is reachable by sourcing the scripts, which is why install.sh and
# wipe.sh guard their `main` call.
{
  pkgs,
  volumeGroup,
  rootVolume,
  rootDevice,
}:
let
  # Where the node finds the scripts under test. On a real stick they come from
  # installer.nix's wrapProgram, which also supplies the environment below.
  scriptDir = "/etc/loom/installer-scripts";

  # Two scratch disks, in MB. Over a gigabyte because the first one carries the
  # 1G ESP before it contributes anything to the pool; no larger, because
  # nothing here calls check_pool_size and its 250 GB minimum would buy only
  # build time.
  diskMb = 2048;
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-install";

  nodes.installer = {
    virtualisation.memorySize = 1024;
    virtualisation.emptyDiskImages = [
      diskMb
      diskMb
    ];

    # What installer.nix puts on the scripts' PATH, minus the parts only a real
    # install reaches for (nixos-install, efibootmgr, nvme-cli).
    environment.systemPackages = with pkgs; [
      cryptsetup
      dosfstools
      e2fsprogs
      gptfdisk
      lvm2
      parted
      util-linux
    ];

    environment.etc."loom/installer-scripts".source = ../installer-scripts;
  };

  testScript = ''
    start_all()
    installer.wait_for_unit("multi-user.target")

    # vda is the node's own root and is never named below.
    DISKS = ["/dev/vdb", "/dev/vdc"]

    # The environment installer.nix's wrapProgram would have set. The three
    # storage names reach this test from the appliance's own configuration by
    # way of default.nix, so a rename in nixos/storage.nix arrives here rather
    # than leaving a literal somebody has to remember to update.
    ENV = " ".join([
        "LOOM_INSTALLER_LIB=${scriptDir}",
        "LOOM_INSTALLER_BIN=${scriptDir}",
        "LOOM_EFI_ARCH=x64",
        "LOOM_TAG=test",
        "LOOM_PLATFORM=test",
        "LOOM_AUTO_GRACE=1",
        "LOOM_VG_NAME=${volumeGroup}",
        "LOOM_LV_NAME=${rootVolume}",
        "LOOM_ROOT_DEVICE=${rootDevice}",
    ])

    def sourced(script: str, snippet: str) -> str:
        """Run a snippet with one installer script's functions in scope."""
        return installer.succeed(
            f"env {ENV} bash -c 'set -euo pipefail; "
            f"source ${scriptDir}/{script}; {snippet}'"
        )

    def install_sh(snippet: str) -> str:
        return sourced("install.sh", snippet)

    # The stick's key partition, as a plain file: install.sh reads 4096 bytes of
    # it exactly as systemd-cryptsetup will in stage 1, and cryptsetup does not
    # care which kind of thing it was handed.
    installer.succeed("dd if=/dev/urandom of=/tmp/key bs=4096 count=1 status=none")
    installer.succeed("dd if=/dev/urandom of=/tmp/other-key bs=4096 count=1 status=none")

    with subtest("every eligible disk joins one volume group"):
        install_sh(f"partition {' '.join(DISKS)}")
        install_sh(f"create_pool {len(DISKS)}")

        # Both members, not just the first. A pool that silently forms over one
        # disk and leaves the second unused looks, from the console, exactly
        # like a working install.
        pv_count = installer.succeed(
            "vgs --noheadings -o pv_count ${volumeGroup}"
        ).strip()
        assert pv_count == str(len(DISKS)), f"volume group spans {pv_count} PVs"

        pvs = installer.succeed("pvs --noheadings -o pv_name,vg_name")
        for disk in DISKS:
            assert disk in pvs, f"{disk} is not a physical volume:\n{pvs}"

        # And the volume takes the whole group. Extents left behind would cost
        # the operator disk space that nothing would ever report as missing.
        free = installer.succeed(
            "vgs --noheadings --nosuffix --units b -o vg_free ${volumeGroup}"
        ).strip()
        assert free == "0", f"{free} bytes left unallocated"

    with subtest("the ESP lands on the first disk and only the first"):
        installer.succeed("test -b /dev/disk/by-partlabel/loom-esp")
        esp_parent = installer.succeed(
            "lsblk --noheadings --raw --paths --output PKNAME "
            "/dev/disk/by-partlabel/loom-esp | head -1"
        ).strip()
        assert esp_parent == DISKS[0], f"ESP is on {esp_parent}, not {DISKS[0]}"

    with subtest("the container is exactly where the box will look for it"):
        # The assertion this file exists for. rootDevice comes off the
        # appliance's own configuration, so this is box-hardware.nix's stage-1
        # device and the key guard's device, not a string chosen here.
        installer.succeed("test -b ${rootDevice}")
        install_sh("encrypt /tmp/key")
        installer.succeed("cryptsetup isLuks ${rootDevice}")
        installer.succeed("test -b /dev/mapper/cryptroot")

        # The filesystem goes on the mapping, not on a partition.
        install_sh("make_filesystems")
        fstype = installer.succeed(
            "lsblk --noheadings --raw --output FSTYPE /dev/mapper/cryptroot"
        ).strip()
        assert fstype == "ext4", f"root filesystem is {fstype}"

    with subtest("the recovery passphrase opens the same container"):
        # Losing the stick must not mean losing the box. The keyslot is enrolled
        # against the pooled container now, so one added to the wrong device
        # would leave the passphrase on the login banner useless -- and nothing
        # would say so until somebody needed it.
        install_sh("mount_target")
        passphrase = install_sh("enroll_recovery_passphrase /tmp/key").strip()
        assert len(passphrase.split("-")) == 6, passphrase
        installer.succeed("test -s /mnt/var/lib/loom/recovery-passphrase")
        install_sh("unmount_target")

        # unmount_target also deactivates the group, so the container has to be
        # brought back before it can be opened -- which is itself worth
        # asserting: an installer that left the pool active would leave the
        # partition tables busy for whatever the operator picks next.
        installer.fail("test -b ${rootDevice}")
        installer.succeed("vgchange --activate y ${volumeGroup}")
        installer.succeed(f"printf %s {passphrase} >/tmp/pass")
        installer.succeed(
            "cryptsetup luksOpen --test-passphrase --key-file /tmp/pass ${rootDevice}"
        )

    with subtest("a stick recognises the box it installed, and only that box"):
        # The guard that replaces the typed INSTALL word. It has to answer yes
        # to the key that built this pool and no to any other, or an unattended
        # install either destroys a working box or refuses to provision a new
        # one.
        claimed = install_sh("pool_claimed_by_key /tmp/key").strip()
        assert claimed == "yes", claimed

        foreign = install_sh("pool_claimed_by_key /tmp/other-key").strip()
        assert foreign == "no", foreign

        # Looking must not leave the box changed.
        installer.fail("test -b ${rootDevice}")

    with subtest("the wipe still reaches the key material"):
        # The regression this guards: the container moved onto a logical volume,
        # so wipe_disk's per-partition sweep no longer finds it. With layer 1
        # skipped the wipe says nothing and falls through to layers that are
        # slower and weaker -- a silent downgrade of the only step that matters.
        sourced("wipe.sh", "erase_pool_keys")
        installer.fail("vgs ${volumeGroup}")
        installer.succeed("vgchange --activate y ${volumeGroup} || true")
        installer.fail("test -b ${rootDevice}")

    with subtest("a single-disk box gets the same layout"):
        # One closure serves both, which is why the disks are pooled rather than
        # a second image built for boxes with two slots. The device path must
        # not depend on how many disks were found.
        installer.succeed(f"sgdisk --zap-all {DISKS[1]}")
        install_sh(f"partition {DISKS[0]}")
        install_sh("create_pool 1")

        installer.succeed("test -b ${rootDevice}")
        pv_count = installer.succeed(
            "vgs --noheadings -o pv_count ${volumeGroup}"
        ).strip()
        assert pv_count == "1", pv_count
  '';
}
