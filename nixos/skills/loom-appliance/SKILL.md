---
name: loom-appliance
description: "Operating and diagnosing this Loom appliance box itself. Use for: the box will not come up, a pod is not ready, systemd units, journalctl, kubectl, k9s, minikube, docker, IP addresses, the loom0 interface, dnsmasq, DNS, the ingress, WiFi, the GPU, LUKS and the USB key, USB ingest, disks, firmware, console and boot problems, and anything named loom-*. Not for searching or uploading documents, which is the loom-usage skill."
---

# Loom appliance operations

This is a single-node, air-gapped Loom appliance: NixOS on bare metal, running Loom on a
one-node minikube cluster. There is no network off this box, no browser on it, and no remote
access. Everything here is done from the console.

Start every diagnosis with the two commands below before reaching for anything else.

```bash
loom-ready            # how far the bring-up got, and what it is waiting on
loom-platform-info    # what this hardware actually is, beside what the image expected
```

## Ground facts

| Thing | Value |
| --- | --- |
| Kubernetes namespace | `loom` |
| Loom checkout (source and docs, writable) | `/home/loom/loom` |
| Operator account | `loom` — in `wheel`, passwordless `sudo` |
| Service names | `*.loom`, pinned in `/etc/hosts`. Both `http` and `https` are served |
| Consoles | tty1 is the Loom session; `Alt-F2`…`Alt-F6` are plain shells |

Paths in this skill are absolute on purpose. `loom-chat` started from an `Alt-F2` prompt has a
different working directory than the console pane, so a relative path is not reliable here.

## First moves by symptom

| Symptom | Start here |
| --- | --- |
| Nothing is up / bring-up seems stuck | `loom-ready`, then `systemctl status loom.service` |
| A pod is crashlooping or pending | `kubectl --namespace loom get pods`, then `reference/kubernetes.md` |
| A laptop gets no address, or `*.loom` does not resolve | `reference/network.md` |
| A laptop resolves but nothing loads | `systemctl status loom-expose`, then `reference/network.md` |
| Login screen says `loom0 does not exist` | `loom-wired-nics`, then `reference/network.md` |
| The WiFi access point is missing | `systemctl status loom-wifi-check`, then `reference/wifi.md` |
| Ollama or the AI features do not work | `reference/gpu.md` |
| A USB stick was plugged in and nothing happened | `loom-usb-status`, then `reference/storage-usb.md` |
| The box asks for a passphrase at boot | `reference/storage-usb.md` |
| A unit failed and the reason is unclear | `reference/units.md` |

## Commands this box has

Read-only, safe to run while diagnosing:

```bash
loom-ready                      # bring-up progress and what is blocking it
loom-platform-info              # hardware vs. what nixos/platforms/<id>.nix declared
loom-platform-info --json       # the same, machine-readable
loom-info                       # the login banner: addresses, key state, recovery info
loom-wired-nics                 # wired interfaces, most-stable PCI path first
loom-usb-status                 # what USB ingest last did
loom-k9s                        # the cluster browser, pinned to the loom namespace
kubectl --namespace loom get pods
journalctl --unit loom.service --no-pager --lines 200
systemctl --failed
```

Mutating. Do not run these to investigate — say what you would run and let the operator decide:

```bash
loom-up                         # bring the cluster up
loom-down                       # take it down
loom-expose                     # (re)install the DNAT rules that publish Loom
```

Never propose `kubectl edit`, `helm upgrade`, or editing anything under `/nix/store`. The store is
read-only, and configuration on this box is not changed in place — Loom is taken down and brought
back up, and the image itself is rebuilt elsewhere and reflashed.

## Going deeper

Each file below is self-contained. Read the one that matches; they do not refer to each other.

| File | What is in it |
| --- | --- |
| `reference/units.md` | The systemd units, run mode vs. setup mode, reading the journal |
| `reference/kubernetes.md` | The namespace, what each workload is, the Celery queue chain |
| `reference/network.md` | Addresses, `loom0`, dnsmasq, `*.loom`, the ingress, `loom-expose` |
| `reference/storage-usb.md` | The LUKS root, the USB key, the key guard, USB ingest |
| `reference/gpu.md` | The GPU, Ollama, and why the AI services follow it |
| `reference/wifi.md` | The optional access point |
| `facts.md` | What this particular image was built with |

## The documentation on this box

The full Loom documentation is in the checkout and is more detailed than this skill. Read it when
the reference files above do not settle the question:

- `/home/loom/loom/Documentation/appliance.md` — the appliance itself. Its `## Troubleshooting`
  section is a symptom-by-symptom list and is the best single thing to read for a box that is
  misbehaving. Also `## The two boot modes`, `## The USB key guard`, `## GPU support`.
- `/home/loom/loom/Documentation/installation.md` — the Helm chart and the values Loom is deployed
  with, including `### Hostnames and the self-signed certificate`.
- `/home/loom/loom/nixos/README.md` — how this image is put together.
