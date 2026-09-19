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

  # The function form, for one value: whether this platform deploys Ollama. The
  # console session has three panes where it does and two where it does not
  # (platforms/nuc12.nix), and hardcoding either number would make this test
  # pass only for some of the platforms it is run against.
  testScript =
    { nodes, ... }:
    ''
      AI_ENABLED = ${if nodes.appliance.loom.platform.runsAiServices then "True" else "False"}

      import json
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

          # loom-eyes draws one pair, and it survives the round trip through the
          # issue file: loom-issue.service captures it with stdout redirected, and
          # agetty hands the bytes to the VT unchanged.
          assert "█" in issue, issue

          # The mark is amber on the login screen, not monochrome. The colour
          # only exists because loom-issue.service forces it: the redirection
          # that builds this file hides the console from loom-info, so a lost
          # LOOM_INFO_COLOR leaves exactly the screen the colour is for -- the
          # prompt nobody has touched yet -- rendering the eyes plain, which
          # nothing short of looking at a monitor would catch.
          #
          # Both palette indices, because a 512-glyph font costs the console its
          # intensity bit and with it the choice of which one bold lands on.
          assert "\033]P3f7b718" in issue, repr(issue)
          assert "\033]PBf7b718" in issue, repr(issue)
          assert "\033[33m" in issue, repr(issue)

          # The same generator, the same art, on a terminal -- which is what the
          # operator's shell gets. `script` is what makes that a terminal at all:
          # succeed() pipes stdout.
          on_a_tty = appliance.succeed("script --quiet --return --command loom-info /dev/null")
          assert "█" in on_a_tty, on_a_tty

          # A pts gets the colour but never the palette redefinition.
          # console_codes(4): xterm hangs on that sequence until somebody presses
          # return, and the panes of the operator's session are pts. They come out
          # amber anyway, from the palette the banner already rewrote on the VT
          # underneath them.
          assert "\033[33m" in on_a_tty, repr(on_a_tty)
          assert "\033]P" not in on_a_tty, repr(on_a_tty)

          # On demand there, and nowhere automatic. The login shell used to
          # reprint the banner, and agetty renders the issue on every VT -- so
          # tty2-tty6 showed the same screen twice with nothing between the copies
          # but the keypress that logged the operator in.
          #
          # Asserted against the shell init rather than against a screen, because
          # a screen cannot see it: two copies of a twenty-line banner scroll the
          # first one off an 80x25 VT, which is exactly why this survived every
          # tty match here. tty1 is the one console where the banner is genuinely
          # covered -- the tmux session draws over it -- and `loom-info` is on the
          # PATH for that.
          appliance.fail("grep -q loom-info /etc/bashrc /etc/profile")

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

      with subtest("the console font is re-applied once the display has settled"):
          # systemd-vconsole-setup runs Before=sysinit.target, and on the real box
          # its early pass logged "Configuration of first virtual console was
          # skipped" and the login screen kept the kernel's 16x32 built-in even
          # though /etc/vconsole.conf named the right font and `setfont` worked by
          # hand. branding.nix therefore applies it a second time, late.
          appliance.succeed("systemctl is-active loom-console-font.service")

          # The `-` on ExecStart. A console that will not take the font must still
          # reach a login prompt: on a box with no remote access a wrong-sized
          # font is cosmetic, a missing getty is unrecoverable. This VM exercises
          # that path for real -- its console cannot load a 6px-wide font at all.
          appliance.succeed("systemctl is-active getty@tty1.service")

          # And the takeover that unit cannot be ordered against. It is late only
          # because `plymouth --wait` holds it there, which first-time setup --
          # booting with plymouth.enable=0 -- does not: the same unit returns at
          # once and the font is applied before the DRM driver takes the console.
          # The recovery is a udev rule on the card.
          #
          # Asserted rather than exercised. This VM's console is not the reset
          # that matters, and what breaks in the field is the rule quietly
          # matching nothing -- which nothing short of a monitor at a site sees.
          rule = appliance.succeed(
              "grep -rh loom-console-font-reapply /etc/udev/rules.d/"
          ).strip()
          assert 'SUBSYSTEM=="drm"' in rule, rule
          assert "SYSTEMD_WANTS" in rule, rule
          appliance.succeed("systemctl cat loom-console-font-reapply.service >/dev/null")

          # The ordering is the dangerous part of that unit: it sits between
          # plymouth-quit-wait and getty-pre. systemd breaks a cycle by *deleting*
          # a job rather than failing, so a cycle would not turn any unit red --
          # it would silently drop one, and the journal is the only place it shows.
          #
          # Not named `log`: that is the test driver's own global logger.
          journal = appliance.succeed("journalctl -b --no-pager")
          assert "ordering cycle" not in journal.lower(), [
              line for line in journal.splitlines() if "ordering cycle" in line.lower()
          ]

      with subtest("a keypress opens the operator's console session"):
          # The monitor has to be showing tty1, which is where the banner, the
          # prompt and the session all are -- and where a keypress lands. This is
          # not a given: a `console=ttyN` anywhere on the kernel command line
          # silently moves the foreground console, and did.
          fg = appliance.succeed("fgconsole").strip()
          assert fg == "1", f"foreground console is {fg}, not tty1"

          appliance.send_key("ret")
          appliance.wait_until_succeeds("pgrep -u ${loomUser} -f tmux")
          # Not the shell prompt any more: no pane of this session is a shell. The
          # bottom pane is loom-chat, and this is the line it prints before it
          # starts waiting on Ollama -- which in a test VM never answers, so this
          # is as far as the pane ever gets, and that is the point.
          #
          # A platform with no AI services has no such pane; the log pane's own
          # header is what proves the session came up there.
          appliance.wait_until_tty_matches(
              "1", "Loom assistant on" if AI_ENABLED else "Following"
          )

          # pane_start_command, not pane_current_command: loom-btop execs btop, so
          # the current command is whatever that wrapper turned into, and on a
          # test VM's 80x25 VT the pane is narrower than anything btop will draw
          # in. What is being asserted is how the session is wired.
          panes = appliance.succeed(
              "tmux -S /run/loom/tmux.sock list-panes -t loom "
              "-F '#{pane_index} #{pane_start_command}'"
          ).splitlines()
          # Index order is layout order -- top-left, top-right, then the full-width
          # pane underneath them -- so this list doubles as an assertion about
          # where each thing sits. The assistant is last because it is at the
          # bottom, which is also why `create` addresses panes by ID: these indices
          # are rewritten by every split.
          assert len(panes) == (3 if AI_ENABLED else 2), panes
          assert "loom-progress" in panes[0], panes
          assert "btop" in panes[1], panes
          if AI_ENABLED:
              assert "loom-chat" in panes[2], panes
          else:
              # A platform with no Ollama drops the pane rather than shipping one
              # that can only ever print a connection error, and drops opencode
              # from the closure with it.
              assert not any("loom-chat" in pane for pane in panes), panes
              appliance.fail("command -v loom-chat")
              appliance.fail("command -v opencode")

          # loom-btop writes its config before exec'ing btop, so this file exists
          # even here, where the pane is too narrow for btop to draw anything.
          #
          # The interface is the assertion worth making. Unpinned, btop picks the
          # interface with the most cumulative traffic, which on this box is `lo`
          # -- and once picked it never reconsiders, so the operator's net box
          # graphs loopback forever. This has to be the interface carrying the
          # appliance address, which is what /etc/loom/network.conf reports as
          # LOOM_INTERFACE further down this file.
          appliance.wait_for_file("/run/loom/btop.conf")
          btop_conf = appliance.succeed("cat /run/loom/btop.conf")
          assert 'net_iface = "loom0"' in btop_conf, btop_conf

          # The first pane starts on the log and hands over to k9s once Loom is
          # up. Both halves live in the script that pane starts, so read it: the
          # handover is invisible in a test VM, where nothing ever comes up.
          progress_pane = appliance.succeed(f"cat {panes[0].split(maxsplit=1)[1]}")
          k9s = re.search(r"/nix/store/\S+-loom-k9s/bin/loom-k9s", progress_pane)
          assert k9s, progress_pane
          # It waits for the unit to have *succeeded*, not merely to exist. On
          # `activating` the bring-up is still running and the log is the screen
          # that matters; on `failed` it is the only screen that does.
          assert "ActiveState" in progress_pane, progress_pane

          # And k9s must watch the namespace up.sh actually deploys into. Both
          # come from vars.sh -- NAMESPACE reaches the pane through
          # build_appliance_image.sh the same way the *.loom host list does -- and
          # a pod list parked on an empty `default` namespace is worse than no pod
          # list, because it says the box is idle when it is not.
          appliance.wait_for_unit("loom-seed-repo.service")
          # bash, not sh: vars.sh builds LOOM_HOSTS_FQDN out of an array.
          want = appliance.succeed(
              "bash -c '. ${loomRepoDir}/vars.sh; printf %s \"$NAMESPACE\"'"
          ).strip()
          # Tolerates the quotes lib.escapeShellArg adds, as the guard action
          # subtest at the bottom of this file does.
          for script in [progress_pane, appliance.succeed(f"cat {k9s.group(0)}")]:
              got = re.search(r"^namespace='?([\w-]+)'?$", script, re.M)
              assert got, script
              assert got.group(1) == want, f"watches {got.group(1)}, up.sh deploys to {want}"

          # Everything below is about the assistant pane, so it only applies where
          # there is one. The block above has already asserted the other case
          # properly -- no pane, no loom-chat, no opencode in the closure.
          #
          # Guarded rather than assumed, because which platforms have a pane is not
          # a fixed list: runsAiServices follows the platform's GPU, so it is the
          # default that decides for most boxes rather than a line somebody wrote.
          if AI_ENABLED:
              # The assistant pane must dial the model the workers use. Same drift
              # argument as the namespace above, with a sharper failure: an
              # air-gapped box only has what ollama/Dockerfile baked in, so a pane
              # pinned to anything else waits forever on a model never served.
              chat_pane = appliance.succeed(f"cat {panes[2].split(maxsplit=1)[1]}")
              want_model = appliance.succeed(
                  "bash -c '. ${loomRepoDir}/vars.sh; printf %s \"$LOOM_CHAT_MODEL\"'"
              ).strip()
              got_model = re.search(r"^model='?([\w/.:@-]+)'?$", chat_pane, re.M)
              assert got_model, chat_pane
              assert got_model.group(1) == want_model, (
                  f"pane pins {got_model.group(1)}, vars.sh says {want_model}"
              )

              # opencode reaches for the network on its own unless told not to. The
              # catalogue refresh is the one to pin down: nixpkgs bakes models.dev
              # in at build time but the flag that stops the lookup is read at
              # *runtime*, so it is easy to lose in a package bump and hard to
              # notice afterwards -- opencode falls back to the baked-in copy rather
              # than failing loudly. This box makes no outbound connection it was
              # not asked to make.
              assert "OPENCODE_DISABLE_MODELS_FETCH=1" in chat_pane, chat_pane
              assert "OPENCODE_DISABLE_AUTOUPDATE=1" in chat_pane, chat_pane

              # And the config it ships. "@ai-sdk/openai-compatible" is the
              # load-bearing string: it is in opencode's BUNDLED_PROVIDERS table, so
              # the adapter is already in the binary. Any other name sends opencode
              # to the npm registry the first time the operator asks a question.
              config_path = re.search(r"OPENCODE_CONFIG=(\S+)", chat_pane)
              assert config_path, chat_pane
              config = json.loads(appliance.succeed(f"cat {config_path.group(1)}"))
              assert config["autoupdate"] is False, config
              assert config["model"] == f"ollama/{want_model}", config
              ollama = config["provider"]["ollama"]
              assert ollama["npm"] == "@ai-sdk/openai-compatible", config
              assert want_model in ollama["models"], config
              # The endpoint has to be a name box.nix pins in /etc/hosts, or the
              # pane cannot resolve it with no DNS off the box -- and it has to be
              # https, because charts/values.yaml annotates every ingress
              # `websecure` and nothing routes this host on port 80 outside
              # values-development.
              base = ollama["options"]["baseURL"]
              assert base in [f"https://{h}/v1" for h in ${builtins.toJSON loomHosts}], base

              # That certificate is self-signed, so the pane has to trust it
              # explicitly. Asserting the CA is handed over rather than
              # verification switched off.
              #
              # Matching an assignment rather than the bare name: loom-chat's own
              # comments explain why the blunt option was not taken, so a substring
              # test for "NODE_TLS_REJECT_UNAUTHORIZED" finds the prose and fails on
              # a script that is doing exactly the right thing.
              assert re.search(r"^export NODE_EXTRA_CA_CERTS=", chat_pane, re.M), chat_pane
              assert not re.search(
                  r"^\s*(export\s+)?NODE_TLS_REJECT_UNAUTHORIZED=", chat_pane, re.M
              ), chat_pane

          # The session no longer holds a shell, so the promise the status line
          # makes -- "Alt-F2 for a shell" -- is the thing worth asserting. Every
          # getty carries --login-pause, tty2 included, so this is the same
          # press-a-key dance as tty1 and then an ordinary prompt.
          appliance.send_key("alt-f2")
          appliance.wait_until_tty_matches("2", "press ENTER to login")
          appliance.send_key("ret")
          appliance.wait_until_tty_matches("2", "${loomUser}@")
          appliance.send_chars("touch /tmp/loom-console-alive\n")
          appliance.wait_for_file("/tmp/loom-console-alive")
          # Back to tty1: the key-guard block at the bottom of this file asserts on
          # what the operator's session shows.
          appliance.send_key("alt-f1")
          appliance.wait_until_succeeds("fgconsole | grep -x 1 >/dev/null")

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

          # This test asserts loom0 is absent, which is only true with the
          # fallback off -- so assert it really is off, rather than letting a
          # changed default quietly turn the subtest above into a no-op.
          appliance.fail("test -e /sys/class/net/loom0")
          appliance.fail("systemctl cat loom-interface-fallback.service")

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

          # And it ends by powering the box off rather than leaving it up for
          # somebody to reboot: the default entry serves DHCP and *.loom on the
          # appliance NIC, which must not happen on whatever network the images
          # were just fetched over. Same ExecStart indirection as above -- the
          # specialisation's units cannot be read with `systemctl cat`.
          fetch_unit = appliance.succeed(
              f"cat {setup_sys}/etc/systemd/system/loom-fetch.service"
          )
          fetch_match = re.search(r"ExecStart=(\S+)", fetch_unit)
          assert fetch_match, fetch_unit
          fetch_script = appliance.succeed(f"cat {fetch_match.group(1)}")
          assert "poweroff" in fetch_script, fetch_script

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
          # `grep`, not `grep -q`, in every pipeline below. The driver wraps each
          # command in `set -eo pipefail`, and -q makes grep exit on the first
          # matching line -- so the producer on the left gets EPIPE on whatever it
          # writes next, and the pipeline fails *because* the match was found.
          # `loom-key-guard status` prints three more lines after the one being
          # matched, which makes that a coin toss on every run. Without -q grep
          # reads its input to the end and nothing is ever killed mid-write.
          appliance.wait_until_succeeds(
              "loom-key-guard status | grep 'loom-key-guard: idle' >/dev/null"
          )
          appliance.succeed(
              "journalctl --unit loom-key-guard.service | grep 'the guard stays idle' >/dev/null"
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
              "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
          )
          # The banner follows the guard rather than reporting what was true at
          # boot, because it is the only thing an operator who never logs in sees.
          appliance.wait_until_succeeds("grep -q 'USB key guard: armed' /run/issue.d/50-loom.issue")
          assert "\\" not in appliance.succeed("cat /run/issue.d/50-loom.issue")

      with subtest("a key that is put back in time cancels the shutdown"):
          appliance.succeed(f"losetup --detach {key_loop}")
          appliance.wait_until_succeeds(
              "journalctl --unit loom-key-guard.service | grep 'USB KEY REMOVED' >/dev/null"
          )

          # Back well inside the grace window, and deliberately on whatever loop
          # device is free now rather than the old one: a re-inserted stick can
          # come back on a different node, and the bytes are the identity.
          key_loop = appliance.succeed(
              "losetup --find --show /var/keyguard-key.img"
          ).strip()
          appliance.succeed(f"ln -sf {key_loop} ${keyGuardKeyDevice}")
          appliance.wait_until_succeeds(
              "journalctl --unit loom-key-guard.service | grep 'Shutdown cancelled' >/dev/null"
          )
          appliance.succeed("loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null")

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
              "journalctl --unit loom-key-guard.service | grep 'USB KEY REMOVED' >/dev/null"
          )

          # Put the real one back so the next subtest starts from a known state.
          appliance.succeed(f"losetup --detach {other_loop}")
          key_loop = appliance.succeed(
              "losetup --find --show /var/keyguard-key.img"
          ).strip()
          appliance.succeed(f"ln -sf {key_loop} ${keyGuardKeyDevice}")
          appliance.wait_until_succeeds(
              "loom-key-guard status | grep 'loom-key-guard: armed' >/dev/null"
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
