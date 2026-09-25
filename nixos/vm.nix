# The appliance as a throwaway VM on a workstation: `appliance-vm box`, or
# `nix-build ./nixos -A boxVm` followed by `./result/bin/run-*-vm`.
#
# This is the cheap half of manual testing. It boots the real appliance closure
# in about a minute and gives you the console session, the branding, the units
# and the banner -- everything that lives above the disk. What it cannot show
# you is everything below it: nixpkgs' qemu-vm module replaces `fileSystems`
# wholesale and clears `boot.initrd.luks.devices` (both `mkVMOverride`), so the
# LUKS root, the partlabel mounts, systemd-boot, the boot menu and the installer
# are all out of frame. `appliance-vm installer` is where those get exercised.
#
# Everything here hangs off `virtualisation.vmVariant`, which nixpkgs evaluates
# only when `system.build.vm` is actually built. So none of it reaches the
# toplevel that gets flashed -- and nixos/default.nix keeps this module out of
# `boxSystem` anyway, so the shipped closure does not so much as evaluate it.
{
  # Whether to leave `loom.service` wanted. See the override below for why the
  # answer is normally no.
  startLoom ? false,
}:
{ config, lib, ... }:
{
  virtualisation.vmVariant = {
    imports = [ ./vm-serial.nix ];

    # Enough to boot and drive the console session comfortably. Deliberately
    # not enough to run Loom, which is not what this target is for.
    virtualisation.memorySize = 4096;
    virtualisation.cores = 4;
    # A cap, not a cost: the disk is a sparse qcow2 that `appliance-vm` keeps in
    # its state directory, so what it takes from the host is what the guest
    # writes.
    virtualisation.diskSize = 8192;

    # The window is the point. The boot menu, the splash and the 6-pixel console
    # font branding.nix picks only exist on a framebuffer, and a serial line
    # renders none of them.
    #
    # It also decides the kernel command line: with graphics on, nixpkgs orders
    # `virtualisation.qemu.consoles` as `console=ttyS0 console=tty0`, and the
    # *last* one is the primary console. So tty0 stays foreground -- the
    # invariant tests/appliance.nix asserts with `fgconsole` -- while the boot
    # log is also copied to the serial socket, where it can be selected and
    # pasted. Turning graphics off would reverse that order and quietly move the
    # appliance's own console out from under it.
    virtualisation.graphics = true;

    # ------------------------------------------------------------------------
    # Networking
    #
    # The same three tests/appliance.nix forces off, for the same reasons it
    # gives. The platform `netMatch` entries are deliberately narrow and never
    # match a virtio NIC, so on its own the box leaves the VM's only interface
    # alone -- but `loom.autoSelectInterface` is the fallback for a box nobody
    # wrote a platform for, and it would claim that NIC as loom0, rename it and
    # pin a static address on it. dnsmasq would then start serving DHCP and
    # wildcard `*.loom` onto the link qemu is already serving.
    #
    # Between them that removes the only route back to the host, including the
    # port forwards `appliance-vm` sets up. The behaviour itself is not going
    # untested: tests/appliance-interface-fallback.nix exists for it.
    # ------------------------------------------------------------------------
    loom.autoSelectInterface = lib.mkForce false;
    networking.interfaces = lib.mkForce { };
    services.dnsmasq.enable = lib.mkForce false;

    # ...with one exception, and only for `appliance-vm box --debug`.
    #
    # Run mode sets `networking.useDHCP = false` (network.nix), because a real
    # appliance holds a static address on loom0 and has nothing upstream to ask.
    # In here that leaves qemu's own user-mode NIC with no address at all --
    # which costs nothing while the VM is something you look at through a
    # window, and costs everything the moment it is something you ssh into:
    # `appliance-vm --debug` forwards a host port to the guest's 22, the
    # connection is accepted by qemu and then reaches a stack with no address,
    # and ssh reports a timeout during banner exchange with nothing in the
    # guest's journal to explain it.
    #
    # `useDHCP` rather than naming the interface: `networking.interfaces` is
    # forced empty just above, and a nested definition under a forced parent is
    # discarded rather than merged. This is a different option, so it survives
    # -- and with no interfaces declared, dhcpcd takes the NIC qemu provided.
    networking.useDHCP = lib.mkIf config.loom.debug.enable (lib.mkForce true);

    # ------------------------------------------------------------------------
    # Loom itself
    #
    # It cannot come up in here and there is no pretending otherwise: there is
    # no minikube cluster, no container images, and up.sh exits on the first
    # `check_command` it cannot satisfy. Left wanted, the first pane of the
    # console session fills with that failure instead of the log an operator
    # would be reading, which makes the pane actively misleading.
    #
    # `--start-loom` puts it back, for the one case where watching it fail is
    # the point -- checking that modes.nix passes the arguments you expected.
    # ------------------------------------------------------------------------
    systemd.services.loom.wantedBy = lib.mkForce (lib.optional startLoom "multi-user.target");

    # The key guard is deliberately left enabled and needs no override: with
    # neither `/dev/disk/by-partlabel/loom-key` nor a LUKS root present,
    # `arm_once` (key-guard.nix) fails both its block-device test and its
    # `cryptsetup --test-passphrase` oracle, so the guard stays idle for the
    # life of the VM and powers nothing off. Watching it actually fire needs a
    # real key partition, which is what the installer rig has.
  };
}
