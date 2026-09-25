"""Tty1, which on this box is the entire user interface.

A keypress opens the three-pane session console.nix builds -- the bring-up log turned
k9s, btop beside it, the assistant underneath -- and none of those panes is a shell.
What is asserted here is how that session is wired: which command each pane starts, that
a pane whose program exits comes back, and that the assistant dials the model and the
endpoint the box actually ships.

The pane list comes from `loom_tests.tmux`, which the mouse test shares.
"""

import json
import re
from typing import TYPE_CHECKING

from loom_tests import tmux
from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def console_font(appliance: "Machine", subtest: "Subtest") -> None:
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


def console_session(
    appliance: "Machine", subtest: "Subtest", params: Params
) -> list[str]:
    with subtest("a keypress opens the operator's console session"):
        # The monitor has to be showing tty1, which is where the banner, the
        # prompt and the session all are -- and where a keypress lands. This is
        # not a given: a `console=ttyN` anywhere on the kernel command line
        # silently moves the foreground console, and did.
        fg = appliance.succeed("fgconsole").strip()
        assert fg == "1", f"foreground console is {fg}, not tty1"

        appliance.send_key("ret")
        appliance.wait_until_succeeds(f"pgrep -u {params.operator.user} -f tmux")
        # Not the shell prompt any more: no pane of this session is a shell. The
        # bottom pane is loom-chat, and this is the line it prints before it
        # starts waiting on Ollama -- which in a test VM never answers, so this
        # is as far as the pane ever gets, and that is the point.
        #
        # A platform with no AI services has no such pane; the log pane's own
        # header is what proves the session came up there.
        appliance.wait_until_tty_matches(
            "1", "Loom assistant on" if params.ai_enabled else "Following"
        )

        # List order is layout order -- top-left, top-right, then the full-width
        # pane underneath them -- so this doubles as an assertion about where each
        # thing sits. The assistant is last because it is at the bottom, which is
        # also why console.nix's `create` addresses panes by ID: the indices are
        # rewritten by every split.
        #
        # `pane_start_command` rather than the current one, and why, is in
        # loom_tests/tmux.py -- which the mouse test reads the same list through.
        # One path, checked rather than repeated: three tests talk to this session
        # and each used to carry its own copy of the socket.
        assert tmux.SOCKET == params.console_socket

        panes = tmux.Session(appliance).panes()
        commands = [pane.command for pane in panes]
        assert len(panes) == (3 if params.ai_enabled else 2), commands
        assert "loom-progress" in commands[0], commands
        assert "btop" in commands[1], commands
        if params.ai_enabled:
            assert "loom-chat" in commands[2], commands
        else:
            # A platform with no Ollama drops the pane rather than shipping one
            # that can only ever print a connection error, and drops opencode
            # from the closure with it.
            assert not any("loom-chat" in command for command in commands), commands
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

    return commands


def pane_restart(
    appliance: "Machine", subtest: "Subtest", params: Params, commands: list[str]
) -> None:
    with subtest("a pane whose program exits gets it back"):
        # Every pane of this session is one application, and quitting one is
        # a keystroke: `q` in btop, `:q` in k9s. On a box whose console is
        # the entire user interface, a pane that then stays dead costs the
        # operator a third of the screen until they find the restart control.
        # `loom-pane` supervises each one, so this is a restart rather than a
        # tombstone.
        appliance.wait_until_succeeds(f"pgrep -u {params.operator.user} -x btop")
        before = appliance.succeed(f"pgrep -u {params.operator.user} -x btop").strip()

        # The pane's own process is the supervisor and does not change; what
        # is killed here is the program it is watching, which is exactly what
        # quitting from inside it would do.
        appliance.succeed(f"pkill -u {params.operator.user} -x btop")
        appliance.wait_until_succeeds(
            f"pgrep -u {params.operator.user} -x btop | grep -qvx {before}"
        )

        # And the pane never died, so the layout never collapsed and
        # `remain-on-exit` never had to hold a corpse.
        dead = (
            tmux.Session(appliance)
            .tmux("list-panes -t " + tmux.SESSION + " -F '#{pane_dead}'")
            .split()
        )
        assert dead == ["0"] * len(dead), dead

        _log_pane_hands_over(appliance, params, commands)

        # Everything below is about the assistant pane, so it only applies where
        # there is one. The block above has already asserted the other case
        # properly -- no pane, no loom-chat, no opencode in the closure.
        #
        # Guarded rather than assumed, because which platforms have a pane is not
        # a fixed list: runsAiServices follows the platform's GPU, so it is the
        # default that decides for most boxes rather than a line somebody wrote.
        if params.ai_enabled:
            _assistant_pane(appliance, params, commands)

        # The session no longer holds a shell, so the promise the status line
        # makes -- "Alt-F2 for a shell" -- is the thing worth asserting. Every
        # getty carries --login-pause, tty2 included, so this is the same
        # press-a-key dance as tty1 and then an ordinary prompt.
        appliance.send_key("alt-f2")
        appliance.wait_until_tty_matches("2", "press ENTER to login")
        appliance.send_key("ret")
        appliance.wait_until_tty_matches("2", f"{params.operator.user}@")
        appliance.send_chars("touch /tmp/loom-console-alive\n")
        appliance.wait_for_file("/tmp/loom-console-alive")
        # Back to tty1: the key-guard block at the bottom of this file asserts on
        # what the operator's session shows.
        appliance.send_key("alt-f1")
        appliance.wait_until_succeeds("fgconsole | grep -x 1 >/dev/null")


