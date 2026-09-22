"""What Loom itself is started through.

The checkout, the wrappers up.sh is reached by, the state directories minikube and
skaffold are pointed at, docker, and the DNAT that publishes the cluster on the
appliance address. None of it brings Loom up -- a test VM has no images and no cluster
-- so these assert the wiring that would carry a bring-up rather than the bring-up
itself.
"""

import json
from typing import TYPE_CHECKING

from loom_tests.appliance.params import Params

if TYPE_CHECKING:
    from loom_tests.driver import Machine, Subtest


def repository(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the repository is seeded writable and owned by the operator"):
        appliance.wait_for_unit("loom-seed-repo.service")
        appliance.succeed(f"test -d {params.operator.repo_dir}/.git")
        owner = appliance.succeed(f"stat -c %U {params.operator.repo_dir}").strip()
        assert (
            owner == params.operator.user
        ), f"expected {params.operator.user}, got {owner}"
        # up.sh:359 writes charts/values-up-flags.yaml into its own tree.
        appliance.succeed(
            f"runuser -u {params.operator.user} -- test -w {params.operator.repo_dir}/charts"
        )

    with subtest("the checkout carries this platform's chart overrides"):
        # repo.nix writes `loom.chartOverrides` into charts/values-overwrites.yaml,
        # which skaffold lists after the values file up.sh generates and therefore
        # applies last. Parsed through the box's own yq rather than compared as text:
        # what has to match is the values, and the generator's formatting is not part
        # of the claim.
        overwrites = f"{params.operator.repo_dir}/charts/values-overwrites.yaml"
        got = json.loads(appliance.succeed(f"yq --compact-output . {overwrites}")) or {}
        want = json.loads(params.chart_overrides_json)
        # Every declared override must be in there, rather than the file being exactly
        # the overrides. The committed copy is comments only -- it parses to `null`, the
        # `or {}` above -- but these tests are also run with `repoSrc ./.` against a
        # developer's checkout, where this very file is the one they keep their own
        # overrides in. What is being asserted is that the platform's landed, not that
        # nobody else wrote here.
        for key, value in want.items():
            assert got.get(key) == value, f"{key}: {got.get(key)} != {value}"


def loom_up_flags(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("loom-up reaches up.sh with the skip flags"):
        out = appliance.succeed(f"runuser -u {params.operator.user} -- loom-up --help")
        assert "--skip-STEP" in out, out


def loom_up_on_path(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("loom.service can actually find loom-up"):
        # systemPackages puts loom-up in the operator's shell but not in a
        # unit's PATH, so this passing in the shell above says nothing about
        # the unit. The appliance boots and dies with "exec: loom-up: not
        # found" if the two disagree.
        unit_path = appliance.succeed(
            "systemctl show -p Environment --value loom.service"
        )
        assert "loom-up" in unit_path, unit_path


def state_directories(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("the unit and the operator agree where minikube keeps its state"):
        # box.nix sets these in `environment.sessionVariables`, which NixOS
        # writes into /etc/profile -- so they reach login shells and nothing
        # else. Without them on the unit as well, minikube falls back to
        # $HOME/.minikube: the cluster loom.service builds lands somewhere no
        # `minikube` command typed at the console can see, and the console
        # reports no cluster on a box that is running one. Same shape as the
        # PATH problem above, and the same cause.
        env = appliance.succeed("systemctl show -p Environment --value loom.service")
        for var, want in [
            ("MINIKUBE_HOME", f"{params.operator.repo_dir}/.minikube"),
            ("SKAFFOLD_HOME", f"{params.operator.repo_dir}/.skaffold"),
        ]:
            assert f"{var}={want}" in env, env
            # The other half of "agree": a login shell, which is where the
            # value has always been right.
            shell = appliance.succeed(
                f"runuser -l {params.operator.user} -c 'echo ${var}'"
            ).splitlines()[-1]
            assert shell == want, f"{var}: unit says {want}, shell says {shell}"


def docker(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("docker is available for the minikube driver"):
        appliance.wait_for_unit("docker.service")
        appliance.succeed("docker info")


def exposure(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("Loom is published on the appliance address"):
        # The one thing a visitor actually depends on, and for a long time
        # nothing here checked it: the box handed out leases and resolved every
        # *.loom name to its own address while nothing whatsoever listened
        # there. `up.sh --expose` ran `minikube tunnel`, which on the docker
        # driver forwards each service port over the system `ssh` client -- and
        # `ssh` is not on loom.service's PATH, so every forward failed and the
        # only symptom was a connection refused from the laptop. The old
        # assertion for that flag passed throughout.
        appliance.wait_for_unit("loom-expose.service")
        box = f"{params.loom_subnet}.1"

        # DNAT: the appliance address becomes the minikube node, which is where
        # traefik's hostPort lives.
        nat = appliance.succeed("iptables --table nat --list-rules LOOM-EXPOSE")
        for port in ["80", "443"]:
            rule = next(
                (line for line in nat.splitlines() if f"--dport {port} " in line), None
            )
            assert rule, nat
            assert f"--to-destination {params.minikube_ip}:{port}" in rule, rule
            assert "-i loom0" in rule, rule
            assert f"-d {box}/32" in rule, rule

        # Nothing else may be forwarded. The tunnel published all seven ports
        # of traefik's Service on this address as a side effect of how it
        # worked; here the list is a decision, so a new one has to be made
        # deliberately.
        assert len([line for line in nat.splitlines() if "DNAT" in line]) == 2, nat

        # And the FORWARD accept, without which dockerd's DROP policy eats the
        # DNAT'd packet and the symptom is identical to no DNAT at all.
        forward = appliance.succeed("iptables --list-rules LOOM-FORWARD")
        assert f"-d {params.minikube_ip}/32" in forward, forward
        assert "--dports 80,443 -j ACCEPT" in forward, forward
        assert "RELATED,ESTABLISHED -j ACCEPT" in forward, forward

        # Both chains have to actually be reached. DOCKER-USER is the hook
        # docker guarantees runs before its own FORWARD rules.
        assert "-j LOOM-EXPOSE" in appliance.succeed(
            "iptables --table nat --list-rules PREROUTING"
        )
        assert "-j LOOM-FORWARD" in appliance.succeed(
            "iptables --list-rules DOCKER-USER"
        )

        # Routed rather than delivered locally, so this is not optional -- and
        # not something to leave to dockerd turning it on as a side effect.
        assert appliance.succeed("sysctl -n net.ipv4.ip_forward").strip() == "1"

        _exposure_is_repeatable(appliance, nat)


def _exposure_is_repeatable(appliance: "Machine", nat: str) -> None:
    """Restarting must rebuild the rules, not stack a second copy of them."""
    # The chains are created-or-flushed for exactly this reason: loom-expose is
    # PartOf=docker.service, so a `systemctl restart docker` reruns it, and on a
    # box that is restarted often enough an appending install would grow the
    # chain without ever being noticed -- every copy matches, so it keeps
    # working right up until somebody reads the ruleset.
    appliance.succeed("systemctl restart loom-expose.service")
    again = appliance.succeed("iptables --table nat --list-rules LOOM-EXPOSE")
    assert again == nat, f"restart changed the ruleset:\n{nat}\n---\n{again}"

    # And stopping takes them away again, so a box can be unexposed without a
    # reboot.
    appliance.succeed("systemctl stop loom-expose.service")
    appliance.fail("iptables --table nat --list-rules LOOM-EXPOSE")
    assert "-j LOOM-FORWARD" not in appliance.succeed(
        "iptables --list-rules DOCKER-USER"
    )
    appliance.succeed("systemctl start loom-expose.service")


def interface_rename(appliance: "Machine", subtest: "Subtest") -> None:
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


def radios(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("radios are disabled"):
        appliance.wait_for_unit("loom-rfkill-block.service")
        for module in ["bluetooth", "btusb", "cfg80211", "mac80211"]:
            # -R, not -r: everything in /etc/modprobe.d is a symlink into
            # /etc/static, and -r skips symlinks it finds while walking a
            # directory. -r here silently matches nothing at all.
            appliance.succeed(f"grep -R 'blacklist {module}' /etc/modprobe.d/")
