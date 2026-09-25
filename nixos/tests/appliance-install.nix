# What the installer lays down on the internal disks, and whether the box could
# ever find it again.
#
# The layout is the one thing in this directory with no second chance. A box whose
# pool does not come up has no sshd, no nixos-rebuild and no console session --
# stage 1 simply stops, and the way back is a reinstall that destroys the data. So
# the assertions here are one question asked from several angles: does what the
# installer creates match what box-hardware.nix waits for?
#
# `rootDevice` and the two names behind it are passed in from default.nix, taken off
# the *appliance's* evaluated configuration rather than restated here. A test that
# spelled the path itself could agree with neither side and still pass.
#
# The test itself is loom_tests/install.py, so that the repository's Python
# hooks reach it -- see loom_tests/driver.py for why, and for why `skipTypeCheck` is
# set below.
{
  pkgs,
  volumeGroup,
  rootVolume,
  rootDevice,
}:
let
  # The installer as an importable library rather than the wrapped programs: the
  # test drives `partition`, `create_pool` and `encrypt` directly, and the wrapper
  # only adds a PATH and the configuration this test supplies itself.
  #
  # Built from the same source tree the stick's own package is, so a step renamed
  # in one place fails here rather than at a box.
  installerLibrary = pkgs.python3Packages.buildPythonPackage {
    pname = "loom-installer";
    version = "0.1.0";
    src = ../installer;
    pyproject = true;
    build-system = [ pkgs.python3Packages.poetry-core ];
    dependencies = [ pkgs.python3Packages.rich ];
    # Run by the stick's own derivation (installer.nix) and by `appliance-check`;
    # a third run would only add build time to a VM test.
    doCheck = false;
  };

  # Two scratch disks, in MB. Over a gigabyte because the first one carries the 1G
  # ESP before it contributes anything to the pool; no larger, because nothing here
  # calls `check_pool_size` and its 250 GB minimum would buy only build time.
  diskMb = 2048;
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance-install";

  # The driver's own mypy cannot resolve loom_tests/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  # The tests themselves, as a package this driver can import. scripts.nix explains
  # why it is built from the callback's argument rather than from `pkgs`.
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  nodes.installer = {
    # 2G rather than the 1G the rest of this test needs, because of one subtest:
    # the `--lock-key` key container is formatted with argon2id pinned at 1 GiB
    # (cicd/build_appliance_image.sh `write_locked_key_partition`), and opening it
    # costs that much again. Running the real parameters here rather than cheap
    # ones is the point -- a pinned cost the box cannot afford would otherwise
    # only show up in stage 1, on hardware, with no way to get in and look.
    virtualisation.memorySize = 2048;
    virtualisation.emptyDiskImages = [
      diskMb
      diskMb
    ];

    # What installer.nix puts on the programs' PATH, minus the parts only a real
    # install reaches for (nixos-install, efibootmgr, nvme-cli).
    environment.systemPackages = with pkgs; [
      cryptsetup
      dosfstools
      e2fsprogs
      gptfdisk
      lvm2
      parted
      util-linux
      (python3.withPackages (_: [ installerLibrary ]))
    ];
  };

  testScript = ''
    from loom_tests.install import Storage, run

    run(
        installer,
        start_all=start_all,
        subtest=subtest,
        storage=Storage(
            volume_group="${volumeGroup}",
            root_volume="${rootVolume}",
            root_device="${rootDevice}",
        ),
    )
  '';
}
