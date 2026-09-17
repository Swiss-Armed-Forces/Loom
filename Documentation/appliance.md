# Appliance Deployment

[[_TOC_]]

An **appliance** is a standalone Loom box provisioned from a single USB stick. It is built for sites with no
internet: it serves its own network, resolves every `*.loom` name to itself, and encrypts its disk with a key
that lives on the stick rather than on the box.

This is a third deployment schema alongside [Single Node](installation.md#single-node-deployment) and
[Multi Node](installation.md#multi-node-deployment). Use it when the box has to be handed to someone else,
or run somewhere you cannot reach.

## Threat model

Read this before building anything; the design only makes sense if these hold.

- **The USB stick is the key.** The internal disk is LUKS2, and the key is 4096 random bytes on the stick. Pull
  the stick and the box will not boot. Every stick gets its own key.
- **Box and stick together are not protected.** If both are seized at once, the encryption buys you nothing.
  The design assumes the stick is removed, or travels separately, whenever the box is unattended.
- **Lose the stick and the data is gone**, unless somebody wrote down the recovery passphrase that the
  installer prints and that every console login repeats. Use `--key-backup` if you want a second copy.
- **There is no remote access.** No sshd, no accounts but the local operator. The console is the only way in.
- **WiFi and Bluetooth are disabled** by module blacklist and `rfkill`. That is a software guarantee; disable
  the radios in the Spark's firmware as well if the site requires it.

## What you need

- A **DGX Spark** (or another aarch64 box) as the appliance.
- An **aarch64 build host**. The image contains a NixOS closure for the appliance, and cross-building one under
  emulation takes hours, so the build runs natively. A Spark can build sticks for its siblings.
- A **USB stick of 16 GB or more**. The stick stays with the box permanently.
- An internal disk of **at least 250 GB** — the container images alone are around 60 GB.
- Secure Boot **disabled** in the Spark's firmware, otherwise it will not boot the stick.

## Building a stick

```bash
build-appliance-image --tag 1.4.0 --flash /dev/sdX --key-backup ~/loom-key-boxA.bin
```

Without `--flash` it only produces the image, under `.appliance-build/`. Useful options:

| Option | Meaning |
| --- | --- |
| `--tag TAG` | Loom release to embed. Defaults to the newest tag, with a confirmation prompt. |
| `--flash DEVICE` | Write the image to `DEVICE` and provision its key partition. Destroys everything on it. |
| `--key-backup FILE` | Also write the LUKS key to `FILE`, mode 0400. Store it away from the box. |
| `--subnet A.B.C` | Pin the appliance subnet. Defaults to a random `10.x.y`. |
| `--interface NAME` | The appliance's network interface. Defaults to `eth0`. |
| `--yes` | Skip confirmation prompts. |

The tag matters: the appliance runs Loom in offline mode, which refuses to start unless the checkout sits on an
exact tag. The build embeds a clean clone at that tag, with git-lfs payloads materialised, and verifies all of
that before producing an image.

Each stick gets a **random `10.<a>.<b>.0/24` subnet**. That keeps two boxes on one wire from colliding, and
keeps the box from clashing with a visitor's own network. The chosen subnet is printed at the end of the build
and shown on every console login.

## Installing

1. Plug the stick into the box and boot from it.
2. The installer menu appears on the console and on serial. It shows which disk is the boot medium (never
   touched) and which is the install target.
3. Choose **Install**. It asks for the target disk's serial number, then for the word `INSTALL` — deliberately,
   so it cannot be confirmed by muscle memory on the wrong machine.
4. It partitions the internal disk, creates the LUKS container from the stick's key, installs the appliance
   closure entirely offline, enrols a recovery passphrase, and makes the internal disk the default boot entry.
5. **Write down the recovery passphrase it prints.**
6. Reboot, leaving the stick in.

The installer moves its own loader off the UEFI removable-media path afterwards. Without that, most firmware
would boot the installer instead of the appliance on every restart, because the stick never leaves. The
installer stays reachable from the firmware's own boot menu for reinstalls and wipes.

## The two boot modes

The appliance has two entries in its boot menu.

| | Run (default) | Setup |
| --- | --- | --- |
| Network | Static address, serves DHCP and `*.loom` | DHCP client |
| Loom | Starts offline and exposed on the appliance network | Builds and pulls every container image |
| When | Normal operation | Once, in the lab, with internet |

A fresh box has no container images, and building them needs registries. So the first boot after installation is
into **Setup**, on a network with internet:

```bash
# Choose "Loom (setup)" in the boot menu, then watch:
journalctl -fu loom-fetch
```

This takes a long time. It populates minikube's image store on the encrypted root and marks itself complete, so
a reboot will not repeat it. When it finishes, reboot into the default entry and the box runs offline forever.

This is also why the stick does not need to carry 60 GB of container images.

## Using Loom on the appliance

Plug a laptop into the box's ethernet port. It gets an address by DHCP, and `dnsmasq` answers for every name
under `.loom`, so this just works:

```text
https://frontend.loom
```

No hosts file, no configuration on the visitor's side. The other services — `grafana.loom`, `open-webui.loom`,
`elasticvue.loom` and the rest — resolve the same way.

The box is not a gateway and does not advertise itself as one, so the laptop keeps whatever other networking it
has.

### From the box's own console

Log in as `loom` on the console. `loom-up` and `loom-down` wrap `up.sh` with the two flags the appliance needs:

```bash
loom-up --offline --expose 10.13.37.1     # whatever subnet the banner shows
loom-down
```

Use these rather than `./up.sh` directly. Bare `up.sh` would rewrite `/etc/hosts` and `/etc/sysctl.d`, both of
which this appliance declares through NixOS — it would undo its own configuration. `loom-up` passes
`--skip-setup_system --skip-install_host_entries` for exactly that reason, and forwards everything else through.

## Wiping a box

Boot the stick (via the firmware boot menu) and choose **ERASE ALL DATA**. The same interlock applies: it prints
what will be destroyed and what will not, and asks for the target's serial number.

The wipe is layered, cheapest first. Because the disk is encrypted, erasing the LUKS keyslots _is_ the wipe and
takes under a second; everything after it is defence in depth:

1. `cryptsetup luksErase` on each container
2. random data over the headers, then `wipefs`
3. `sgdisk --zap-all`
4. `blkdiscard`
5. `nvme format --ses=1`, falling back to `--ses=2`

Layers that a given drive does not support are skipped and reported. A full overwrite is deliberately not the
default: on a wear-levelling NVMe it takes hours and still cannot reach retired or over-provisioned blocks, so it
is both slower and weaker than a controller-level erase.

## GPU support

**GPU support is not implemented yet** — the appliance ships CPU-only, and `--gpu` refuses to run.

Mainline Linux boots the DGX Spark but is reported to lose both the GPU and the ConnectX-7 networking, which
NVIDIA provides through their own kernel fork. Since the appliance's DHCP and DNS depend on that interface,
this needs validating on real hardware before the driver module is written. The first thing to try is booting
a stock NixOS aarch64 image on a Spark and checking whether the ethernet port comes up.

The plumbing (`enableGpu`, and the `--gpus all` that run mode would pass to `up.sh`) is already in place; what
is missing is the NixOS module carrying the driver and the container toolkit.

## Troubleshooting

**The box boots into the installer every time.** The firmware is preferring the stick's removable-media path.
Re-run the install, or set the internal disk first in the firmware boot order.

**The box will not boot and asks for a passphrase.** The stick is missing, in a different port, or its key
partition is empty. Enter the recovery passphrase, then check the stick — the installer menu's status screen
reports whether a key is present.

**`loom-up` refuses to start, complaining about the minikube address.** The `*.loom` names are pinned to
`192.168.49.2` in `/etc/hosts` and minikube came up somewhere else. `minikube delete` and retry.

**Loom does not come up after a reboot in run mode.** Check `journalctl -u loom`. If the image store was never
populated, boot into Setup mode first.
