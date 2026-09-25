# The key guard on a `--lock-key` box.
#
# tests/appliance.nix covers the guard on an ordinary stick, where the key bytes
# are on the partition and `arm_once` proves the stick opens the root before it
# arms. That proof is not available here: the partition holds a LUKS2 container
# and the guard has no plaintext key to authenticate with -- deliberately, since
# keeping one for the life of the box is exactly what --lock-key exists to avoid.
#
# So the locked build arms on a weaker check (`cryptsetup isLuks`) and leans on
# the fingerprint for identity. That is one `if` in key-guard.nix, and getting it
# wrong fails silently: the guard would sit idle for the life of the box and
# pulling the stick would do nothing at all. Nothing else in this repository
# would notice, which is why it gets a node of its own rather than a line in a
# review.
#
# A node of its own rather than a second one in tests/appliance.nix: that test is
# the heaviest in the suite and its last subtest really does power the machine
# off, so it is a bad place to add anything. The same argument
# tests/appliance-wifi.nix and tests/appliance-interface-fallback.nix already
# make.
#
# What is NOT covered here, and cannot be: the initrd unit that asks for the
# passphrase and unlocks the container in stage 1. nixpkgs' qemu-vm module
# replaces the bootloader and the root device, so no VM test in this repository
# reaches stage 1. That one is proved on hardware -- see the --lock-key section
# in Documentation/appliance.md.
{
  pkgs,
  specialArgs,
  applianceModules,
}:
let
  # As tests/appliance.nix: there is no USB stick and no LUKS root in a VM, so
  # both devices are loop devices reached through symlinks -- which is also what
  # udev gives the real box, where /dev/disk/by-partlabel/loom-key is a symlink
  # that can point somewhere else after a re-insert.
  keyGuardDir = "/run/loom-keyguard-test";
  keyGuardKeyDevice = "${keyGuardDir}/key";
  keyGuardRootDevice = "${keyGuardDir}/root";
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-key-store";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check
  # that runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  node.specialArgs = specialArgs;

  nodes.locked = {
    imports = applianceModules;
    # 2048 rather than 1024: the container this test formats uses the argon2id
    # parameters cicd/build_appliance_image.sh pins, and opening one costs 1 GiB.
    # Running the real parameters is the point -- see tests/appliance-install.nix.
    virtualisation.memorySize = 2048;
    virtualisation.diskSize = 2048;
    services.dnsmasq.enable = pkgs.lib.mkForce false;
    networking.interfaces = pkgs.lib.mkForce { };
    loom.autoSelectInterface = pkgs.lib.mkForce false;
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];

    # The flag this whole file is about. It also flips
    # `loom.keyGuard.requireKeyOracle` to false, which is the behaviour under test.
    loom.keyStore.enable = true;

    loom.keyGuard = {
      keyDevice = keyGuardKeyDevice;
      rootDevice = keyGuardRootDevice;
      # As tests/appliance.nix: only the timing is tuned, and only because the
      # removal subtest has to detach a loop device and observe the countdown
      # across a test driver on a loaded builder.
      graceTicks = 15;
      # Left as it comes from modes.nix. Nothing here powers the box off -- that
      # is asserted once, in tests/appliance.nix, and it is the same code path
      # either way.
    };
  };

  # The test itself is loom_tests/key_store.py, so that the repository's Python
  # hooks reach it -- see loom_tests/driver.py for why, and for why
  # `skipTypeCheck` is set above.
  testScript = ''
    from loom_tests.key_store import KeyGuardPaths, run

    run(
        locked,
        start_all=start_all,
        subtest=subtest,
        key_guard=KeyGuardPaths(
            directory="${keyGuardDir}",
            key_device="${keyGuardKeyDevice}",
            root_device="${keyGuardRootDevice}",
        ),
    )
  '';
}
