"""The appliance itself, booted in a VM.

This is the big one: one machine, and everything about it that can be asserted without a
cluster. It is split by subject rather than left as the thousand-line file it grew into
-- `upstream` for what box.nix restates from up.sh, `banner` for the screen a passer-by
sees, `session` for tty1, `readiness` for how far a bring-up has got, `startup` for what
Loom is launched through, `modes` for the two boot entries, and `guard` for the USB key.

`run()` below is the table of contents, and the one thing in this package whose order
matters: everything under the key guard manipulates its devices, and the last subtest
really does let the machine power itself off.
"""

from typing import TYPE_CHECKING

from loom_tests.appliance import (
    banner,
    guard,
    modes,
    readiness,
    session,
    startup,
    upstream,
)
from loom_tests.appliance.params import KeyGuardPaths, Operator, Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest

__all__ = ["KeyGuardPaths", "Operator", "Params", "run"]


def run(
    appliance: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
    params: Params,
) -> None:
    """The whole test, as tests/appliance.nix calls it.

    The order is load-bearing at one end only: everything under "the USB key guard"
    manipulates the guard's devices, and the last of them really does power the
    machine off. Nothing may be added after it.
    """
    start_all()
    appliance.wait_for_unit("multi-user.target")

    # What up.sh and vars.sh say this box has to be.
    upstream.sysctls(appliance, subtest)
    upstream.host_resolution(appliance, subtest, params)
    upstream.hosts_file(appliance, subtest)
    upstream.unit_path(appliance, subtest, params)
    upstream.yq_flavour(appliance, subtest)
    banner.access_policy(appliance, subtest, params)

    # tty1, which is the whole user interface.
    session.console_font(appliance, subtest)
    panes = session.console_session(appliance, subtest, params)
    session.pane_restart(appliance, subtest, params, panes)

    # After the session exists: two of the three screens readiness draws on are in it,
    # and the third is the banner, which is asserted where the rest of the banner is.
    readiness.published(appliance, subtest)
    readiness.status_line(appliance, subtest)
    readiness.one_shot(appliance, subtest, params)
    banner.readiness_line(appliance, subtest)

    # What Loom itself is started through.
    startup.repository(appliance, subtest, params)
    startup.loom_up_flags(appliance, subtest, params)
    startup.loom_up_on_path(appliance, subtest)
    startup.state_directories(appliance, subtest, params)
    startup.docker(appliance, subtest)
    startup.exposure(appliance, subtest, params)
    startup.interface_rename(appliance, subtest)
    startup.radios(appliance, subtest)

    # The two boot modes, and the branding both of them wear.
    setup_sys = modes.boot_modes(appliance, subtest)
    modes.mode_sessions(appliance, subtest, setup_sys)
    banner.boot_splash(appliance, subtest)

    # The USB key guard. The loop device is handed on from subtest to subtest
    # because a re-inserted stick can come back on a different node, and each of
    # these leaves the box on whichever one it last attached.
    guard.idle(appliance, subtest)
    key_loop = guard.arms(appliance, subtest, params)
    key_loop = guard.cancels(appliance, subtest, params, key_loop)
    key_loop = guard.foreign_key(appliance, subtest, params, key_loop)
    guard.action_per_mode(appliance, subtest, setup_sys)
    guard.powers_off(appliance, subtest, key_loop)
