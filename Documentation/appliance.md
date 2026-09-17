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
  the radios in the box's own firmware as well if the site requires it.

## Supported platforms

Two boxes are supported. Pick one with `--platform`; it decides the architecture and everything else that
differs between them.

| | `spark` (default) | `evo-x2` |
| --- | --- | --- |
| Box | NVIDIA DGX Spark | GMKtec EVO-X2 (AMD Ryzen AI Max+ 395) |
| Architecture | `aarch64-linux` | `x86_64-linux` |
| Build host | aarch64 — a Spark can build sticks for its siblings | any ordinary x86_64 machine |
| Console | serial or monitor | monitor and USB keyboard (no serial port) |
| Network | ConnectX-7, one port | 2.5GbE, two ports |
| GPU | not supported (see below) | not supported (see below) |

Everything else — the LUKS-key-on-stick scheme, the two boot modes, the installer and the wipe — is identical.

## What you need

- One of the boxes above.
- A **build host of the same architecture**. The image carries a whole NixOS closure for the appliance, and
  cross-building needs an emulator the host probably does not have, so the build refuses unless you pass
  `--allow-cross`. See [Cross-building](#cross-building).
- A **USB stick of 16 GB or more**. The stick stays with the box permanently.
- An internal disk of **at least 250 GB** — the container images alone are around 60 GB.
- Secure Boot **disabled** in the box's firmware, otherwise it will not boot the stick.

On the EVO-X2 specifically, check two more firmware settings before installing:

- **The UMA / VRAM split.** The Ryzen AI Max+ 395 carves its LPDDR5X between CPU and iGPU in firmware. Linux
  only ever sees what is left, and that is what Loom sizes minikube from — so a generous VRAM split silently
  shrinks the box. Loom runs CPU-only here, so keep the split small.
- **Disable the radios** in the AMI BIOS, for the same reason the threat model gives above.

## Building a stick

```bash
build-appliance-image --platform evo-x2 --tag 1.4.0 --flash /dev/sdX --key-backup ~/loom-key-boxA.bin
```

Without `--flash` it only produces the image, under `.appliance-build/`. The options:

| Option | Meaning |
| --- | --- |
| `--platform PLATFORM` | Which box: `spark` or `evo-x2`. Defaults to `spark`. |
| `--tag TAG` | Loom release to embed. Defaults to the newest tag, with a confirmation prompt. |
| `--flash DEVICE` | Write the image to `DEVICE` and provision its key partition. Destroys everything on it. |
| `--key-backup FILE` | Also write the LUKS key to `FILE`, mode 0400. Store it away from the box. |
| `--subnet A.B.C` | Pin the appliance subnet. Defaults to a random `10.x.y`. |
| `--interface NAME` | Pin the appliance NIC by kernel name instead of letting the platform match it. It is renamed to `loom0` either way — see [The appliance network interface](#the-appliance-network-interface). |
| `--system SYSTEM` | Override the nix system. Normally the platform decides; a mismatch is refused. |
| `--allow-cross` | Build for an architecture other than the host's. |
| `--minikube-ip IP` | Address `*.loom` resolves to on the box. Defaults to `192.168.49.2`. |
| `--nixpkgs PATH` | nixpkgs source. Defaults to `$LOOM_NIXPKGS`, which devenv sets. |
| `--output DIR` | Where to put the image. Defaults to `.appliance-build/`. |
| `--skip-STEP` | Skip a build step, by name. |
| `--yes` | Skip confirmation prompts. |
| `--verbose` | Trace every command. |

The tag matters: the appliance runs Loom in offline mode, which refuses to start unless the checkout sits on an
exact tag. The build embeds a clean clone at that tag, with git-lfs payloads materialised, and verifies all of
that before producing an image.

Each stick gets a **random `10.<a>.<b>.0/24` subnet**. That keeps two boxes on one wire from colliding, and
keeps the box from clashing with a visitor's own network. The chosen subnet is printed at the end of the build
and shown on every console login.

### Cross-building

The build refuses to produce an image for an architecture other than the host's unless you pass
`--allow-cross`, because without an emulator registered it would fail deep inside the build rather than at the
start. On NixOS, register one with:

```nix
boot.binfmt.emulatedSystems = [ "aarch64-linux" ];
```

It is less painful than it sounds. Almost the whole closure comes prebuilt from `cache.nixos.org` for both
architectures — an aarch64 build on an x86_64 host fetches roughly 774 MiB and compiles nothing, leaving only
config generation and the image assembly to run under emulation. Native is still faster, and is what the
default enforces.

### The appliance network interface

The appliance never refers to a NIC by its kernel-assigned name. Predictable naming would call it
`enp1s0f0np0` on one box and something else on the next, and a single image cannot know which — while a wrong
guess produces a box with a static address on an interface that does not exist, no DHCP, no DNS, and no sshd
to fix it from.

Instead each platform declares a `[Match]` rule, udev renames whatever matches to **`loom0`**, and the address,
the dnsmasq binding and the console banner all pin to that name. If nothing matches, a `loom-network-check`
service says so on the console at every boot and lists the interfaces that do exist.

The EVO-X2 has two ethernet ports and both are Realtek, so the match cannot single one out: whichever udev
processes first becomes `loom0`, and the other keeps its kernel name. If the box comes up unreachable, try the
other port. To pin a specific one, read its stable path off the box and rebuild with `--interface`:

```bash
udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
```

## Installing

1. Plug the stick into the box and boot from it.
2. The installer menu appears on the console — and on serial too, on a box that has a serial port. It shows
    which disk is the boot medium (never touched) and which is the install target.
3. Choose **Install**. If the box has **more than one internal disk**, as the EVO-X2's two M.2 slots allow, it
    lists them all and asks which one — rather than silently picking the first. It then names the disk it is
    about to destroy and asks for the word `INSTALL`, which is not something typed by accident.
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
every disk that will be destroyed, and the one that will not, and asks for the words `ERASE ALL DATA`.

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

**GPU support is not implemented on either platform** — the appliance ships CPU-only, and `--gpu` refuses to
run. The reasons differ, and neither is about the appliance itself.

**On the DGX Spark**, mainline Linux boots but is reported to lose both the GPU and the ConnectX-7 networking,
which NVIDIA provides through their own kernel fork. Since the appliance's DHCP and DNS depend on that
interface, this needs validating on real hardware before the driver module is written. The first thing to try
is booting a stock NixOS aarch64 image on a Spark and checking whether the ethernet port comes up.

**On the EVO-X2**, the kernel side is the easy half — `amdgpu` is mainline and already loads, which is what
puts the installer menu on the monitor. The blocker is above it: `up.sh` has no AMD path at all. It advertises
`--gpus amd`, but requires `nvidia-smi` whenever `--gpus` is set, and `charts/values-gpu.yaml` asks for
`nvidia.com/gpu`. Enabling AMD is tracked as issue #284 and is a change to Loom proper, not to the appliance.

The appliance-side plumbing (`enableGpu`, and the `--gpus all` that run mode would pass to `up.sh`) is already
in place; what is missing is a NixOS module carrying the driver, and — on AMD — the Loom-side support to point
it at.

## Troubleshooting

**The box boots into the installer every time.** The firmware is preferring the stick's removable-media path.
Re-run the install, or set the internal disk first in the firmware boot order.

**The box will not boot and asks for a passphrase.** The stick is missing, in a different port, or its key
partition is empty. Enter the recovery passphrase, then check the stick — the installer menu's status screen
reports whether a key is present.

**The console says `loom0 does not exist`.** The platform's interface match selected nothing, so the box has no
address and serves no DHCP or DNS. The same message lists the interfaces that are present; rebuild the stick
with `--interface <one of them>`. On the EVO-X2, first just try the other ethernet port.

**`loom-up` refuses to start, complaining about the minikube address.** The `*.loom` names are pinned to
`192.168.49.2` in `/etc/hosts` and minikube came up somewhere else. `minikube delete` and retry.

**Loom does not come up after a reboot in run mode.** Check `journalctl -u loom`. If the image store was never
populated, boot into Setup mode first.
