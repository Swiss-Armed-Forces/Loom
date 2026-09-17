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
  minikubeIp,
  loomSubnet,
  loomUser,
  loomRepoDir,
}:
let
  # The literal list from up.sh `validate_environment` (up.sh:402-428), minus
  # `sudo` (a setuid wrapper, not on the plain PATH) and `nvidia-smi` (GPU only).
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
  ];

  loomHosts = builtins.fromJSON loomHostsJson;
in
pkgs.testers.runNixOSTest {
  name = "loom-appliance";

  node.specialArgs = specialArgs;

  nodes.appliance = {
    imports = applianceModules;
    virtualisation.memorySize = 2048;
    virtualisation.diskSize = 4096;
    # The test framework drives networking itself; the appliance's DHCP server
    # and static address would fight it.
    services.dnsmasq.enable = pkgs.lib.mkForce false;
    # Loom cannot actually come up in a test VM (no images, no cluster); we are
    # checking that the units are wired, not that Loom runs.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
  };

  testScript = ''
    start_all()
    appliance.wait_for_unit("multi-user.target")

    with subtest("sysctls from up.sh setup_system are applied"):
        for key, want in {
            "vm.max_map_count": "1677720",
            "vm.overcommit_memory": "1",
            "fs.inotify.max_user_watches": "655360",
            "fs.inotify.max_user_instances": "1280",
            "fs.file-max": "2097152",
            "vm.swappiness": "1",
            "vm.dirty_background_ratio": "10",
            "vm.dirty_ratio": "40",
        }.items():
            got = appliance.succeed(f"sysctl -n {key}").strip()
            assert got == want, f"{key}: expected {want}, got {got}"

    with subtest("every *.loom name resolves to the minikube address"):
        for host in ${builtins.toJSON loomHosts}:
            got = appliance.succeed(f"getent hosts {host}").split()[0]
            assert got == "${minikubeIp}", f"{host}: expected ${minikubeIp}, got {got}"

    with subtest("/etc/hosts is still a store symlink"):
        # up.sh install_host_entries would have replaced it with a mutable copy.
        appliance.succeed("test -L /etc/hosts")
        appliance.succeed("readlink /etc/hosts | grep -q '^/nix/store/'")

    with subtest("every binary up.sh validate_environment checks for is present"):
        for cmd in ${builtins.toJSON upshCommands}:
            appliance.succeed(f"command -v {cmd}")
        # sudo is a setuid wrapper rather than a systemPackages entry.
        appliance.succeed("test -u /run/wrappers/bin/sudo")

    with subtest("yq is the kislyuk build that up.sh:359 needs"):
        # yq-go cannot parse this jq expression, and write_up_flags_values
        # would fail on the box rather than at build time.
        appliance.succeed(
            "printf 'a: 1\\n' > /tmp/a.yaml && printf 'b: 2\\n' > /tmp/b.yaml && "
            "yq -y -s 'reduce .[] as $item ({}; . * $item)' /tmp/a.yaml /tmp/b.yaml"
        )

    with subtest("appliance access policy"):
        appliance.fail("systemctl is-active sshd.service")
        groups = appliance.succeed("id -nG ${loomUser}").split()
        for group in ["wheel", "docker"]:
            assert group in groups, f"${loomUser} not in {group}: {groups}"

    with subtest("the repository is seeded writable and owned by the operator"):
        appliance.wait_for_unit("loom-seed-repo.service")
        appliance.succeed("test -d ${loomRepoDir}/.git")
        owner = appliance.succeed("stat -c %U ${loomRepoDir}").strip()
        assert owner == "${loomUser}", f"expected ${loomUser}, got {owner}"
        # up.sh:359 writes charts/values-up-flags.yaml into its own tree.
        appliance.succeed("runuser -u ${loomUser} -- test -w ${loomRepoDir}/charts")

    with subtest("loom-up reaches up.sh with the skip flags"):
        out = appliance.succeed("runuser -u ${loomUser} -- loom-up --help")
        assert "--skip-STEP" in out, out

    with subtest("docker is available for the minikube driver"):
        appliance.wait_for_unit("docker.service")
        appliance.succeed("docker info")

    with subtest("radios are disabled"):
        appliance.wait_for_unit("loom-rfkill-block.service")
        for module in ["bluetooth", "btusb", "cfg80211", "mac80211"]:
            appliance.succeed(f"grep -r 'blacklist {module}' /etc/modprobe.d/")

    with subtest("both boot modes exist and differ in the right way"):
        # The setup specialisation is what lets one box both fetch images
        # online and then run entirely offline.
        setup = appliance.succeed(
            "ls /run/current-system/specialisation/"
        ).split()
        assert "setup" in setup, setup

        # Run mode serves the network and starts Loom offline.
        appliance.succeed("systemctl cat loom.service | grep -- '--offline'")
        appliance.succeed(
            "systemctl cat loom.service | grep -- '--expose ${loomSubnet}.1'"
        )
        # Setup mode fetches instead, and must not serve DHCP.
        setup_sys = appliance.succeed(
            "readlink -f /run/current-system/specialisation/setup"
        ).strip()
        appliance.succeed(f"test -e {setup_sys}/etc/systemd/system/loom-fetch.service")
        appliance.fail(f"test -e {setup_sys}/etc/systemd/system/dnsmasq.service")
  '';
}
