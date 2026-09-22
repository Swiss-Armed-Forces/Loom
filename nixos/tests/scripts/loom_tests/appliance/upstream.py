"""What up.sh and vars.sh say this box has to be.

The point of these is drift: box.nix restates values that live in up.sh. If somebody
changes a sysctl in `setup_system`, adds a host to vars.sh, or adds a `check_command` to
`validate_environment` without updating the appliance, the box silently ships
misconfigured -- and there is no remote access to notice it with.
"""

import re
import shlex
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def sysctls(appliance: "Machine", subtest: "Subtest") -> None:
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


def host_resolution(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("every *.loom name resolves to the minikube address"):
        for host in params.loom_hosts:
            got = appliance.succeed(f"getent hosts {host}").split()[0]
            assert (
                got == params.minikube_ip
            ), f"{host}: expected {params.minikube_ip}, got {got}"


def hosts_file(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("/etc/hosts is still a store symlink"):
        # up.sh install_host_entries would have replaced it with a mutable copy.
        appliance.succeed("test -L /etc/hosts")
        # -f, not a bare readlink: NixOS points /etc/hosts at /etc/static/hosts
        # and only /etc/static at the store, so following one hop lands on
        # /etc/static/hosts and never matches. Resolve the whole chain.
        appliance.succeed("readlink -f /etc/hosts | grep -q '^/nix/store/'")


def unit_path(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
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
        for cmd in params.upsh_commands + ["sudo"]:
            appliance.succeed(
                f"env -i PATH=\"$(cat /tmp/unit-path)\" sh -c 'command -v {cmd}'"
            )
        appliance.succeed("test -u /run/wrappers/bin/sudo")


def yq_flavour(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("yq is the kislyuk build that up.sh:359 needs"):
        # yq-go cannot parse this jq expression, and write_up_flags_values
        # would fail on the box rather than at build time.
        appliance.succeed(
            "printf 'a: 1\\n' > /tmp/a.yaml && printf 'b: 2\\n' > /tmp/b.yaml && "
            "yq -y -s 'reduce .[] as $item ({}; . * $item)' /tmp/a.yaml /tmp/b.yaml"
        )
