# Systemd units and the journal

## Reading the journal

The operator account can read the full system journal, so these work without `sudo`:

```bash
journalctl --unit loom.service --no-pager --lines 200
journalctl --unit loom.service --follow
journalctl --boot --priority err --no-pager      # everything that failed this boot
journalctl --since "10 min ago" --no-pager
systemctl --failed
systemctl status <unit>
systemctl list-units 'loom*'
```

`systemctl status` truncates. When a unit failed and the status output does not say why, go to
`journalctl --unit <name>` for the whole thing.

## The two boot modes

The box boots in one of two modes, and which one it is in changes what should be running.

- **Run mode** — the normal appliance. `loom.service` brings the cluster up offline from what is
  already on the disk.
- **Setup mode** — first-time setup, used once after installation. `loom-fetch.service` builds or
  pulls every container image. This takes **hours** and needs the internet. When it finishes the
  box promotes its boot entry and setup mode is gone for good.

```bash
systemctl status loom.service        # run mode
systemctl status loom-fetch.service  # setup mode
```

A message like `Condition check resulted in loom-fetch.service being skipped` is normal in run
mode — the unit is deliberately not running.

See `## The two boot modes` in `/home/loom/loom/Documentation/appliance.md`.

## Bring-up

| Unit | What it does |
| --- | --- |
| `loom.service` | Run mode: brings the whole cluster up offline. Oneshot, stays active |
| `loom-fetch.service` | Setup mode: fetches every container image. Hours |
| `loom-seed-repo` | Copies the embedded checkout into `/home/loom/loom`. Runs once, ever |
| `loom-ready` | Polls the cluster and publishes bring-up progress for the console to draw |

`loom-ready` is deliberately not ordered after `loom.service`, so it reports during bring-up too.
`loom-ready` as a command prints the same thing on demand.

## Network

| Unit | What it does |
| --- | --- |
| `loom-interface-fallback` | Claims a wired NIC as `loom0` when no platform rule matched |
| `loom-bridge-attach` | Attaches the wired port to the appliance bridge |
| `loom-bridge-tune` | Pins forwarding behaviour on the bridge |
| `loom-expose` | Installs the DNAT rules that publish Loom on the appliance address |
| `loom-network-check` | Reports how the interface was chosen, onto the login screen |
| `loom-rfkill-block` | Hard-blocks the radios. On a WiFi build, bluetooth only |

## Console and branding

| Unit | What it does |
| --- | --- |
| `loom-issue` | Writes the login banner before the getty starts |
| `loom-banner-repaint` | One late redraw once the console has stopped resizing |
| `loom-console-font` | Re-applies the console font once the display has settled |

## Storage and USB

| Unit | What it does |
| --- | --- |
| `loom-key-guard` | Watches the LUKS USB key and powers the box off when it is pulled |
| `loom-usb-ingest@.service` | Templated per device — mounts USB media and ingests it |
| `loom-usb-release` | Forgets media that has been unplugged |

There are no timers on this box. Anything periodic inside Loom is Celery beat, in the cluster, not
systemd.

## When a unit will not start

1. `systemctl status <unit>` — the exit status and the last few lines.
2. `journalctl --unit <unit> --no-pager` — the whole log, which is usually where the real error is.
3. `systemctl cat <unit>` — what it actually runs. On NixOS this is a store path; read it, do not
    edit it.
4. `systemctl list-dependencies <unit>` — if it never started at all, something it needs failed
    first.

Do not try to fix a unit by editing files under `/nix/store`; it is read-only, and the next boot
would undo it anyway.
