# Where the appliance's data lives, named once.
#
# The installer builds the layout and the box boots it, and the two are written
# in different languages on different media -- so the names have to come from
# one place or they drift into a box that partitions perfectly and then cannot
# find its own root. installer.nix passes these through `wrapProgram` to the
# scripts on the stick, exactly as it already does for the EFI architecture and
# the setup specialisation.
#
# The layout itself:
#
#   nvme0n1  p1 loom-esp  (1G, vfat)
#            p2 loom-pv0  ----+
#   nvme1n1  p1 loom-pv1  ----+--> VG --> LV --> LUKS2 --> ext4
#
# The key that opens that LUKS2 container is on the stick, and `--lock-key`
# (key-store.nix) puts a second container in front of it. Nothing in this file
# changes either way: what varies is the path the key bytes are read from, never
# the layout below.
#
# LUKS sits on *top* of LVM, which is the inverse of the usual NixOS recipe, and
# the reason is the one invariant this whole directory is built around: a single
# system closure serves every box. `boot.initrd.luks.devices` is static
# configuration, but how many M.2 slots a box has populated is not known when
# that closure is built. LVM-inside-LUKS would need one `luks.devices` entry per
# disk, and a one-disk box booting a two-entry closure blocks in stage 1 forever
# on a .device unit that never appears. Pooling first leaves exactly one
# container, one keyslot, one recovery passphrase and one device path -- for one
# disk or for three.
#
# Nothing has to be enabled for this to boot. nixpkgs' luksroot.nix sets
# `services.lvm.enable` and `boot.initrd.services.lvm.enable` unconditionally
# whenever any LUKS device is declared, so lvm2's udev rules and binaries are
# already in the appliance's initrd, and event-based autoactivation brings the
# volume up before systemd-cryptsetup asks for it.
{ config, lib, ... }:
let
  cfg = config.loom.storage;
in
{
  options.loom.storage = {
    volumeGroup = lib.mkOption {
      type = lib.types.str;
      default = "loom";
      internal = true;
      description = ''
        The volume group the installer creates across every eligible internal
        disk.

        Keep it free of dashes. LVM escapes `-` as `--` when it composes the
        /dev/mapper name, so a group called `loom-pool` would appear as
        `/dev/mapper/loom--pool-root` and `rootDevice` below would be wrong in a
        way that only shows up on a box that will not boot.
      '';
    };

    rootVolume = lib.mkOption {
      type = lib.types.str;
      default = "root";
      internal = true;
      description = ''
        The logical volume holding the LUKS container. Takes the whole group;
        allocation is linear rather than striped, so disks of different sizes
        are used to the last extent.

        Dash-free for the same reason as `volumeGroup`.
      '';
    };

    rootDevice = lib.mkOption {
      type = lib.types.str;
      default = "/dev/mapper/${cfg.volumeGroup}-${cfg.rootVolume}";
      readOnly = true;
      internal = true;
      description = ''
        The LUKS backing device, as device-mapper names it.

        /dev/mapper rather than /dev/<vg>/<lv>: both are created by LVM's udev
        rules, but the mapper path is the one dm itself brings into being, and
        it is what systemd derives the .device unit from that stage 1 waits on.
      '';
    };
  };
}
