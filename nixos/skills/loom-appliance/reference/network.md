# Network

In run mode the box is an island. It owns a subnet, hands out addresses on it, answers DNS for it,
and publishes Loom onto it. Nothing routes off the box — the lease names the box as the default
gateway so that captive-portal detection works at all, and everything aimed off the segment is
refused immediately.

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

The appliance serves **both** `http` and `https` — on every image except one. It is built with
Loom's `--enable-http`, which widens every ingress to Traefik's `web` entrypoint as well as
`websecure`, so that the captive portal has a page a visitor's phone can reach without being
handed a CA.

**`--require-client-cert` changes this.** There `--enable-http` is deliberately dropped, so port 80
carries only the global redirect to https and nothing is served in cleartext — a plaintext
entrypoint beside a client-certificate requirement would be a way around it. On that box a refused
TLS handshake from a client holding no certificate is the *correct* answer, not a fault to debug.
`loom-appliance/facts.md` says which image this is.

Probe it with `loom-curl`, which holds the anchor for the self-signed certificate and the client
certificate where one is required. Plain `curl` needs `--insecure` for the first and cannot do the
second at all:

```bash
loom-curl --silent --output /dev/null --write-out '%{http_code}\n' https://frontend.loom
curl --silent --output /dev/null --write-out '%{http_code}\n' http://frontend.loom
```

On a `--require-client-cert` box the second line answering `302` is the global redirect, which is
all port 80 carries there, rather than a fault. Anywhere else, `http` answering while `https` does
not is a certificate problem and not a routing one.

## Publishing Loom

DHCP and DNS come from dnsmasq. Reaching the actual stack is `loom-expose`, a **different** unit
that installs DNAT rules — so one working says nothing about the other.

```bash
systemctl status loom-expose
sudo iptables --table nat --list-rules LOOM-EXPOSE
```

If the rules are there and a client still gets nothing, the stack is probably still coming up.
`loom-curl https://frontend.loom` from the box goes straight to Traefik and separates "not
exposed" from "not up yet" in one command.

## The captive portal page

A phone that joins the network is redirected to the page, which is served by **this box** rather than
by the cluster — so it answers long before Loom does, and its own failures have nothing to do with the
stack. The redirect names the box's portal *address* rather than `portal.loom`, so that a client whose
resolver the box does not control can still follow it; the name is served too, and is what the page
prints for somebody coming back later.

The resolver answers **every** name with that address, not a list of known probes: a client that cannot
resolve its probe concludes there is no internet rather than that there is a portal. A handful of names are
carved out (`dns.msftncsi.com`, `use-application-dns.net`, the iCloud Private Relay mask hosts and
`wpad`), and port 53 and port 80 off the segment are redirected to the box for clients that ignore the
lease's resolver entirely.

```bash
systemctl status loom-portal              # the page server, on 127.0.0.1:18082 behind nginx
systemctl status loom-portal-certificate  # publishes the certificate Loom serves, hourly
curl --silent http://portal.loom/ | head  # the page itself
ls /run/loom-portal/validated | wc -l     # devices that pressed "stop the warning"
```

The last one is the page's fourth section: until a visitor presses that button every connectivity
probe gets the redirect, and afterwards that client's probes get the success answer its vendor wants,
so the device stops warning about the network. The markers are keyed digests on tmpfs, expire after
twelve hours, and are gone at reboot.

If the page says the certificate is **not available yet**, `loom-portal-certificate` is still waiting
for the cluster — that is the normal state for the first part of a box's life, and
`journalctl --unit loom-portal-certificate` says so in one line.

On a box built with `--require-client-cert` the page also issues client certificates, and three more
units are involved:

```bash
sudo cat /run/loom-portal/password        # today's password, also on the login screen
journalctl --unit loom-portal-password    # it rotates at midnight
journalctl --unit loom-portal-issue       # every certificate the page has handed out
loom-curl --silent https://portal.loom/ | grep '<form'
```

`loom-portal-issue` runs as root and is started by a `systemd.path` watching
`/run/loom-portal/requests`; the page server itself is unprivileged and has no cluster access at all.
A visitor who gets "Loom is still starting" is being told the mutual TLS CA does not exist yet.

## A client that loses its own internet

Expected. The box's DHCP lease names it as the default gateway and the box has no upstream, so a
cabled laptop's other traffic goes to an island. This is deliberate and is what makes the portal
reachable — a client with no route to the box never sends it a probe. Confirm on the client with
`ip route` (`route print` on Windows): `default via <box address>`.

Unplugging restores it. To stay cabled, delete that route on the client (it returns at the next lease
renewal) and open the portal by address by hand, since nothing will offer it any more.

## Full detail

`/home/loom/loom/Documentation/appliance.md`:

- `## Troubleshooting` — the symptom list, including both cases above
- `### Finding Loom without being told where it is` — the captive portal
- `### What the portal page offers` — and the certificate it hands out
- `### Visitors get their own certificate from the portal` — the `--require-client-cert` build
- `## Using Loom on the appliance`

`/home/loom/loom/Documentation/installation.md`:

- `### Hostnames and the self-signed certificate` — why the certificate names each host explicitly
