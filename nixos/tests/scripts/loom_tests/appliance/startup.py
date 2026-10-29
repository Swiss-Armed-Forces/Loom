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

    with subtest("the checkout carries this platform's appliance values"):
        # repo.nix writes `loom.applianceValues` into charts/values-appliance.yaml,
        # which skaffold lists after the values file up.sh generates and therefore
        # applies over every up.sh flag. Parsed through the box's own yq rather than
        # compared as text: what has to match is the values, and the generator's
        # formatting is not part of the claim.
        appliance_values = f"{params.operator.repo_dir}/charts/values-appliance.yaml"
        got = (
            json.loads(appliance.succeed(f"yq --compact-output . {appliance_values}"))
            or {}
        )
        want = json.loads(params.appliance_values_json)
        # Every declared value must be in there, rather than the file being exactly
        # them. The committed copy is comments only -- it parses to `null`, the `or {}`
        # above. What is being asserted is that the platform's landed.
        for key, value in want.items():
            assert got.get(key) == value, f"{key}: {got.get(key)} != {value}"

    with subtest("the operator's own values file is left alone"):
        # charts/values-overwrites.yaml is the last word in the chart and belongs to
        # whoever deploys Loom. It is `--skip-worktree` in a developer's clone so that
        # real content can live in it, and these tests run with `repoSrc ./.` -- so a
        # seed that wrote it would overwrite the values of the person running them.
        #
        # Asserted by the absence of the seed's own header rather than by a diff: the
        # file is `--skip-worktree`, so `git status` would report a clean tree whatever
        # was written to it, and its content is by definition whatever the operator put
        # there.
        overwrites = f"{params.operator.repo_dir}/charts/values-overwrites.yaml"
        content = appliance.succeed(f"cat {overwrites}")
        assert (
            "Written by the Loom appliance" not in content
        ), f"the seed wrote values-overwrites.yaml:\n{content}"


