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

        # The banner has to reach whoever never logs in at all, so it is
        # rendered as the agetty issue before the login line.
        appliance.wait_for_unit("loom-issue.service")
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")
        assert "Loom appliance" in issue, issue
        assert "frontend.loom" in issue, issue
        # A backslash would be eaten by agetty as an issue escape.
        assert "\\" not in issue, issue

        # The issue is one file read by the VT getty and the serial getty both,
        # so the eyes in it have to be the ASCII pair -- loom-eyes picks that by
        # seeing that loom-issue.service redirected it into a file. Half blocks
        # here would be a screen of question marks on a Spark's serial cable.
        assert "( ( o ) )  ( ( o ) )" in issue, issue
        assert "█" not in issue, issue

        # On a terminal the same generator draws the other pair, which is what
        # the operator's shell gets. `script` is what makes that a terminal at
        # all: succeed() pipes stdout, and a pipe is exactly the case that
        # selects ASCII above.
        on_a_tty = appliance.succeed("script --quiet --return --command loom-info /dev/null")
        assert "█" in on_a_tty, on_a_tty

        # Nothing opens a session by itself. --login-pause holds agetty on the
        # issue until somebody presses a key; --autologin is what performs the
        # login afterwards, and is still needed because the operator's shadow
        # entry is locked (no password is declared for a passwordless box).
        #
        # Assert the flags on the live process rather than the unit: 26.05
        # renders getty@'s ExecStart as a generated script, so `systemctl cat`
        # shows none of these arguments.
        appliance.wait_until_succeeds("pgrep -f 'agetty.*tty1'")
        agetty = appliance.succeed("pgrep -a -f 'agetty.*tty1'")
        assert "--login-pause" in agetty, agetty
        assert "--autologin ${loomUser}" in agetty, agetty
        appliance.wait_until_tty_matches("1", "press ENTER to login")
        appliance.fail("pgrep -u ${loomUser} -f tmux")

        groups = appliance.succeed("id -nG ${loomUser}").split()
        # systemd-journal: without it the operator's console session cannot read
        # PID 1's messages about the unit its first pane follows.
        for group in ["wheel", "docker", "systemd-journal"]:
            assert group in groups, f"${loomUser} not in {group}: {groups}"

    with subtest("a keypress opens the operator's console session"):
        # The monitor has to be showing tty1, which is where the banner, the
        # prompt and the session all are -- and where a keypress lands. This is
        # not a given: a `console=ttyN` anywhere on the kernel command line
        # silently moves the foreground console, and did.
        fg = appliance.succeed("fgconsole").strip()
        assert fg == "1", f"foreground console is {fg}, not tty1"

        appliance.send_key("ret")
        appliance.wait_until_succeeds("pgrep -u ${loomUser} -f tmux")
        appliance.wait_until_tty_matches("1", "${loomUser}@")

        # pane_start_command, not pane_current_command: on a test VM's small VT
        # btop may bail out on start, and what is being asserted is how the
        # session is wired, not what survived.
        panes = appliance.succeed(
            "tmux -S /run/loom/tmux.sock list-panes -t loom "
            "-F '#{pane_index} #{pane_start_command}'"
        ).splitlines()
        assert len(panes) == 3, panes
        assert "loom-progress" in panes[0], panes
        assert "btop" in panes[2], panes

        # The middle pane is a usable shell, which is the whole point of it.
        appliance.send_chars("touch /tmp/loom-console-alive\n")
        appliance.wait_for_file("/tmp/loom-console-alive")

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
        # The first-time-setup specialisation is what lets one box both fetch
        # images online and then run entirely offline. Its *name* is also the
        # boot menu entry -- NixOS builds the title from distroName plus this
        # attribute -- so a rename here silently renames what the operator is
        # told to pick in Documentation/appliance.md.
        specialisations = appliance.succeed(
            "ls /run/current-system/specialisation/"
        ).split()
        assert "first-time-setup" in specialisations, specialisations

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
        # First-time setup fetches instead, and must not serve DHCP.
        setup_sys = appliance.succeed(
            "readlink -f /run/current-system/specialisation/first-time-setup"
        ).strip()
        appliance.succeed(f"test -e {setup_sys}/etc/systemd/system/loom-fetch.service")
        appliance.fail(f"test -e {setup_sys}/etc/systemd/system/dnsmasq.service")

        # The two modes also differ in what they put on the screen, and that
        # difference lives only on the kernel command line. Run mode hides the
        # log behind the splash; first-time setup, which takes hours, keeps it.
        run_cmdline = appliance.succeed("cat /run/current-system/kernel-params")
        for param in ["quiet", "splash"]:
            assert param in run_cmdline.split(), run_cmdline
        setup_cmdline = appliance.succeed(f"cat {setup_sys}/kernel-params")
        assert "plymouth.enable=0" in setup_cmdline.split(), setup_cmdline

        # Neither mode may name a *numbered* VT as a console. `console=ttyN`
        # does not just redirect output there, it makes that VT the foreground
        # one -- which once left this box showing the kernel log while the
        # banner and the press-a-key prompt sat on a tty1 nobody could see or
        # type into. `console=tty0` is exempt and is what the test framework
        # itself passes: tty0 means "whichever VT is current", so it moves
        # nothing. A specialisation only *adds* to its parent's command line,
        # so checking both is checking every combination.
        for cmdline in [run_cmdline, setup_cmdline]:
            vt_consoles = [
                p for p in cmdline.split()
                if re.fullmatch(r"console=tty[1-9][0-9]*", p)
            ]
            assert not vt_consoles, cmdline

    with subtest("both modes run the same session, following their own unit"):
        # Same indirection as above: /etc/profile names the session script,
        # which names the pane-1 script, which names the unit. Reading the
        # chain is the only way to see the difference between the two modes
        # without booting the specialisation.
        def progress_script(profile):
            console = re.search(
                r"/nix/store/\S+-loom-console/bin/loom-console",
                appliance.succeed(f"cat {profile}"),
            )
            assert console, profile
            progress = re.search(
                r"/nix/store/\S+-loom-progress/bin/loom-progress",
                appliance.succeed(f"cat {console.group(0)}"),
            )
            assert progress, console.group(0)
            return appliance.succeed(f"cat {progress.group(0)}")

        run_pane = progress_script("/etc/profile")
        assert "loom.service" in run_pane, run_pane
        assert "loom-fetch.service" not in run_pane, run_pane
        setup_pane = progress_script(f"{setup_sys}/etc/profile")
        assert "loom-fetch.service" in setup_pane, setup_pane

    with subtest("the boot splash is Loom's, not stock NixOS's"):
        # `theme = "loom"` alone proves nothing: the NixOS module only checks
        # that the directory exists. What matters is that the watermark is a
        # real PNG rather than an unmaterialised git-lfs pointer, which would
        # otherwise first show up as a blank screen on a box in the field.
        appliance.succeed("test -e /etc/plymouth/themes/loom/loom.plymouth")
        magic = appliance.succeed(
            "head --bytes=4 /etc/plymouth/themes/loom/watermark.png | od -An -tx1"
        )
        assert magic.split() == ["89", "50", "4e", "47"], magic

    # ------------------------------------------------------------------------
    # The USB key guard.
    #
    # Everything from here on manipulates the guard's devices, and the last
    # subtest really does power the machine off -- so this block stays at the
    # bottom of the file and nothing may be appended after it.
    # ------------------------------------------------------------------------
    with subtest("the guard stays idle when there is no key"):
        # This is the recovery boot: somebody unlocked the disk by typing the
        # passphrase, so there is no stick at all. Powering such a box off
        # would make it unrepairable, since the console is the only way in.
        appliance.wait_for_unit("loom-key-guard.service")
        appliance.wait_until_succeeds(
            "loom-key-guard status | grep -q 'loom-key-guard: idle'"
        )
        appliance.succeed(
            "journalctl --unit loom-key-guard.service | grep -q 'the guard stays idle'"
        )
        # Said once, not every interval for the life of the box.
        idle_lines = appliance.succeed(
            "journalctl --unit loom-key-guard.service | grep -c 'the guard stays idle'"
        )
        assert idle_lines.strip() == "1", idle_lines

    with subtest("the guard arms on a key that opens the root"):
        appliance.succeed("mkdir -p ${keyGuardDir}")
        appliance.succeed(
            "dd if=/dev/urandom of=/var/keyguard-key.img bs=4096 count=1 status=none"
        )
        # 32M: a LUKS2 header is 16M, and the container needs no payload here.
        appliance.succeed("truncate --size=32M /var/keyguard-root.img")
        root_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-root.img"
        ).strip()
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()

        # The same parameters install.sh formats with, pbkdf2 included -- argon2
        # would want more memory than this VM has.
        appliance.succeed(
            "cryptsetup luksFormat --type luks2 --batch-mode --pbkdf pbkdf2 "
            f"--pbkdf-force-iterations 1000 --key-file {key_loop} "
            f"--keyfile-size 4096 {root_loop}"
        )
        appliance.succeed(f"ln -sf {root_loop} ${keyGuardRootDevice}")
        appliance.succeed(f"ln -sf {key_loop} ${keyGuardKeyDevice}")

        appliance.wait_until_succeeds(
            "loom-key-guard status | grep -q 'loom-key-guard: armed'"
        )
        # The banner follows the guard rather than reporting what was true at
        # boot, because it is the only thing an operator who never logs in sees.
        appliance.wait_until_succeeds("grep -q 'USB key guard: armed' /run/issue.d/50-loom.issue")
        assert "\\" not in appliance.succeed("cat /run/issue.d/50-loom.issue")

    with subtest("a key that is put back in time cancels the shutdown"):
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep -q 'USB KEY REMOVED'"
        )

        # Back well inside the grace window, and deliberately on whatever loop
        # device is free now rather than the old one: a re-inserted stick can
        # come back on a different node, and the bytes are the identity.
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()
        appliance.succeed(f"ln -sf {key_loop} ${keyGuardKeyDevice}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep -q 'Shutdown cancelled'"
        )
        appliance.succeed("loom-key-guard status | grep -q 'loom-key-guard: armed'")

    with subtest("a foreign key does not keep the box alive"):
        # A stick carrying a partition named loom-key is not the stick this
        # disk was encrypted with. Presence alone cannot tell the two apart;
        # the fingerprint taken at arm time can.
        appliance.succeed(
            "dd if=/dev/urandom of=/var/keyguard-other.img bs=4096 count=1 status=none"
        )
        other_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-other.img"
        ).strip()
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.succeed(f"ln -sf {other_loop} ${keyGuardKeyDevice}")
        appliance.wait_until_succeeds(
            "journalctl --unit loom-key-guard.service | grep -q 'USB KEY REMOVED'"
        )

        # Put the real one back so the next subtest starts from a known state.
        appliance.succeed(f"losetup --detach {other_loop}")
        key_loop = appliance.succeed(
            "losetup --find --show /var/keyguard-key.img"
        ).strip()
        appliance.succeed(f"ln -sf {key_loop} ${keyGuardKeyDevice}")
        appliance.wait_until_succeeds(
            "loom-key-guard status | grep -q 'loom-key-guard: armed'"
        )

    with subtest("first-time setup warns where run mode powers off"):
        # Asserted from the two generated scripts rather than by booting the
        # specialisation: hours of container pulls must not be thrown away by a
        # glitching USB port, and run mode must not be merely advisory. Same
        # ExecStart indirection as loom.service above -- the value is baked into
        # the script, not visible in the unit.
        def guard_action(system_path):
            unit = appliance.succeed(
                f"cat {system_path}/etc/systemd/system/loom-key-guard.service"
            )
            exec_start = re.search(r"ExecStart=(\S+)", unit)
            assert exec_start, unit
            script = appliance.succeed(f"cat {exec_start.group(1)}")
            # Tolerates the quotes lib.escapeShellArg adds only when it has to.
            action = re.search(r"^readonly ACTION='?(\w+)'?$", script, re.M)
            assert action, script
            return action.group(1)

        assert guard_action("/run/current-system") == "poweroff"
        assert guard_action(setup_sys) == "warn"

    with subtest("pulling the key powers the box off"):
        # The end of the test, literally: this shuts the machine down. Nothing
        # may be added below, and nothing short of watching it happen proves
        # that the box a stick was pulled from actually stops.
        appliance.succeed(f"losetup --detach {key_loop}")
        appliance.wait_for_shutdown()
  '';
}
