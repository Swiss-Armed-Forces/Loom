"""What each `nixos/tests/*.nix` knows about the box it booted, and this package does
not.

Kept in its own module rather than in the package's `__init__`, so that the modules
below and the `run()` that calls them can both import it without an import cycle.
"""

from typing import NamedTuple


class Operator(NamedTuple):
    """The unprivileged account the console session and the checkout belong to."""

    user: str
    repo_dir: str
    # The account's home, which is *not* repo_dir's parent by definition and is not
    # the same thing as SKAFFOLD_HOME. Read off the account in the .nix file so this
    # and the tmpfiles rule in box.nix cannot disagree.
    home: str


class KeyGuardPaths(NamedTuple):
    """Where the key guard looks for its two devices in the VM.

    There is no USB stick and no LUKS root here, so the test builds both out of loop
    devices and points the guard at them through these symlinks -- which is also what
    udev does on the real box, where /dev/disk/by-partlabel/loom-key is a symlink that
    can point somewhere else after a re-insert.
    """

    directory: str
    key_device: str
    root_device: str


class Params(NamedTuple):
    """What the .nix file knows about this box."""

    # Whether this platform deploys Ollama. The console session has three panes where
    # it does and two where it does not (platforms/nuc12.nix), and hardcoding either
    # number would make this test pass only for some of the platforms it is run
    # against.
    ai_enabled: bool
    # Whether this platform passes `--scaling`. Read off `runsAutoscaling` rather than
    # hardcoded for the same reason `ai_enabled` is: it is false on the NUC 12, where
    # up.sh would refuse the flag alongside the `--no-resources` that box needs.
    autoscaling: bool
    # `loom.chartOverrides` as JSON -- the Helm values the appliance forces on top of
    # whatever up.sh assembles, which repo.nix writes into the seeded checkout. `{}` on
    # a platform that overrides nothing.
    chart_overrides_json: str
    loom_hosts: list[str]
    minikube_ip: str
    # The literal list from up.sh `validate_environment`, plus whichever vendor SMI
    # tool this platform's GPU requires.
    upsh_commands: list[str]
    loom_subnet: str
    # console.nix's `loom.consoleSocket`. loom_tests/tmux.py keeps one copy of this
    # path for every test that talks to the session; this is what proves the copy
    # still matches the box.
    console_socket: str
    operator: Operator
    key_guard: KeyGuardPaths
