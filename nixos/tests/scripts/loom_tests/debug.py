"""The `--debug` build: a way in, and five places that say so.

This is the one image where `services.openssh.enable` is true, and it is the counterpart
to `loom_tests.appliance.banner.access_policy`, which asserts the opposite for every
other build. Neither assertion means much without the other: "no sshd" is only a
guarantee if the build that does run one is exercised somewhere, and the warning is only
worth rendering if something checks it is on the screen.

Two nodes, because the interesting half of the question is reachability from another
machine. A login over loopback would prove the sshd configuration and nothing about the
firewall -- `nixos-fw` accepts `lo` unconditionally, so it is the one path that cannot
fail.

What this deliberately does not cover: the console session's status marker and the boot
menu entry. The first belongs to the tmux configuration and is checked by reading it,
not by booting; the second is a string in the bootloader entry, which the VM test
framework never writes (it boots the kernel directly).
"""

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest


@dataclass(frozen=True)
class Params:
    """What the .nix file knows and this module must not guess."""

    # The appliance's operator account -- `loomUser` in nixos/default.nix.
    user: str
    # The appliance's address on the test network. An address rather than the
    # node name because box.nix renames every appliance to `loom`, so the name
    # the framework put in /etc/hosts is not the one this file would guess.
    host: str
    # The throwaway private key committed beside the test, as a store path on
    # the client. Copied out before use: a store file is 0444 and world
    # readable, and ssh refuses a key it can see is readable by anybody.
    key_store_path: str
    # A phrase from `loom.debug.warningLines` that every rendering has to carry.
    # Passed rather than spelled here so that rewording the warning cannot leave
    # this test passing against text nobody sees any more.
    warning_phrase: str


# Where the client keeps the key once it has been given a mode ssh accepts.
KEY = "/root/loom-debug-key"

# Non-interactive to the last: an ssh that falls back to asking for a password
# would hang the driver until its timeout rather than fail with a reason.
SSH = (
    "ssh{tty} -i {key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
    " -o UserKnownHostsFile=/dev/null -o BatchMode=yes"
    " -o ConnectTimeout=10 {user}@{host}"
)


def _ssh(
    params: Params,
    command: str | None = None,
    *,
    tty: bool = False,
    user: str | None = None,
) -> str:
    """One ssh invocation, as a line for the client's own shell.

    `command=None` is a login rather than a command, which is a different thing
    to sshd and not only to the user: it is the only case that runs the shell as
    a login shell and the only one where pam_motd prints.

    Every ssh command in this module goes through here, including the ones that
    are meant to be refused -- `SSH` has exactly one caller on purpose. A second
    place formatting that template is a second place to forget a field the day
    one is added, and `str.format` reports that as a KeyError at test time
    rather than as anything mypy can see.

    `shlex.quote` rather than an f-string repr: the command travels through two
    shells -- the client's, then the appliance's -- and only the first quoting
    is ours to get right. Anything with a quote in it would otherwise arrive as
    a different command than the one written here, which is the kind of bug
    that reads as a broken appliance.

    `tty` is `-tt`, not `-t`: the driver's own stdin is not a terminal, and a
    single `-t` declines to allocate one in that case with a warning rather
    than an error -- so the subtest that needs a pty would quietly get the
    session it was written to distinguish itself from.
    """
    prefix = SSH.format(
        tty=" -tt" if tty else "",
        key=KEY,
        user=user or params.user,
        host=params.host,
    )
    if command is None:
        # `exit` typed INTO the session, not `</dev/null`.
        #
        # A pty carries no EOF: with `-tt` ssh ignores stdin closing and holds
        # the channel open, so a redirect from /dev/null hangs until the
        # driver's 900-second timeout rather than ending the login. Sending a
        # line the remote shell can act on is the only thing that closes it.
        return f"echo exit | {prefix}"
    return f"{prefix} {shlex.quote(command)}"


