# Network

In run mode the box is an island. It owns a subnet, hands out addresses on it, answers DNS for it,
and publishes Loom onto it. Nothing routes off the box.

## What this box's addresses are

Do not guess these — the subnet is randomised per image. Read them:

```bash
cat /etc/loom/network.conf    # LOOM_INTERFACE, LOOM_SUBNET, LOOM_PORTAL_ADDRESS
loom-info                     # the same, as the operator sees it on the login screen
ip --brief address
ip route
```

The box takes the `.1` address of its subnet. A laptop plugged into the wired port gets a lease
from the `.100`–`.200` range.

## The interface

The wired port Loom serves on is renamed `loom0`. If the login screen says `loom0 does not exist`,
the platform's interface rule matched nothing and the box has no address, so it serves neither DHCP
nor DNS.

```bash
loom-wired-nics                        # the wired ports this box has
loom-platform-info                     # names them, and says which the rule did and did not match
systemctl status loom-interface-fallback
systemctl status loom-network-check
```

On a box with two ethernet ports, try the other one first. The real fix is a new stick built with
`build-appliance-image --interface <name>`, using the name the box itself reports (`enp2s0`, not
`eth0`). That is done elsewhere, not here.

See `### The appliance network interface` in `/home/loom/loom/Documentation/appliance.md`.

## Names

Every `*.loom` name is pinned in `/etc/hosts` on the box itself, and served to clients by the
box's own dnsmasq.

```bash
grep loom /etc/hosts
systemctl status dnsmasq
journalctl --unit dnsmasq --no-pager --lines 50
getent hosts frontend.loom
```

The appliance serves **both** `http` and `https`. It is built with Loom's `--enable-http`, which
widens every ingress to Traefik's `web` entrypoint as well as `websecure`, so that the captive
portal has a page a visitor's phone can reach without being handed a CA.

The certificate is self-signed, so `curl` over `https` needs `--insecure`:

```bash
curl --insecure --silent --output /dev/null --write-out '%{http_code}\n' https://frontend.loom
curl --silent --output /dev/null --write-out '%{http_code}\n' http://frontend.loom
```

If `http` answers and `https` does not, that is a certificate problem, not a routing one.

## Publishing Loom

DHCP and DNS come from dnsmasq. Reaching the actual stack is `loom-expose`, a **different** unit
that installs DNAT rules — so one working says nothing about the other.

```bash
systemctl status loom-expose
sudo iptables --table nat --list-rules LOOM-EXPOSE
```

If the rules are there and a client still gets nothing, the stack is probably still coming up.
`curl --insecure https://frontend.loom` from the box goes straight to Traefik and separates "not
exposed" from "not up yet" in one command.

## A client that loses its own internet

If a laptop plugged into the box loses connectivity on every other interface, the box's DHCP lease
is naming it as the default gateway and the box has no upstream. Confirm on the client with
`ip route` (`route print` on Windows) — a `default via <box address>` is the symptom. Deleting that
route on the client is the stopgap; it returns at the next lease renewal. The real fix is a newer
stick.

## Full detail

`/home/loom/loom/Documentation/appliance.md`:

- `## Troubleshooting` — the symptom list, including both cases above
- `### Finding Loom without being told where it is` — the captive portal
- `## Using Loom on the appliance`

`/home/loom/loom/Documentation/installation.md`:

- `### Hostnames and the self-signed certificate` — why the certificate names each host explicitly
