# Disks, the USB key, and USB ingest

## How the box is encrypted

The internal disk is LUKS-encrypted. The key is **not** on the box — it lives on the USB stick the
box was installed from. That stick has to be present at boot, and the box watches for it while it
runs.

This means physical possession of the stick is the trust boundary. Treat the stick and the recovery
passphrase as the two ways in, and do not help anyone read, copy or print key material. If an
operator has lost both, there is no recovery — the data is gone by design.

```bash
lsblk
sudo cryptsetup status <mapper-name>
df --human-readable
```

## The key guard

`loom-key-guard` watches the key stick while the box runs and **powers the box off** when it is
pulled. That is intended behaviour, not a fault.

```bash
systemctl status loom-key-guard
journalctl --unit loom-key-guard --no-pager --lines 50
loom-info                                 # reports key state on the banner
```

An unexpected shutdown with nothing else in the log is usually this: the stick was removed, or a
port was bumped.

## The box asks for a passphrase at boot

The stick is missing, in a different port, or its key partition is empty. The recovery passphrase
gets past it. On an image built with `--lock-key` there is an additional passphrase prompt for the
key container itself, before the root is opened.

Do not read these out, store them, or write them to a file. Point the operator at
`## Locking the stick's key` and `### If the passphrase is refused` in
`/home/loom/loom/Documentation/appliance.md`.

## USB ingest

Plugging a USB stick in mounts it **read-only** and copies what is on it into Loom. The key stick
is never touched.

```bash
loom-usb-status                                   # what the last ingest did
systemctl status 'loom-usb-ingest@*'
journalctl --unit 'loom-usb-ingest@*' --no-pager --lines 100
lsblk --fs
```

Nothing happening after a stick is plugged in usually means one of:

- the filesystem is not one of the types ingest accepts — `loom-usb-status` and the journal say so;
- the device was recognised as the key stick, which is deliberately skipped;
- the cluster is not up yet, so there is nowhere to put the files. Check `loom-ready` first.

See `### Ingesting data from USB` in `/home/loom/loom/Documentation/appliance.md`.

## Disk filling up

An appliance disk is sized for Loom, and a full one is not recoverable from the console.

```bash
df --human-readable
du --max-depth 1 --human-readable /home/loom 2>/dev/null | sort --human-numeric-sort
```

The usual consumers are container images, the Elasticsearch index and the object store.

Clearing indexed data has two routes **on the box**, and `wipe-data` is not one of them: that is a
devenv script that shells out to poetry, and this box has neither (`nixos/box.nix`: "devenv is
deliberately not used on the appliance").

- `POST /v1/wipe-data` on the API — see `loom-usage/reference/api.md`. Destroys everything Loom has
  ingested and leaves the box running.
- The installer menu's **ERASE ALL DATA** entry, booted from the stick. Destroys the pool itself.

Both are destructive: say which one you would run and what it takes with it, and let the operator
decide.