def _sshd_is_running(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("the debug build runs an sshd, and the default build does not"):
        appliance.wait_for_unit("sshd.service")
        appliance.wait_for_open_port(22)

        # The firewall, read off the running ruleset rather than off the
        # configuration: `openFirewall` is the option, an accept rule in
        # `nixos-fw` is the thing that decides whether the client below gets in.
        rules = appliance.succeed("iptables --list-rules nixos-fw")
        assert "--dport 22" in rules, rules


def _the_key_gets_in(client: "Machine", params: Params, subtest: "Subtest") -> None:
    with subtest("the generated key opens a session as the operator"):
        client.succeed(f"install -m 0600 {params.key_store_path} {KEY}")

        who = client.succeed(_ssh(params, "id -un")).strip()
        assert who == params.user, who


def _the_session_is_a_plain_shell(
    client: "Machine", params: Params, subtest: "Subtest"
) -> None:
    with subtest("an ssh session is a plain shell, not the console session"):
        # This is what makes the feature usable at all, and it is not arranged
        # by debug.nix -- it falls out of console.nix's login hook testing
        # `$(tty)` for /dev/tty1. Were that ever to change, every command an
        # agent ran over this port would be swallowed by tmux.
        #
        # `-tt` plus `bash -l` reproduces the only arrangement in which the hook
        # could fire at all: a pty, and /etc/profile actually sourced. Plain
        # `ssh host command` has neither -- sshd runs it as `$SHELL -c` with no
        # terminal -- so a test written that way would pass against a hook that
        # was broken in exactly the way this one matters.
        output = client.succeed(
            _ssh(
                params,
                "bash -l -c 'tty; echo LOOM_SESSION=${LOOM_SESSION:-unset}'",
                tty=True,
            )
        )
        assert "/dev/pts/" in output, output
        # The hook's own re-entry guard, which it exports before starting the
        # session: unset here means it never ran.
        assert "LOOM_SESSION=unset" in output, output


def _the_key_is_root(client: "Machine", params: Params, subtest: "Subtest") -> None:
    with subtest("the operator account reaches root without a password"):
        # Not a surprise and not an accident: box.nix puts the operator in
        # `wheel` with `wheelNeedsPassword = false` for up.sh's benefit. Worth
        # asserting because it is the whole of what the warning claims -- if
        # this ever stopped being true the banner would be overstating the
        # risk, and if it silently started requiring a password the debug image
        # would be much less useful than it says.
        assert client.succeed(_ssh(params, "sudo -n id -un")).strip() == "root"


def _passwords_are_refused(
    client: "Machine", params: Params, subtest: "Subtest"
) -> None:
    with subtest("password authentication is refused outright"):
        # The operator account has no password, so this could never have
        # succeeded; what is asserted is that sshd does not offer the method at
        # all. `PreferredAuthentications=password` with no key on the command
        # line leaves ssh with nothing sshd will take.
        client.fail(
            "ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no"
            " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
            f" -o BatchMode=yes -o ConnectTimeout=10 {params.user}@{params.host} true"
        )


def _other_accounts_are_refused(
    client: "Machine", params: Params, subtest: "Subtest"
) -> None:
    with subtest("AllowUsers keeps every other account out"):
        # root has a locked shadow entry and no authorized key, so this fails
        # twice over. The point is the first of the two: `AllowUsers` is what
        # makes a future change to either of those harmless.
        client.fail(_ssh(params, "true", user="root"))


def _the_banner_says_so(
    appliance: "Machine", params: Params, subtest: "Subtest"
) -> None:
    with subtest("the login screen carries the warning, last and unescaped"):
        appliance.wait_for_unit("loom-issue.service")
        issue = appliance.succeed("cat /run/issue.d/50-loom.issue")

        assert params.warning_phrase in issue, issue

        # No backslash anywhere: agetty reads one as the start of an escape of
        # its own and eats it before the screen sees it. Every generator that
        # writes into /run/issue.d is held to this.
        assert "\\" not in issue, issue

        # Red, and set as a background rather than only a foreground -- a
        # warning the console renders in the same colour as everything else is
        # not the warning that was written.
        assert "\x1b[1;37;41m" in issue, repr(issue)

        # Last. The issue is written straight to the VT with no paging, so a
        # banner taller than the console loses its FIRST rows -- which makes the
        # tail the only position that cannot scroll away. Asserted by checking
        # nothing but blank lines follows the final red run.
        tail = issue[issue.rindex("\x1b[1;37;41m") :]
        after = tail.split("\x1b[0m", 1)[1]
        assert after.strip() == "", repr(after)


def _the_motd_says_so(client: "Machine", params: Params, subtest: "Subtest") -> None:
    with subtest("an ssh session is told what it has connected to"):
        # The banner is for whoever is standing at the box. This is the same
        # warning for whoever -- or whatever -- is not, and it has to reach two
        # different audiences by two different routes.
        #
        # A person logging in: pam_motd, which prints on an interactive login
        # and on nothing else. Bounded, because the failure mode of a login
        # that does not end itself is a test that hangs for a quarter of an
        # hour rather than one that says what went wrong.
        login = client.succeed(_ssh(params, tty=True), timeout=60)
        assert params.warning_phrase in login, login

        # Anything running a command: pam_motd never fires, so the only thing
        # that helps is the file being somewhere conventional. This is why
        # debug.nix writes /etc/motd rather than setting `users.motd`, which
        # would render it to a store path visible to pam alone.
        motd = client.succeed(_ssh(params, "cat /etc/motd"))
        assert params.warning_phrase in motd, motd


def _the_bundle_collects(client: "Machine", params: Params, subtest: "Subtest") -> None:
    with subtest("loom-debug-bundle produces a readable tarball"):
        # Run on a box with no cluster at all, which is the case it was written
        # for: every collector that needs kubectl fails, and the bundle must
        # still be produced and still carry the journal that says why.
        output = client.succeed(_ssh(params, "loom-debug-bundle"))
        path = output.rsplit("Wrote ", 1)[1].split("\n", 1)[0].strip()

        listing = client.succeed(_ssh(params, f"tar --list --file {path}"))
        for member in (
            "journal-this-boot.txt",
            "platform-info.txt",
            "units-failed.txt",
        ):
            assert member in listing, listing

        # Not empty, which is the failure a `|| true` on every command could
        # otherwise hide completely.
        size = client.succeed(_ssh(params, f"stat -c %s {path}")).strip()
        assert int(size) > 1024, size


def run(
    appliance: "Machine",
    client: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
    params: Params,
) -> None:
    """Every subtest, in the order that fails most usefully."""
    start_all()
    appliance.wait_for_unit("multi-user.target")
    client.wait_for_unit("multi-user.target")

    _sshd_is_running(appliance, subtest)
    _the_banner_says_so(appliance, params, subtest)
    _the_key_gets_in(client, params, subtest)
    _the_session_is_a_plain_shell(client, params, subtest)
    _the_key_is_root(client, params, subtest)
    _passwords_are_refused(client, params, subtest)
    _other_accounts_are_refused(client, params, subtest)
    _the_motd_says_so(client, params, subtest)
    _the_bundle_collects(client, params, subtest)
