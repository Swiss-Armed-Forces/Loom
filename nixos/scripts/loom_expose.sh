# shellcheck shell=bash
#
# The body of `loom-expose`, which DNATs the appliance address onto the
# minikube node so a visitor on the appliance segment reaches Loom, sends
# everything else at the captive portal, and tears both down again.
# nixos/network.nix reads this file into the writeShellApplication of the
# same name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly INTERFACE="${LOOM_SERVICE_INTERFACE:?nixos/network.nix must set this}"
readonly BOX="${LOOM_BOX_ADDRESS:?nixos/network.nix must set this}"
readonly PORTAL="${LOOM_PORTAL_ADDRESS:?nixos/network.nix must set this}"
readonly SEGMENT="${LOOM_SEGMENT:?nixos/network.nix must set this}"
readonly PORTAL_ENABLED="${LOOM_PORTAL_ENABLED:?nixos/network.nix must set this}"
readonly NODE="${LOOM_MINIKUBE_IP:?nixos/network.nix must set this}"
readonly PORTS="${LOOM_EXPOSED_PORTS:?nixos/network.nix must set this}"
readonly MULTIPORT="${LOOM_EXPOSED_MULTIPORT:?nixos/network.nix must set this}"


# Our own chains, jumped to from a hook each table guarantees us.
readonly NAT_CHAIN=LOOM-EXPOSE
readonly FORWARD_CHAIN=LOOM-FORWARD

