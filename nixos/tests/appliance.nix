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
  # `nvidia-smi` (GPU only, and --gpu is rejected by build_appliance_image.sh).
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
    # loom0 never materialises in here -- the platform match is by driver, and
    # the test VM's NIC is virtio, which is exactly the point of keeping those
    # matches narrow. Without this the address unit would sit waiting on a
    # .device that never appears. The rename is asserted from the generated
    # configuration below instead.
    networking.interfaces = pkgs.lib.mkForce { };
    # Loom cannot actually come up in a test VM (no images, no cluster); we are
    # checking that the units are wired, not that Loom runs.
    systemd.services.loom.wantedBy = pkgs.lib.mkForce [ ];
  };

  testScript = ''
    import re
    import shlex

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
        # -f, not a bare readlink: NixOS points /etc/hosts at /etc/static/hosts
        # and only /etc/static at the store, so following one hop lands on
        # /etc/static/hosts and never matches. Resolve the whole chain.
        appliance.succeed("readlink -f /etc/hosts | grep -q '^/nix/store/'")

    with subtest("every binary up.sh needs resolves on loom.service's own PATH"):
        # Deliberately NOT `command -v` in the test driver's shell: that resolves
        # through /run/current-system/sw/bin, which is never on a unit's PATH. A
        # shell-based check passes while the unit that actually runs up.sh is
        # missing half the toolchain -- which is exactly how a box shipped whose
        # loom.service died on `awk: command not found`.
        env = appliance.succeed("systemctl show -p Environment --value loom.service")
        match = re.search(r"(?:^|\s)PATH=(\S+)", env)
        assert match, env
        # Parked in a file rather than interpolated into each command: the unit
        # PATH is ~4 kB of store paths, and inlining it 21 times buries the name
        # of whichever binary actually went missing in the failure output.
        appliance.succeed(f"printf '%s' {shlex.quote(match.group(1))} >/tmp/unit-path")

        # `sudo` belongs here too. It is a setuid wrapper rather than a package,
        # so it can only arrive via /run/wrappers/bin being on the unit's PATH.
        for cmd in ${builtins.toJSON upshCommands} + ["sudo"]:
            appliance.succeed(
                f"env -i PATH=\"$(cat /tmp/unit-path)\" sh -c 'command -v {cmd}'"
            )
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
        # The operator has no password, so a locked shadow entry makes the
        # console prompt unanswerable -- and with no sshd there is nothing to
        # fall back on. Assert the shell prompt itself rather than the unit:
        # 26.05 renders getty@'s ExecStart as a generated script, so the
        # --autologin flag is not visible in `systemctl cat`.
        appliance.wait_until_tty_matches("1", "${loomUser}@")

        # The same banner has to reach whoever never logs in at all, so it is
        # rendered as the agetty issue before the login line. agetty prints the
        # issue even under --autologin.
        appliance.wait_for_unit("loom-issue.service")
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        assert "Loom appliance" in issue, issue
        assert "frontend.loom" in issue, issue
        # A backslash would be eaten by agetty as an issue escape.
        assert "\\" not in issue, issue

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

    with subtest("loom.service can actually find loom-up"):
        # systemPackages puts loom-up in the operator's shell but not in a
        # unit's PATH, so this passing in the shell above says nothing about
        # the unit. The appliance boots and dies with "exec: loom-up: not
        # found" if the two disagree.
        unit_path = appliance.succeed(
            "systemctl show -p Environment --value loom.service"
        )
        assert "loom-up" in unit_path, unit_path

    with subtest("docker is available for the minikube driver"):
        appliance.wait_for_unit("docker.service")
        appliance.succeed("docker info")

    with subtest("the appliance NIC is renamed rather than guessed by name"):
        # The whole point is that no kernel-assigned name (eth0, enp1s0f0np0)
        # appears anywhere: a single image cannot know what the box will call
        # its NIC, and a wrong guess is a box with no network and no sshd.
        link = appliance.succeed("cat /etc/systemd/network/10-loom0.link")
        assert "Name=loom0" in link, link
        assert "[Match]" in link, link

        conf = appliance.succeed("cat /etc/loom/network.conf")
        assert "LOOM_INTERFACE=loom0" in conf, conf

        # The banner and dnsmasq must agree with the rename, not with a name
        # that only existed on the machine the image was built for.
        appliance.succeed("systemctl cat loom-network-check.service")

    with subtest("radios are disabled"):
        appliance.wait_for_unit("loom-rfkill-block.service")
        for module in ["bluetooth", "btusb", "cfg80211", "mac80211"]:
            # -R, not -r: everything in /etc/modprobe.d is a symlink into
            # /etc/static, and -r skips symlinks it finds while walking a
            # directory. -r here silently matches nothing at all.
            appliance.succeed(f"grep -R 'blacklist {module}' /etc/modprobe.d/")

    with subtest("both boot modes exist and differ in the right way"):
        # The setup specialisation is what lets one box both fetch images
        # online and then run entirely offline.
        setup = appliance.succeed(
            "ls /run/current-system/specialisation/"
        ).split()
        assert "setup" in setup, setup

        # Run mode serves the network and starts Loom offline.
        #
        # The flags are not in the unit file: `script = ...` compiles to
        # ExecStart=<store path of a generated script>, so grepping the output
        # of `systemctl cat` for them matches nothing at all. Follow the
        # indirection and read the script the unit actually runs.
        unit = appliance.succeed("systemctl cat loom.service")
        match = re.search(r"ExecStart=(\S+)", unit)
        assert match, unit
        start_script = appliance.succeed(f"cat {match.group(1)}")
        assert "--offline" in start_script, start_script
        assert "--expose ${loomSubnet}.1" in start_script, start_script
        # Setup mode fetches instead, and must not serve DHCP.
        setup_sys = appliance.succeed(
            "readlink -f /run/current-system/specialisation/setup"
        ).strip()
        appliance.succeed(f"test -e {setup_sys}/etc/systemd/system/loom-fetch.service")
        appliance.fail(f"test -e {setup_sys}/etc/systemd/system/dnsmasq.service")
  '';
}
