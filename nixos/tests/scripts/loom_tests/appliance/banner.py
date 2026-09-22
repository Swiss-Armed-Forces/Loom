"""The screen somebody who never logs in sees.

The pre-login banner is the whole of what a box tells a person standing in front of it:
what it is, which port to plug into, how far the bring-up has got, whether the key guard
is armed, and the LUKS recovery passphrase. agetty writes it straight to the VT, so what
is asserted here is the issue file itself rather than a `loom-info` run with arguments
that flatter it.

The boot splash is here too. It is the same mark, drawn by plymouth instead, and the two
are wrong in the same way when branding.nix is.
"""

from typing import TYPE_CHECKING

from loom_tests.appliance import readiness
from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest

# What box.nix renders the banner into, and what agetty paints from.
ISSUE = "/run/issue.d/50-loom.issue"


def access_policy(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
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
        on_a_tty = appliance.succeed(
            "script --quiet --return --command loom-info /dev/null"
        )
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
        assert f"--autologin {params.operator.user}" in agetty, agetty
        appliance.wait_until_tty_matches("1", "press ENTER to login")
        appliance.fail(f"pgrep -u {params.operator.user} -f tmux")

        groups = appliance.succeed(f"id -nG {params.operator.user}").split()
        # systemd-journal: without it the operator's console session cannot read
        # PID 1's messages about the unit its first pane follows.
        for group in ["wheel", "docker", "systemd-journal"]:
            assert group in groups, f"{params.operator.user} not in {group}: {groups}"


def boot_splash(appliance: "Machine", subtest: "Subtest") -> None:
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


def readiness_line(appliance: "Machine", subtest: "Subtest") -> None:
    """The one line that changes while the box runs.

    Empty while the cluster has not answered, which is the whole of this VM's life -- so
    the two halves below are "it costs no row yet" and "it says something once there is
    something to say", the second driven by publishing a stage this VM cannot reach.
    """
    with subtest("the banner costs no row until it has something to report"):
        # The banner is written straight to the VT with no paging, so a line too many
        # scrolls the Loom mark off the top -- and on a --wifi box a QR code is already
        # competing for those rows.
        assert appliance.succeed(f"cat {readiness.SUMMARY}").strip() == ""
        issue = appliance.succeed(f"cat {ISSUE}")
        assert "Loom:" not in issue, issue

    with subtest("a box that has got somewhere says so on the login screen"):
        # The unit is stopped first because it would overwrite the record within one
        # poll -- and this is also how a human demonstrates the whole display on a box
        # with no cluster.
        appliance.succeed("systemctl stop loom-ready.service")
        appliance.succeed(
            f"printf 'Loom: starting -- 12/18 pods ready.\\n' >{readiness.SUMMARY}"
        )

        # loom-banner-refresh rewrites the issue; the operator is logged in by now, so
        # it must NOT restart the getty -- that would blank the session somebody is
        # sitting in, which on a box whose console is the entire user interface is the
        # worst thing this feature could do. Exit 1 is how it says it did not.
        status, _ = appliance.execute("loom-banner-refresh")
        assert status == 1, "redrew the login screen under a logged-in operator"

        issue = appliance.succeed(f"cat {ISSUE}")
        assert "Loom: starting -- 12/18 pods ready." in issue, issue
        # That the line can never carry a backslash -- an agetty escape, eaten before
        # anybody sees it (box.nix) -- is asserted where it is generated, against every
        # stage at once: nixos/ready/tests/test_summary.py.

        appliance.succeed("systemctl start loom-ready.service")
        appliance.wait_until_succeeds(f'test -z "$(cat {readiness.SUMMARY})"')