def loom_up_flags(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("loom-up reaches up.sh with the skip flags"):
        out = appliance.succeed(f"runuser -u {params.operator.user} -- loom-up --help")
        assert "--skip-STEP" in out, out
        # There is no cluster on this box, so `minikube ip` fails. That answer
        # means "nothing to compare yet", and the wrapper has to say so and carry
        # on: the boot that creates the cluster is the one no pre-flight can
        # check, and folding the failure into the comparison makes the guard pass
        # silently on exactly that boot.
        assert "No minikube cluster" in out, out


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
            # The other half of "agree": a login shell, which reads it from
            # /etc/profile.
            shell = appliance.succeed(
                f"runuser -l {params.operator.user} -c 'echo ${var}'"
            ).splitlines()[-1]
            assert shell == want, f"{var}: unit says {want}, shell says {shell}"


def skaffold_metrics(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("skaffold reports no usage metrics from this box"):
        # box.nix seeds skaffold's global config with `collect-metrics: false`.
        # Without it skaffold announces on its first run that it collects anonymized
        # usage data and then reports to firebaselogging-pa.googleapis.com -- during
        # first-time setup, which is the one boot this box spends on a real network.
        config = f"{params.operator.home}/.skaffold/config"
        stat = appliance.succeed(f"stat -c '%U %a' {config}").strip()
        assert stat == f"{params.operator.user} 644", stat

        # The assertion that matters, and the reason it is made through skaffold
        # rather than by reading the file: the path above is $HOME-derived, and
        # SKAFFOLD_HOME -- which the box also sets, to somewhere else entirely -- has
        # nothing to do with it (see box.nix's `environment.sessionVariables`). Asking
        # skaffold re-derives the path the way skaffold does, so seeding the file
        # under SKAFFOLD_HOME instead fails here rather than shipping.
        listed = appliance.succeed(
            f"runuser -l {params.operator.user} -c 'skaffold config list --all'"
        )
        assert "collect-metrics: false" in listed, listed


def docker(appliance: "Machine", subtest: "Subtest") -> None:
    with subtest("docker is available for the minikube driver"):
        appliance.wait_for_unit("docker.service")
        appliance.succeed("docker info")


def exposure(appliance: "Machine", subtest: "Subtest", params: Params) -> None:
    with subtest("Loom is published on the appliance address"):
        # The one thing a visitor actually depends on: without it the box hands
        # out leases and resolves every *.loom name to its own address while
        # nothing whatsoever listens there, and the only symptom is a connection
        # refused from the laptop.
        appliance.wait_for_unit("loom-expose.service")
        box = f"{params.loom_subnet}.1"
        portal = f"{params.loom_subnet}.2"
        segment = f"{params.loom_subnet}.0/24"

        # DNAT: the appliance address becomes the minikube node, which is where
        # traefik's hostPort lives.
        nat = appliance.succeed("iptables --table nat --list-rules LOOM-EXPOSE")
        for port in ["80", "443"]:
            rule = next(
                (
                    line
                    for line in nat.splitlines()
                    if f"--dport {port} " in line and f"-d {box}/32" in line
                ),
                None,
            )
            assert rule, nat
            assert f"--to-destination {params.minikube_ip}:{port}" in rule, rule
            assert "-i loom0" in rule, rule

        # And the catch-all rules, for a client that does not use the resolver in
        # its lease -- a hardcoded 8.8.8.8, an MDM profile, an encrypted-DNS
        # setting. Without them, DNS interception is only as good as the
        # client's willingness to cooperate with it.
        # In the order iptables prints them, which is not the order they were
        # written: `--list-rules` emits the destination match before the
        # interface one.
        for proto in ["udp", "tcp"]:
            assert (
                f"! -d {segment} -i loom0 -p {proto} -m {proto} --dport 53 "
                f"-j DNAT --to-destination {box}:53"
            ) in nat, nat

        # Port 80 to the responder and not to the box, which is DNAT'd to
        # Traefik above -- DNAT is terminal, so a packet sent there would reach
        # a 404 for a Host Traefik does not route. This is the backstop the
        # whole portal rests on: every vendor's probe is plaintext http, so it
        # lands here whatever happened to DNS.
        assert (
            f"! -d {segment} -i loom0 -p tcp -m tcp --dport 80 "
            f"-j DNAT --to-destination {portal}:80"
        ) in nat, nat

        # Nothing for 443: hijacking TLS is a certificate warning in a webview
        # that offers no way past it, and a reset is faster and more honest.
        assert f"--dport 443 -j DNAT --to-destination {portal}" not in nat, nat

        # The two that make frontend.loom work have to be ahead of the
        # catch-all rules, since the first matching DNAT wins.
        lines = nat.splitlines()
        last_box_rule = max(
            index for index, line in enumerate(lines) if f"-d {box}/32" in line
        )
        first_catch_all = min(
            index for index, line in enumerate(lines) if f"! -d {segment}" in line
        )
        assert last_box_rule < first_catch_all, nat

        # Nothing else may be forwarded. The list is a decision rather than a
        # side effect, so a new one has to be made deliberately.
        assert len([line for line in lines if "DNAT" in line]) == 5, nat

        # And the FORWARD accept, without which dockerd's DROP policy eats the
        # DNAT'd packet and the symptom is identical to no DNAT at all.
        forward = appliance.succeed("iptables --list-rules LOOM-FORWARD")
        assert f"-d {params.minikube_ip}/32" in forward, forward
        assert "--dports 80,443 -j ACCEPT" in forward, forward
        assert "RELATED,ESTABLISHED -j ACCEPT" in forward, forward

        # And the blackhole, last, so the two ACCEPT rules above keep winning.
        #
        # The lease now names this box as the default route, so a client's
        # off-subnet traffic arrives here. Most dies in the routing decision
        # before this chain -- the box has no default route of its own -- but
        # traffic aimed at docker0 or the minikube bridge does not, and docker's
        # own chain accepts forwarded packets to any published container port
        # from any interface, the kube-apiserver included.
        #
        # `! -o loom0` and not a bare `-i loom0`: in a --wifi build the wired
        # port and the radio are two ports of one bridge, and br_netfilter puts
        # frames between them through this chain.
        assert forward.strip().splitlines()[-1] == (
            "-A LOOM-FORWARD -i loom0 ! -o loom0 -j REJECT "
            "--reject-with icmp-host-unreachable"
        ), forward

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

        # And the two that make the REJECT above arrive. Both default to one
        # ICMP error per second per peer, which turns "the box refused it" into
        # "the box ignored it": a browser opens six connections, one is answered
        # and five hang for the client's own timeout. That is the difference
        # between a visitor seeing a portal page and a visitor reporting that
        # the network is broken.
        for knob in ["net.ipv4.route.error_cost", "net.ipv4.icmp_ratelimit"]:
            assert appliance.succeed(f"sysctl -n {knob}").strip() == "0", knob

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

        # -R, not -r: everything in /etc/modprobe.d is a symlink into
        # /etc/static, and -r skips symlinks it finds while walking a
        # directory. -r here silently matches nothing at all.
        for module in ["bluetooth", "btusb", "cfg80211", "mac80211"]:
            appliance.succeed(f"grep -R 'blacklist {module}' /etc/modprobe.d/")
        for module in ["bluetooth", "cfg80211"]:
            appliance.succeed(f"grep -R 'install {module}' /etc/modprobe.d/")
        appliance.succeed("grep -R 'options rfkill default_state=0' /etc/modprobe.d/")

        # The assertion the config greps above cannot make. A blacklist is
        # scoped to a module's own device aliases, so it says nothing about the
        # path radios actually arrive by: a driver matches its own alias and
        # modprobe pulls the 802.11 core in behind it as a dependency. hwsim
        # depends on mac80211 and cfg80211 like any real driver, so a load that
        # fails is the dependency chain being broken rather than a file holding
        # the right words.
        appliance.fail("modprobe mac80211_hwsim")
        appliance.fail("lsmod | grep -q '^cfg80211'")
        appliance.fail("lsmod | grep -q '^bluetooth'")

        # And that a switch registering later registers blocked, which is what
        # covers the window before the unit above runs and anything hotplugged
        # after it. rfkill is loadable by design -- it is the mechanism, not a
        # radio -- so this reads the policy back off the running kernel.
        appliance.succeed("modprobe rfkill")
        assert (
            appliance.succeed("cat /sys/module/rfkill/parameters/default_state").strip()
            == "0"
        )
