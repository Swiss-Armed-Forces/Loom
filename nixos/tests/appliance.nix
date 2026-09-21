# Boots the appliance in a VM and asserts the invariants that up.sh depends on.
#
# The point of this test is drift: box.nix restates values that live in up.sh and
# vars.sh. If someone changes a sysctl in up.sh `setup_system`, adds a host to
# vars.sh, or adds a `check_command` to `validate_environment` without updating
# the appliance, the box silently ships misconfigured. This catches that.
#
# box-hardware.nix is deliberately not imported -- the test framework supplies
# its own disks and bootloader.
{
  pkgs,
  specialArgs,
  applianceModules,
  loomHostsJson,
  loomChatModel,
  minikubeIp,
  loomSubnet,
  loomUser,
  loomRepoDir,
  gpuVendor,
}:
let
  # The literal list from up.sh `validate_environment` (up.sh:402-428), minus
  # the two vendor SMI tools, which that function only requires when --gpus is
  # set. Whichever of them this platform needs is appended below.
  # `sudo` is appended in the test itself, where the reason it is special --
  # a setuid wrapper rather than a package -- is asserted alongside it.
  #
  # `awk` is on this list twice over: up.sh also pipes through it at up.sh:380,
  # above the check_command block, so it is the first thing to fail.
  upshCommands = [
    "cp"
    "mkdir"
    "diff"
    "grep"
    "sysctl"
    "pidwait"
    "nproc"
    "awk"
    "df"
    "pkill"
    "tee"
    "realpath"
    "sh"
    "curl"
    "docker"
    "kubectl"
    "helm"
    "minikube"
    "skaffold"
    "yq"
  ]
  # A platform that declares a GPU makes modes.nix pass `--gpus <vendor>`, and
  # from there up.sh will not start without the vendor's SMI tool: it is a
  # check_command, and check_host_resources counts the GPUs by parsing it. This
  # is the drift this test exists for -- declaring gpuVendor and forgetting
  # box.nix's toolchain would otherwise ship a box that dies on first boot.
  ++ pkgs.lib.optional (gpuVendor == "amd") "rocm-smi"
  ++ pkgs.lib.optional (gpuVendor == "nvidia") "nvidia-smi";

  loomHosts = builtins.fromJSON loomHostsJson;

  # Where the key guard looks for its two devices in the VM. There is no USB
  # stick and no LUKS root here, so the test builds both out of loop devices and
  # points the guard at them through these symlinks -- which is also what udev
  # does on the real box, where /dev/disk/by-partlabel/loom-key is a symlink
  # that can point somewhere else after a re-insert.
  keyGuardDir = "/run/loom-keyguard-test";
  keyGuardKeyDevice = "${keyGuardDir}/key";
  keyGuardRootDevice = "${keyGuardDir}/root";
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance";

  # The driver's own mypy cannot resolve scripts/driver.py, so the type check that
  # runs is the repository's. See the header of that file.
  skipTypeCheck = true;

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;
    # A cap, not a cost: the node's root is a sparse qcow2 in the Nix build
    # directory, so what it takes from the build host is what the guest writes.
    # Measured at the end of this test that is 165 MB -- the heaviest of the
    # suite, the rest sit near 20 MB -- and the store is not in it, being a
    # tmpfs in here (/nix/.rw-store). 2048 leaves an order of magnitude spare.
    virtualisation.diskSize = 2048;
    # The test framework drives networking itself; the appliance's DHCP server
    # and static address would fight it.
    services.dnsmasq.enable = pkgs.lib.mkForce false;
    # loom0 never materialises in here -- the platform match is by driver, and
    # the test VM's NIC is virtio, which is exactly the point of keeping those
    # matches narrow. Without this the address unit would sit waiting on a
    # .device that never appears. The rename is asserted from the generated
    # configuration below instead.
    networking.interfaces = pkgs.lib.mkForce { };
    # ...and the fallback would undo that, by claiming the VM's single virtio NIC
    # exactly as it is meant to on a box nobody wrote a platform for. That
    # behaviour has its own test (tests/appliance-usb-ingest.nix's sibling,
    # tests/appliance-interface-fallback.nix); here it is switched off so the
    # assertions above and below keep testing what they were written to test.
    loom.autoSelectInterface = pkgs.lib.mkForce false;
    # Loom cannot actually come up in a test VM (no images, no cluster); we are
    # checking that the units are wired, not that Loom runs.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];

    # The key guard, pointed at devices this test can actually create and
    # destroy. `action` is deliberately NOT overridden: the last subtest lets
    # the real poweroff happen, which is the only way to know it works.
    loom.keyGuard = {
      keyDevice = keyGuardKeyDevice;
      rootDevice = keyGuardRootDevice;
      # Only the timing is tuned, and only because the cancellation subtest has
      # to detach a loop device, observe the countdown and re-attach before the
      # guard acts. Ten seconds is comfortable at a box; it is not comfortable
      # across a test driver on a loaded builder.
      graceTicks = 15;
    };
  };

  # The test itself is scripts/appliance.py, so that the repository's Python hooks
  # reach it -- see scripts/driver.py for why, and for why `skipTypeCheck` is set
  # above. The function form here is for one value: whether this platform deploys
  # Ollama. The console session has three panes where it does and two where it does
  # not (platforms/nuc12.nix), and hardcoding either number would make this test pass
  # only for some of the platforms it is run against.
  testScript =
    { nodes, ... }:
    ''
      ${builtins.readFile ./scripts/appliance.py}

      run(
          appliance,
          start_all=start_all,
          subtest=subtest,
          params=Params(
              ai_enabled=${if nodes.appliance.loom.platform.runsAiServices then "True" else "False"},
              loom_hosts=${builtins.toJSON loomHosts},
              minikube_ip="${minikubeIp}",
              upsh_commands=${builtins.toJSON upshCommands} + ["sudo"],
              loom_subnet="${loomSubnet}",
              operator=Operator(
                  user="${loomUser}",
                  repo_dir="${loomRepoDir}",
              ),
              key_guard=KeyGuardPaths(
                  directory="${keyGuardDir}",
                  key_device="${keyGuardKeyDevice}",
                  root_device="${keyGuardRootDevice}",
              ),
          ),
      )
    '';
}