def _log_pane_hands_over(
    appliance: "Machine", params: Params, commands: list[str]
) -> None:
    """The first pane starts on the log and becomes k9s once Loom is up."""
    # The handover is invisible in a test VM, where nothing ever comes up, so what is
    # read here is the wrapper that pane starts -- which names the unit, the namespace
    # and the thing it hands over to.
    # Two store paths: loom-pane and the program it supervises. `cat` of both is
    # what these assertions have always read.
    progress_pane = appliance.succeed(f"cat {commands[0]}")
    k9s = re.search(r"/nix/store/\S+-loom-k9s/bin/loom-k9s", progress_pane)
    assert k9s, progress_pane
    # The condition it hands over on is `Readiness.settled` in nixos/ready/ -- one
    # definition shared by the pane, the status line and the banner, exercised in that
    # package's own suite. What must be true here is that the pane has somewhere to read
    # it from: an empty --state-dir is how setup mode says there is no publisher.
    # Quotes are stripped because lib.escapeShellArg only adds them where they are
    # needed, which here is the empty string and not the path.
    state_dir = re.search(r"--state-dir (\S*)", progress_pane)
    assert state_dir, progress_pane
    assert state_dir.group(1).strip("'"), "run mode must name a state dir"

    # And k9s must watch the namespace up.sh actually deploys into. Both
    # come from vars.sh -- NAMESPACE reaches the pane through
    # build_appliance_image.sh the same way the *.loom host list does -- and
    # a pod list parked on an empty `default` namespace is worse than no pod
    # list, because it says the box is idle when it is not.
    appliance.wait_for_unit("loom-seed-repo.service")
    # bash, not sh: vars.sh builds LOOM_HOSTS_FQDN out of an array.
    want = appliance.succeed(
        f"bash -c '. {params.operator.repo_dir}/vars.sh; printf %s \"$NAMESPACE\"'"
    ).strip()
    # Tolerates the quotes lib.escapeShellArg adds, as the guard action
    # subtest at the bottom of this file does.
    for script in [progress_pane, appliance.succeed(f"cat {k9s.group(0)}")]:
        got = re.search(r"^namespace='?([\w-]+)'?$", script, re.M)
        assert got, script
        assert got.group(1) == want, f"watches {got.group(1)}, up.sh deploys to {want}"


def _assistant_pane(appliance: "Machine", params: Params, commands: list[str]) -> None:
    """What the bottom pane dials, and what it is not allowed to reach for."""
    # The assistant pane must dial the model the workers use. Same drift
    # argument as the namespace above, with a sharper failure: an
    # air-gapped box only has what ollama/Dockerfile.models baked in, so a pane
    # pinned to anything else warns and then fails every question the
    # operator asks it. The pane no longer *waits* on the model -- see
    # `ready` in console.nix -- which is what makes this assertion the only
    # thing standing between a typo in vars.sh and an assistant that is
    # simply broken on a box with no way to fetch the tag it wants.
    chat_pane = appliance.succeed(f"cat {commands[2]}")
    want_model = appliance.succeed(
        f"bash -c '. {params.operator.repo_dir}/vars.sh;"
        ' printf %s "$LOOM_CHAT_MODEL"\''
    ).strip()
    got_model = re.search(r"^model='?([\w/.:@-]+)'?$", chat_pane, re.M)
    assert got_model, chat_pane
    assert (
        got_model.group(1) == want_model
    ), f"pane pins {got_model.group(1)}, vars.sh says {want_model}"

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
    assert base in [f"https://{h}/v1" for h in params.loom_hosts], base

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
