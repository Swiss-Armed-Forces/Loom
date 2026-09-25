# Boots a --debug appliance in a VM and gets into it from another machine.
#
# Separate from tests/appliance.nix rather than a second node in it, because
# that test asserts the opposite: `access_policy` in loom_tests/appliance/banner.py
# runs `systemctl is-active sshd.service` and requires it to fail. That
# assertion is the appliance's "no remote access" guarantee, and it would be
# worth very little if the same file could be read as also covering the one
# build where an sshd does run.
#
# Two nodes, because the half of this worth testing is reachability from
# somewhere else. A login over loopback would exercise the sshd configuration
# and nothing about the firewall -- `nixos-fw` accepts `lo` unconditionally.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomUser,
}:
let
  # A throwaway keypair, committed. See keys/README.md for what it is and why it
  # has to exist on disk rather than be generated here: the authorized key is
  # baked into the closure at build time, and the closure is built before the
  # test runs.
  #
  # Kept in its own directory rather than inline, so the `.secretsignore` entry
  # that stops ripsecrets from rejecting it covers those two files and not this
  # one. A real secret pasted into this file is still caught.
  #
  # `builtins.readFile` for the public half: it has to be a string, because the
  # point of the test is that it travels through `loom.debug.authorizedKey` --
  # the same option cicd/build_appliance_image.sh sets -- rather than through
  # some path-shaped shortcut the flag itself does not use.
  # The trailing newline has to go: debug.nix asserts the key against a regex,
  # and `builtins.match` anchors to the whole string.
  publicKey = pkgs.lib.removeSuffix "\n" (builtins.readFile ./keys/loom-debug-test_ed25519.pub);

  # The private half reaches the client as a store path, and is copied out of
  # the store before use: a store file is 0444 and ssh refuses a key anyone can
  # read.
  privateKey = ./keys/loom-debug-test_ed25519;

  # One line out of `loom.debug.warningLines`, so a reworded warning fails this
  # test rather than leaving it passing against text nobody renders any more.
  warningPhrase = "NEVER USE THIS IN PRODUCTION";
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-debug";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;

    loom.debug = {
      enable = true;
      authorizedKey = publicKey;
    };

    # The framework drives networking itself, and the appliance's DHCP server
    # would fight it -- as tests/appliance.nix says at the same place.
    services.dnsmasq.enable = pkgs.lib.mkForce false;

    # Only loom0's address, NOT `networking.interfaces` wholesale.
    #
    # tests/appliance.nix clears the lot, which it can afford: it has one node
    # and the driver talks to it over the qemu backdoor rather than over IP.
    # Here the client has to reach this box by address, and the framework hands
    # those out through this very option (nixos/lib/testing/network.nix) -- so
    # clearing it would take the test network down with loom0.
    #
    # What has to go is the static appliance address alone: loom0 never
    # materialises in a VM (the platform match is by driver and this NIC is
    # virtio), so its address unit would sit waiting on a .device that never
    # appears.
    networking.interfaces.loom0.ipv4.addresses = pkgs.lib.mkForce [ ];

    # ...and the fallback would undo that by claiming the VM's virtio NIC and
    # renaming it loom0, which here would mean renaming the interface the client
    # is talking over. That behaviour has its own test
    # (tests/appliance-interface-fallback.nix).
    loom.autoSelectInterface = pkgs.lib.mkForce false;

    # dnsmasq is off above, and network.nix points the box's resolver at it. Left
    # as it is, every lookup on this node waits for a resolver that is not there.
    # The names this test uses come from the framework's /etc/hosts either way.
    networking.nameservers = pkgs.lib.mkForce [ ];

    # Loom cannot come up in a test VM -- no images, no cluster. That is also the
    # state `loom-debug-bundle` is checked against below, which is the state it
    # was written for.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
  };

  # An ordinary machine with an ssh client. Deliberately not an appliance: the
  # question is whether something that is not this box can get in.
  nodes.client =
    { ... }:
    {
      environment.systemPackages = [ pkgs.openssh ];
    };

  # The test itself is loom_tests/debug.py, so that the repository's Python
  # hooks reach it -- see loom_tests/driver.py for why, and for why
  # `skipTypeCheck` is set above.
  testScript =
    { nodes, ... }:
    ''
      from loom_tests.debug import Params, run

      run(
          appliance,
          client,
          start_all=start_all,
          subtest=subtest,
          params=Params(
              user="${loomUser}",
              # By address, not by node name.
              #
              # The framework writes each node into every other node's
              # /etc/hosts under `networking.hostName` -- which it sets with
              # `mkDefault` to the node name, and which box.nix then overrides
              # outright to `loom`. So `appliance` resolves nowhere in here, and
              # naming the appliance's real hostname instead would make this
              # test depend on a value it is not about.
              host="${nodes.appliance.networking.primaryIPAddress}",
              key_store_path="${privateKey}",
              warning_phrase="${warningPhrase}",
          ),
      )
    '';
}