up() {
    # ---------------------------------------------------------------
    # nat PREROUTING: the appliance address becomes the minikube node.
    #
    # Created-or-flushed rather than created-if-absent, so a restart
    # rebuilds the rules instead of appending a second copy of them.
    # ---------------------------------------------------------------
    iptables --table nat --new-chain "${NAT_CHAIN}" 2>/dev/null \
        || iptables --table nat --flush "${NAT_CHAIN}"

    if ! iptables --table nat --check PREROUTING \
        --jump "${NAT_CHAIN}" 2>/dev/null; then
        iptables --table nat --insert PREROUTING --jump "${NAT_CHAIN}"
    fi

    local port
    for port in ${PORTS}; do
        iptables --table nat --append "${NAT_CHAIN}" \
            --in-interface "${INTERFACE}" \
            --destination "${BOX}" \
            --protocol tcp --destination-port "${port}" \
            --jump DNAT --to-destination "${NODE}:${port}"
    done

    # ---------------------------------------------------------------
    # And everything a client aimed off this segment.
    #
    # DNS interception is only as good as the client's willingness to use
    # the resolver in its lease, and a phone with an MDM profile, a
    # hardcoded 8.8.8.8 or an encrypted-DNS setting uses something else.
    # These two rules are what make the portal reachable anyway, and the
    # port 80 one is the real backstop for all of it: every vendor's
    # connectivity probe is plaintext http, so it lands here whatever
    # happened to DNS.
    #
    # After the loop above rather than before it, although the
    # `! --destination` below already excludes the box. The rules that
    # make frontend.loom reach Traefik are the ones a reader has to see
    # winning, and an ordering that doubles as the correctness argument
    # costs nothing.
    #
    # The exclusion is the whole /24 and not two addresses: iptables
    # takes one --destination per rule, and the segment is the honest
    # unit anyway. The box, the responder and every other client are
    # things on this wire, and nothing here should touch traffic between
    # them.
    # ---------------------------------------------------------------

    local proto
    for proto in udp tcp; do
        iptables --table nat --append "${NAT_CHAIN}" \
            --in-interface "${INTERFACE}" \
            ! --destination "${SEGMENT}" \
            --protocol "${proto}" --destination-port 53 \
            --jump DNAT --to-destination "${BOX}:53"
    done

    # To the responder, and emphatically not to the box: port 80 on the
    # box is DNAT'd to Traefik four rules above, DNAT is terminal, and a
    # packet sent there would leave this chain and reach a 404 for a Host
    # Traefik does not route.
    #
    # Nothing for 443. Hijacking TLS produces a certificate warning in a
    # webview that offers no way past it; the reset a client gets from a
    # closed port is both faster and more honest.
    #
    # Guarded in the shell rather than by building the script two ways,
    # so there is one script to read and shellcheck sees all of it. With
    # `loom.portal.enable = false` there is no listener on that address,
    # and sending every client's http there would hang them on a SYN
    # rather than fail -- the same reason the dnsmasq wildcard is gated.
    if [[ "${PORTAL_ENABLED}" = 1 ]]; then
        iptables --table nat --append "${NAT_CHAIN}" \
            --in-interface "${INTERFACE}" \
            ! --destination "${SEGMENT}" \
            --protocol tcp --destination-port 80 \
            --jump DNAT --to-destination "${PORTAL}:80"
    fi

    # ---------------------------------------------------------------
    # filter FORWARD: and then it has to be allowed across.
    #
    # This is the half that is easy to miss. dockerd sets the FORWARD
    # policy to DROP, so a DNAT'd packet crossing from the appliance
    # NIC to the minikube bridge is dropped by default and the symptom
    # is indistinguishable from the DNAT not being there at all.
    #
    # DOCKER-USER is docker's documented hook for this: it is jumped to
    # ahead of every docker-generated FORWARD rule and docker never
    # edits its contents. Created here only as a fallback -- `After`
    # and `Requires` on docker.service mean it normally exists already,
    # and creating it ourselves would otherwise leave a chain nothing
    # jumps to.
    # ---------------------------------------------------------------
    iptables --new-chain "${FORWARD_CHAIN}" 2>/dev/null \
        || iptables --flush "${FORWARD_CHAIN}"

    iptables --new-chain DOCKER-USER 2>/dev/null || true
    if ! iptables --check FORWARD --jump DOCKER-USER 2>/dev/null; then
        iptables --insert FORWARD --jump DOCKER-USER
    fi
    if ! iptables --check DOCKER-USER \
        --jump "${FORWARD_CHAIN}" 2>/dev/null; then
        iptables --insert DOCKER-USER --jump "${FORWARD_CHAIN}"
    fi

    # Matched on the node's address rather than on the bridge it is
    # behind: that bridge is `br-<docker network id>`, which changes
    # every time the cluster is deleted and recreated.
    iptables --append "${FORWARD_CHAIN}" \
        --in-interface "${INTERFACE}" \
        --destination "${NODE}" \
        --protocol tcp --match multiport --dports "${MULTIPORT}" \
        --jump ACCEPT

    # The replies. docker's own per-network rules happen to cover these
    # today, which is not something to depend on for the direction that
    # makes the whole thing work.
    iptables --append "${FORWARD_CHAIN}" \
        --out-interface "${INTERFACE}" \
        --match conntrack --ctstate RELATED,ESTABLISHED \
        --jump ACCEPT

    # ---------------------------------------------------------------
    # And nothing else crosses this box.
    #
    # The lease now names the box as the default gateway, so a client's
    # off-subnet traffic arrives here to be forwarded, and ip_forward is
    # on for the DNAT above. Most of it dies in the routing decision
    # before this chain is reached, because the box itself has no default
    # route. What does not is traffic aimed at a network the box *can*
    # reach: docker0 and the minikube bridge. docker's own DOCKER chain
    # accepts forwarded packets to any published container port from any
    # interface, which on this box includes the kube-apiserver -- so
    # without this rule a visitor with a default route via the box can
    # reach it. That is worth closing on its own account, portal or no
    # portal.
    #
    # Last in the chain, so the two ACCEPT rules above keep winning: a
    # 80/443 to the node, and the replies coming back.
    #
    # REJECT and not DROP. A drop is a thirty-second hang in a browser tab
    # and an afternoon of somebody's patience; icmp-host-unreachable takes
    # connect() out of SYN_SENT immediately on every client OS here, and
    # reads correctly in ping -- which is more than icmp-admin-prohibited
    # manages, since that surfaces as "Permission denied". The rate limit
    # that would otherwise make this hang anyway is lifted in the sysctls
    # above.
    #
    # `! --out-interface` rather than a bare `--in-interface`, and it
    # matters only in the --wifi build, where it matters a lot: dockerd
    # loads br_netfilter, so frames bridged between the wired port and the
    # radio traverse this chain as in and out of the same bridge. A bare
    # rule would start rejecting wired-to-wireless traffic that today
    # falls through to the FORWARD policy, and would answer client
    # broadcasts with ICMP. This leaves the inside of the bridge exactly
    # as it is -- hostapd's apIsolate still owns radio-to-radio -- and
    # takes away only the routed path out.
    # ---------------------------------------------------------------
    iptables --append "${FORWARD_CHAIN}" \
        --in-interface "${INTERFACE}" \
        ! --out-interface "${INTERFACE}" \
        --jump REJECT --reject-with icmp-host-unreachable

    echo "[*] Loom is exposed on ${BOX} ports ${MULTIPORT} (via ${NODE})."
}

# Never fails. This runs as ExecStop, including on the way to a
# shutdown that is about to discard the whole ruleset anyway, and a
# rule that somebody already removed by hand is not a failure worth
# refusing to stop over.
down() {
    if iptables --table nat --check PREROUTING \
        --jump "${NAT_CHAIN}" 2>/dev/null; then
        iptables --table nat --delete PREROUTING --jump "${NAT_CHAIN}" || true
    fi
    iptables --table nat --flush "${NAT_CHAIN}" 2>/dev/null || true
    iptables --table nat --delete-chain "${NAT_CHAIN}" 2>/dev/null || true

    if iptables --check DOCKER-USER \
        --jump "${FORWARD_CHAIN}" 2>/dev/null; then
        iptables --delete DOCKER-USER --jump "${FORWARD_CHAIN}" || true
    fi
    iptables --flush "${FORWARD_CHAIN}" 2>/dev/null || true
    iptables --delete-chain "${FORWARD_CHAIN}" 2>/dev/null || true
}

case "${1:-}" in
    up)   up   ;;
    down) down ;;
    *)
        echo >&2 "usage: loom-expose up|down"
        exit 1
        ;;
esac
