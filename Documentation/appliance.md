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
- **The stick has to stay plugged in.** A running box is watched: remove the key and it powers itself off
  ten seconds later. See [The USB key guard](#the-usb-key-guard).
- **Box and stick together are not protected.** If both are seized at once, the encryption buys you nothing.
  The design assumes the stick is removed, or travels separately, whenever the box is unattended.
- **Lose the stick and the data is gone**, unless somebody wrote down the recovery passphrase that the
  installer prints and that the console shows on its login screen at every boot. Use `--key-backup` if you
  want a second copy.
- **There is no remote access.** No sshd, no accounts but the local operator. The console is the only way in —
  and it is not an authentication boundary: it shows the banner, waits for a keypress, and then opens a
  root-capable session with no password. Neither box is driven over a serial cable, and neither image
  configures one, so the monitor and keyboard are the whole attack surface.
  **The one exception is an image built with `--debug`**, which runs an SSH server keyed to a keypair the
  build generates — see [Debug images](#debug-images). Such an image announces itself in red on its own login
  screen and is not something to hand to anybody.
- **The console runs an AI agent that can act on the box.** The bottom pane is `opencode` wired to the
  cluster's own Ollama — it reads and writes files and runs commands as `loom`, which is in `wheel` and
  `docker`. It talks to nothing outside the box, so this adds no network exposure; what it adds is a way for
  anyone already at the keyboard to act through natural language instead of a shell. Given the bullet above,
  that is not a new boundary being crossed — but it is one more reason the box must not be left unattended
  with the stick in it. **Only on `evo-x2`**: the pane needs Ollama, and Ollama needs a GPU, so the other two
  images ship neither it nor `opencode` — see [AI services follow the GPU](#ai-services-follow-the-gpu).
- **Any USB medium plugged in is mounted and indexed.** Every image does this — see
  [Ingesting data from USB](#ingesting-data-from-usb). A USB port is therefore an unauthenticated
  data-injection path: anyone who can reach the box can put arbitrary content into the index, and kernel
  and FUSE filesystem drivers parse structures that whoever plugged it in controls. Media is mounted
  read-only and never executed, and the LUKS key stick is positively excluded — but the parsing itself is
  the exposure. Given that the console is already a passwordless root session, this crosses no boundary
  that physical access did not already cross; it does make an unattended box a worse proposition than
  before.
- **Booting the stick installs the box.** The installer no longer waits to be told to; it counts down for
  60 seconds and then provisions the internal disks by itself, because provisioning is the only reason
  the stick exists. Pressing any key during that countdown puts you in the menu instead. Two things keep
  this from eating a working box: it refuses when the disks already hold a Loom pool that _this_ stick's
  key unlocks, and it refuses a second attempt in the same boot. Neither covers a stick pointed at
  somebody else's hardware — treat a Loom stick as a device that erases whatever it is booted on.
- **Bluetooth is disabled** by module blacklist and `rfkill`, in every image. **WiFi is disabled the same way
  unless the image was built with `--wifi`**, which turns the box into an access point — read
  [The WiFi access point](#the-wifi-access-point) before using it, because it changes most of the bullets
  above. Either way this is a software guarantee; disable the radios in the box's own firmware as well if the
  site requires it.

## Supported platforms

Three boxes are supported. Pick one with `--platform`; it decides the architecture and everything else that
differs between them.

| | `spark` (default) | `evo-x2` | `nuc12` |
| --- | --- | --- | --- |
| Box | NVIDIA DGX Spark | GMKtec EVO-X2 (AMD Ryzen AI Max+ 395) | Intel NUC 12 Pro (Wall Street Canyon) |
| Architecture | `aarch64-linux` | `x86_64-linux` | `x86_64-linux` |
| Build host | aarch64 — a Spark can build sticks for its siblings | any ordinary x86_64 machine | any ordinary x86_64 machine |
| Console | monitor and USB keyboard | monitor and USB keyboard | monitor and USB keyboard |
| Network | ConnectX-7, expected to present four `mlx5` ports, plus a 10GbE RJ45 — see below | 2.5GbE, two ports | 2.5GbE, one port (`igc`) |
| WiFi (`--wifi`) | untested | untested | untested — AX211, AP mode unverified |
| GPU | **GB10 Blackwell via CUDA** — not yet confirmed on hardware, see below | **Radeon 8060S via ROCm** | not supported (see below) |
| AI services | yes | yes | **no** — no GPU, and not the memory either |
| Autoscaling | yes | yes | **no** — see below |
| Before installing | update firmware from DGX OS, Secure Boot off — see [What you need](#what-you-need) | UMA split, radios off — see [What you need](#what-you-need) | — |

`nuc12` covers both Wall Street Canyon chassis, the slim NUC12WSK and the tall NUC12WSH — same board, same
NIC. A WSH fitted with the second-LAN expansion has two `igc` ports, and then the match cannot single one
out: whichever udev processes first becomes `loom0`, exactly as on the EVO-X2's pair. If the box comes up
unreachable, try the other port.

### AI services follow the GPU

Only a platform with a working GPU ships Ollama and open-webui. This is a rule, not a coincidence per box:
the models in the image are sized for offload, and the embedding step runs over _every_ indexed file. On a
CPU that does not slow the pipeline down, it stops it — an indexing run that should take an afternoon takes
days and the queue never drains. A box that shipped them anyway would look like it was working.

So `gpuVendor` in `nixos/platforms/<id>.nix` decides, and today only the EVO-X2 declares one. The other two
pass `--disable-ai` to `up.sh`, which stops both services being deployed **and** stops the indexing pipeline
calling them. Gone: summaries, translation, image descriptions, auto-tagging, embeddings, and with them
semantic search and RAG. Kept: full-text search, OCR, metadata extraction and archive import. The console
session also drops its assistant pane, because that pane is an `opencode` pointed at the cluster's own Ollama
and would have nothing to talk to.

It is stated on the login banner, so a box without AI is never a silent surprise. A platform can override the
rule — a CPU-only box somebody has measured and is happy with sets `runsAiServices = true` — but nobody has.

### Two of the three boxes autoscale

The Spark and the EVO-X2 pass `--scaling` to `up.sh`, which installs KEDA and applies
[`charts/values-scaling.yaml`](../charts/values-scaling.yaml): the worker and the reaper follow the depth of
their RabbitMQ queues (up to ten replicas each), Tika and Gotenberg follow CPU. Without it every service sits
at the one replica the chart declares, and an indexing run on a twenty-core box uses a fraction of it.

Nothing is fetched for this. KEDA's chart is vendored in `keda/` and its two images are pulled during
first-time setup like every other image — which is _why_ the flag is set in both boot modes rather than only
in the one that runs Loom. A stick whose setup ran without `--scaling` has no KEDA images on it, and run mode
is air-gapped by then.

One node is still one node. The quota in that values file is written for a small cluster and never binds
here; what binds is the scheduler. At full stretch the worker and reaper replicas ask for about 10 more cores
and 27 GiB more memory than the single-replica stack does, which both boxes have — but a pod that does not
fit stays `Pending` until the load drops, and the readiness bar on the console counts it while it waits. A
bar that dips during a heavy indexing run and recovers afterwards is that, not a fault.

Two things are deliberately not scaled:

- **Ollama.** `values-scaling.yaml` gives it an HPA, written for a cluster with more than one GPU node. On
  the EVO-X2 the pod requests `amd.com/gpu: 1` and the box advertises exactly one, so a second replica could
  never be scheduled — it would sit `Pending` for as long as the HPA wanted it, and the readiness bar on the
  console counts it as a workload that has not come up. The appliance therefore writes
  `ollama.hpa.enabled: false` into `charts/values-overwrites.yaml` when it seeds the checkout. That file is
  Skaffold's last word on values, so it wins over the flag; a header in it says who wrote it, and an
  operator's later edits stay.
- **The NUC 12**, which cannot have the flag at all — below.

### The NUC 12 runs a reduced Loom

These kits ship with one SO-DIMM, and the iGPU takes its share before Linux sees the rest — around 15 GiB
usable, against a documented minimum of 25 GiB. The platform therefore declares two facts about itself, in
`nixos/platforms/nuc12.nix`, and the image is built around them:

- **`runsAiServices = false`** → the appliance passes `--disable-ai`, as described above. Written out rather
  than left to the GPU rule, because memory is an independent reason for it: fit the second SO-DIMM and an
  Iris Xe still cannot run the models.
- **`meetsResourceMinimum = false`** → the appliance passes `--no-resources`. This is not merely about
  getting past `check_host_resources`: even without the AI services the chart asks for about 19.4 GiB of
  memory **requests**, so a box with ~12 GiB allocatable would clear the check and then leave most of its
  pods `Pending` forever. `--no-resources` strips requests and limits, and skips the host check on the way
  past. It also rules out `--scaling`: `up.sh` rejects the two together, because the scaling values file
  turns on a resource quota that requires requests on every pod and this flag is what removes them. So
  `runsAutoscaling` follows `meetsResourceMinimum`, and this box stays at one replica per service.

Both are stated on the login banner, so a box running below spec is never a silent surprise.

**What to expect.** Usable rather than comfortable. With no limits, nothing stops one container starving the
others, and a heavy indexing run on this much memory ends in OOM kills rather than orderly eviction. Fitting
the second SO-DIMM — the board takes 64 GB — clears the resource half and `meetsResourceMinimum` can go. The
AI half stays: there is no GPU here for it either way.

Everything else — the LUKS-key-on-stick scheme, the two boot modes, the installer and the wipe — is identical.

A box that is **not** one of these will still come up: see
[The appliance network interface](#the-appliance-network-interface) for what happens when no platform
matches its NIC.

## What you need

- One of the boxes above.
- A **build host of the same architecture**. The image carries a whole NixOS closure for the appliance, and
  cross-building needs an emulator the host probably does not have, so the build refuses unless you pass
  `--allow-cross`. See [Cross-building](#cross-building).
- A **USB stick of 16 GB or more**. The stick stays with the box permanently.
- Internal disks totalling **at least 250 GB** — the container images alone are around 60 GB. Every
  eligible internal NVMe is pooled into one volume, so a box with two M.2 slots may reach that with two
  smaller drives. See [How the disks are used](#how-the-disks-are-used).
- Secure Boot **disabled** in the box's firmware, otherwise it will not boot the stick.
- **Free disk on the build host.** One image is a whole appliance closure plus a ~1.5 GB squashfs, so
  budget around 20 GB for a build and more if you build several tags. Nix frees none of it by
  itself — `nixos/README.md` has the settings that make it, which matter more if you also run the VM
  tests.

On the EVO-X2 specifically, check two more firmware settings before installing:

- **The UMA / VRAM split — set it to the _lowest_ value the firmware offers.** This is counterintuitive
  enough to be worth the paragraph. The Ryzen AI Max+ 395 carves a fixed slice of its LPDDR5X off for the
  iGPU in firmware, and Linux never sees that slice: it is subtracted from the host whether the GPU uses it
  or not. It is also _not_ where the iGPU's working memory comes from. That comes from GTT — ordinary
  system memory the GPU pins on demand — and the image sets its ceiling at 64 GiB
  (`nixos/platforms/evo-x2.nix`). So a large carve-out starves both ends at once: it takes memory away from
  minikube _and_ caps nothing useful for Ollama. Pick the minimum on offer; on EVO-X2 BIOS 1.12 that is
  2 GB, and the ~1.5 GB of GTT headroom it costs is not worth hunting for.

  This follows published measurement on this board rather than on our own unit. Confirm it after
  installing with `loom-platform-info`, which prints the firmware carve-out and the GTT ceiling side by
  side.
- **Disable the radios** in the AMI BIOS, for the same reason the threat model gives above.

On the DGX Spark specifically, there is one step that has to happen **before** the box is disconnected
from the internet, and it cannot be undone later:

- **Update the firmware from DGX OS, while the box still has a network.** A factory-fresh Spark ships with
  firmware only DGX OS can boot from — NixOS will not come up on it at all, and the appliance stick will
  look dead rather than unsupported. NVIDIA publishes Spark firmware to the Linux Vendor Firmware Service,
  so from the DGX OS the box arrived with:

  ```bash
  fwupdmgr refresh
  fwupdmgr get-updates
  fwupdmgr update
  ```

  This is the one prerequisite that needs the box online. An air-gapped Spark that was never updated has to
  be put back on a network to get past it.
- **Secure Boot off**, as for every platform, but worth checking twice here: it is on by default on this
  box.

`loom-platform-info` reports both — the firmware version with any pending update, and the Secure Boot and
Setup Mode flags read straight out of the EFI variables. It is plain bash with no Nix dependency precisely
so it can be run on the Spark **while it is still running DGX OS**, before a stick is ever built:

```bash
./nixos/scripts/platform_info.sh
```

## Building a stick

```bash
build-appliance-image --platform evo-x2 --tag 1.4.0 --flash /dev/sdX --key-backup ~/loom-key-boxA.bin
```

Without `--flash` it only produces the image, under `.appliance-build/`. The options:

| Option | Meaning |
| --- | --- |
| `--platform PLATFORM` | Which box: `spark`, `evo-x2` or `nuc12`. Defaults to `spark`. |
| `--tag TAG` | Loom release to embed. Must exist in this checkout — the image is built from a clone of it, not from the remote. Defaults to the newest tag, with a confirmation prompt; see [Which tag gets picked](#which-tag-gets-picked). |
| `--flash DEVICE` | Write the image to `DEVICE` and provision its key partition. Destroys everything on it. |
| `--key-backup FILE` | Also write the LUKS key to `FILE`, mode 0400. Store it away from the box. |
| `--subnet A.B.C` | Pin the appliance subnet. Defaults to a random `10.x.y`. |
| `--no-gpu` | Build CPU-only for a platform that offloads to a GPU — `spark` or `evo-x2`. There is no `--gpu`: the GPU is a property of the box. On the Spark this drops the offload but keeps the NVIDIA driver, which also runs that box's console. See [GPU support](#gpu-support) for when you need this. |
| `--interface NAME` | Pin the appliance NIC by the name the box reports (`enp2s0`), instead of letting the platform match it. Renamed to `loom0` either way. Rarely needed — an unmatched box claims a wired port on its own; see [The appliance network interface](#the-appliance-network-interface). |
| `--wifi` | Also run an access point, bridged onto the wired port. Radios are disabled without it. Read [The WiFi access point](#the-wifi-access-point) first. |
| `--wifi-ssid SSID` | Network name. Defaults to a generated `loom-xxxx`. |
| `--wifi-psk PSK` | WPA passphrase. Defaults to a generated one. Letters, digits, `-` and `_` only. |
| `--wifi-country CC` | ISO country code. Moves the AP to 5GHz; without it the AP stays on 2.4GHz. |
| `--wifi-interface NAME` | Pin the radio by its **kernel** name (`wlan0`), not the predictable one — unlike `--interface`, this is still a `.link` match and carries the limitation described under [Pinning a port](#pinning-a-port). Rarely needed: the default claims any radio. Renamed to `loomwl0` either way. |
| `--debug` | Run an SSH server on the box, keyed to a keypair generated for this image. Takes back the "no remote access" guarantee. Read [Debug images](#debug-images) before using it. |
| `--system SYSTEM` | Override the nix system. Normally the platform decides; a mismatch is refused. |
| `--allow-cross` | Build for an architecture other than the host's. |
| `--minikube-ip IP` | Address `*.loom` resolves to on the box. Defaults to `192.168.49.2`. |
| `--nixpkgs PATH` | nixpkgs source. Required — `build-appliance-image` passes devenv's pinned nixpkgs for you, so you only need this when driving the script directly. |
| `--nixos-hardware PATH` | [nixos-hardware](https://github.com/NixOS/nixos-hardware) source, which the x86 platforms take their hardware profile from. Required, and passed for you the same way. |
| `--output DIR` | Where to put the image. Defaults to `.appliance-build/`. |
| `--skip-STEP` | Skip a build step, by name — `--help` lists them in the order they run. A debugging escape hatch: later steps assume the earlier ones ran, so a stick built with one of these is not a stick anybody should ship. `--skip-validate_environment` is the one with a legitimate use, when the preflight's 20 GB store estimate is wrong for your host. |
| `--yes` | Skip confirmation prompts. |
| `--verbose` | Trace every command. |

The tag matters: the appliance runs Loom in offline mode, which refuses to start unless the checkout sits on an
exact tag. The build embeds a clean clone at that tag, with git-lfs payloads materialised, and verifies all of
that before producing an image.

That clone carries **exactly one ref**, the shipped tag. Branches, other tags, the remote and the git-lfs
objects no longer reachable from it are all stripped, so `git log --all` on the box shows the release and
nothing about the machine that built it. It is also what makes two builds of one tag produce the same image:
with the build host's branch tips left in, the embedded pack differed per machine and per day, and every build
added another ~1.5 GB image to the builder's Nix store for a release that had not changed.

Each stick gets a **random `10.<a>.<b>.0/24` subnet**. That keeps two boxes on one wire from colliding, and
keeps the box from clashing with a visitor's own network. The chosen subnet is printed at the end of the build
and shown on the console's login screen.

### Which tag gets picked

Without `--tag`, the build takes the newest tag in your checkout and asks you to confirm it. Two things make
that answer trustworthy:

- **It fetches first.** The local tag list is otherwise only as fresh as your last `git fetch`, and a stale
  pick costs an hour of build and yields a stick indistinguishable from the right one until somebody boots it.
  The fetch is best-effort: no `origin`, or no route to it, warns and carries on with the tags you have, since
  building on a disconnected host is supported. `--skip-fetch_tags` turns it off.
- **A release outranks its own release candidates.** Git's version sort would otherwise put `1.3.0-rc10` above
  `1.3.0`, because a longer string sorts above the prefix it extends — so the default would never pick a
  finished release at all. The build sets `versionsort.suffix=-rc` to correct that, which covers this
  repository's two tag shapes, `X.Y.Z` and `X.Y.Z-rcN`.

`--tag` skips both: it names the release outright, and the tag has to be in this checkout already, because the
image is built from a clone of it rather than from the remote. If it is not, fetch and try again.

### Trying a stick without a box

You do not need appliance hardware — or a stick — to see what one does. `appliance-vm installer`
flashes the image onto a file and boots it under UEFI against emulated NVMe, so the real installer
runs against a real pool, reboots into what it installed, and unlocks it from the key partition the
same way a box would. `appliance-vm box` is the quicker half: the appliance closure booted directly,
which gives you the console session and the branding in about a minute, but nothing below the disk.

Both keep their disks between runs, so an installed VM is still installed tomorrow. The mechanics —
what each one can and cannot show, why the rig can boot an image the test suite cannot, and what
`--serial` costs — are in [../nixos/README.md](../nixos/README.md).

### Cross-building

The build refuses to produce an image for an architecture other than the host's unless you pass
`--allow-cross`, because without an emulator registered it would fail deep inside the build rather than at the
start. On NixOS, register one with:

```nix
boot.binfmt.emulatedSystems = [ "aarch64-linux" ];
```

It is less painful than it sounds. Almost the whole closure comes prebuilt from `cache.nixos.org` for both
architectures — an aarch64 build on an x86_64 host fetches roughly 774 MiB and compiles nothing, leaving only
config generation to run under emulation. Native is still faster, and is what the default enforces.

The final image assembly deliberately does _not_ run under emulation. `nixos/modules/image/repart-image.nix`
invokes `unshare --map-root-user fakeroot systemd-repart`, and `unshare(CLONE_NEWUSER)` fails with `EINVAL`
inside qemu-user: the kernel only unshares a user namespace for a single-threaded process, and qemu-user never
is one. `nativeImageAssembly` in `nixos/default.nix` therefore swaps that derivation's `nativeBuildInputs` for
host binaries whenever `system` differs from the build host. Nothing about the assembly is
architecture-specific — repart copies opaque bytes, and the partition types this image uses (`esp`,
`linux-generic`) carry no architecture — so the resulting stick is byte-for-byte an aarch64 image either way.

### The appliance network interface

The appliance never refers to a NIC by its kernel-assigned name. Predictable naming would call it
`enp1s0f0np0` on one box and something else on the next, and a single image cannot know which — while a wrong
guess produces a box with a static address on an interface that does not exist, no DHCP, no DNS, and no sshd
to fix it from.

Instead each platform declares a `[Match]` rule, udev renames whatever matches to **`loom0`**, and the address,
the dnsmasq binding and the console banner all pin to that name.

The EVO-X2 has two ethernet ports and both are Realtek, so the match cannot single one out: whichever udev
processes first becomes `loom0`, and the other keeps its kernel name. If the box comes up unreachable, try the
other port.

#### When no platform matches

An image installed on hardware none of the platforms covers would otherwise rename nothing, and a box with no
`loom0` has no address, no DHCP and no `*.loom` — unrecoverable at the console, because there is no sshd and
no `nixos-rebuild`. So when the match selects nothing, `loom-interface-fallback` claims a wired port itself,
before any address or bridge unit runs:

| Wired ports found | What happens |
| --- | --- |
| 0 | Nothing is renamed. The console names every interface it did find. |
| 1 | It becomes `loom0`. No ambiguity, nothing to warn about beyond saying so. |
| 2 or more | The one with the lowest PCI path becomes `loom0`; the console names the others. |

"Wired" excludes anything the kernel gives a `DEVTYPE` — radios, WWAN modems, bridges, veth — as well as
virtual interfaces with no backing device. A cellular modem is the awkward one: it looks like an ordinary
ethernet card apart from that `DEVTYPE=wwan`, and serving DHCP down a mobile connection is not a mistake worth
making.

Picking rather than refusing is deliberate. A box that came up on the wrong port of a multi-port machine is
fixed by moving the cable; a box with no `loom0` at all needs a new stick.

`loom-wired-nics` prints the candidate list, in order, on the box itself.

#### Pinning a port

`--interface NAME` takes the name as the box reports it — `enp2s0`, not `eth0`. It is applied at runtime by
the same service, for a reason worth knowing if you are reading the generated `.link` file and wondering: a
`[Match] OriginalName=` clause matches the name udev sees _while_ it is deciding, which is the kernel's
`eth0`. The predictable name is the _output_ of that decision, so matching on it there can never work.

```bash
udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
```

The driver is what a new platform should match on; the name is what `--interface` wants.

### The WiFi access point

Off by default. `--wifi` builds an image whose installed appliance also runs an access point on the box's own
radio, **bridged onto the wired port**, so it does not matter how a visitor arrives: the same DHCP pool, the
same resolver, the same `https://frontend.loom`, whether they joined over the air or plugged a cable in.

```bash
build-appliance-image --platform evo-x2 --tag 1.4.0 --wifi --flash /dev/sdX
```

The SSID and passphrase are generated at build time and printed at the end of the build. The box's login
screen shows them too, along with a QR code — point a phone camera at the monitor and it offers to join,
the same way Android and iOS "share this network" works.

#### Read this before using it

The rest of this document describes a box that is an island. `--wifi` is the one option that changes that, and
it changes it a lot:

- **The passphrase is the only thing protecting the data.** Loom has no user management and its frontend is
  not an authentication boundary. Anyone who joins the network has everything the box has indexed. With a
  cable that meant "anyone who can physically reach the box"; with a radio it means anyone in range, through
  the wall, in the car park.
- **The passphrase is on the screen.** Anyone at the monitor can read it or scan it. That is not a new leak —
  the console already opens a root-capable session on the next keypress — but it does mean the monitor now
  hands out network access, not just local access.
- **The credentials are on the stick.** They are baked into the image, so they are in `/nix/store`
  world-readable and readable from the stick itself. Two boxes installed from one stick share a network.
  Build a stick per box if that matters.
- **Never cable a `--wifi` box into a network you do not own.** The radio and the wired port are one bridge,
  so doing that makes the box an unauthenticated door onto that LAN. The box already refuses to act as a DHCP
  server anywhere but its own link; bridging is not something it can refuse for you.
- **It is slower.** 2.4GHz gives roughly 50–100 Mbit/s against 2.5GbE or ConnectX-7 on the wire. Addressing
  and DNS are identical either way; throughput is not. Bulk ingest belongs on the cable.

#### Bands and the country code

The AP runs on **2.4GHz channel 6** unless you pass `--wifi-country`. That is not a conservative default that
5GHz could be talked out of. With no country code, Linux uses regulatory domain `00`, in which every 5GHz
sub-band is flagged `NO-IR` — _No Initiating Radiation_ — which allows joining a network someone else started
but forbids beaconing, so hostapd cannot bring an AP up at all. Confirm on any box with `iw reg get`.

Passing `--wifi-country CH` sets the regulatory domain and moves the AP to **channel 36**, the bottom of
UNII-1, which is non-DFS wherever it is allocated — so the AP never waits out a radar availability check. Set
it to where the box actually is.

Note that many MediaTek and Intel radios are _self-managed regdomain_: the allocation is enforced in firmware
and `--wifi-country` will not widen it.

#### If the access point does not come up

AP mode is not something every radio supports, and the failure is quiet: hostapd is bound to the radio's
device unit, so a missing card or an unsupported mode simply leaves it inactive. The box says so on the login
screen rather than leaving you to guess — a warning appears above the credentials, and the wired port keeps
working throughout. On the box:

```bash
iw list | grep -A15 'Supported interface modes'   # needs a line reading '* AP'
journalctl -u hostapd
journalctl -u loom-wifi-check
```

If the radio is there but the platform's match did not select it, rebuild with
`--wifi-interface <kernel name>`. It is renamed to `loomwl0` either way, and the bridge is `loombr0`.

## Debug images

```bash
build-appliance-image --platform evo-x2 --debug
```

A **debug image** is an ordinary appliance that also runs an SSH server. It exists for the box that misbehaves
in a way the console cannot answer — where everything has to be read off a monitor and typed back in — and
for pointing an AI agent at such a box. It is the only build where `services.openssh.enable` is true.

### Read this before building one

`--debug` takes back the first line of the [threat model](#threat-model). Specifically:

- **The generated key is root on the box.** It logs in as the operator account, which is in `wheel` with
  passwordless `sudo`, because up.sh needs that. There is nothing behind it: Loom has no user management and
  its frontend is not an authentication boundary.
- **Port 22 is open on the whole appliance segment** — and on the WiFi bridge too, if the image was also
  built with `--wifi`. Anyone who can plug a cable in can reach the port; only the key stops them.
- **The image is not what a real stick is.** It boots without the splash so failures are readable, and its
  [USB key guard](#the-usb-key-guard) only warns instead of powering the box off, so that a glitching port
  on a bench does not take the session down. Do not use one to judge how a shipped stick behaves.
- **Never hand one to anybody.** Wipe the box when you are done, and delete the key directory.

The box makes this hard to forget. It says `DEBUG IMAGE — NEVER USE THIS IN PRODUCTION` in white on red at
the bottom of its login screen, the message of the day repeats it, the console session's status line carries
`DEBUG — SSH OPEN`, and the image file itself is named `loom-installer-debug_*.raw`. The boot menu carries it
too, on the entry's second line — `debug-<version>` rather than the plain version — for the box that never
gets as far as a login screen; the title itself still reads `Loom`, exactly as it does for the
`first-time-setup` entry.

`--debug` is refused outright when `$CI` is set: a pipeline would publish a remotely accessible artifact and
throw the only key to it away with the runner.

### Getting in

The build generates a fresh ed25519 keypair per image, keeps the private half out of the Nix store entirely,
and leaves it in a temp directory it prints at the end:

```text
[*] Debug access. The key that opens this image:
      key dir   : /tmp/loom-appliance-debug-1.4.0-evo-x2.N35LEv
      on the box: ssh -F /tmp/loom-appliance-debug-1.4.0-evo-x2.N35LEv/ssh_config loom-appliance
```

That directory holds `id_ed25519`, its `.pub`, a `known_hosts`, and two ready-made `ssh_config` files — one
for the box on its own network, one for the same image under `appliance-vm box --debug`. Use them rather than
assembling flags: each stick gets a [random subnet](#building-a-stick), so the box's address is not knowable
in advance, and the config carries it along with `IdentitiesOnly` and an `accept-new` host-key policy that
needs no interaction. That last part is what makes the directory usable by an agent as well as a person.

The directory survives the build on purpose — it is the whole output of the flag — and nothing ever deletes
it for you.

### Collecting everything at once

The debug image carries `loom-debug-bundle`, which tars up both boots' journals, the failed units,
`loom-service` status, `loom-platform-info`, the login screen, the network configuration, and the cluster's
pods, events and logs, then prints the path:

```bash
ssh -F <key dir>/ssh_config loom-appliance loom-debug-bundle
scp -F <key dir>/ssh_config loom-appliance:/tmp/loom-debug-*.tar.gz .
```

Every collector in it is allowed to fail. The most likely thing to be debugging is a box whose cluster never
came up, and a bundle that aborted on the first `kubectl` timeout would carry none of the journal that
explains why — so a section that could not be read is an empty file rather than a missing bundle.

### Without a box

`appliance-vm box --debug` is the cheap way to use any of this: about a minute, no tag, no image build, and
it forwards `localhost:2222` to the guest's sshd. Its keypair lives in the VM's state directory rather than
in `/tmp`, so it is the same key across runs — and `appliance-vm reset` deletes it with the disks.

It does not reach the installer. That half is driven with `appliance-vm installer --serial`; see
[Trying a stick without a box](#trying-a-stick-without-a-box).

## Installing

**Plug the stick in, boot from it, and leave it alone.** Nothing has to be typed. What follows is what
happens on its own, and where you can still interrupt it.

1. Plug the stick into the box and boot from it. Have the box on **a network with internet** already — the
    boot after this one fetches every container image.
2. The installer appears on the console. Its header names the **Loom release and the platform the stick was
    built for**, so check there that you booted the right stick; two sticks are otherwise indistinguishable.
    Below that it shows which disk is the boot medium (never touched), whether the stick's LUKS key is
    present, and every disk that will be pooled and erased.
3. It counts down for **60 seconds** and then installs. **Press any key to stop it** and get the menu, where
    Install still asks for the word `INSTALL` and nothing happens unattended. The countdown does not start
    at all when something is wrong — the console says which, and waits:

    | It says | Meaning |
    | --- | --- |
    | `this stick already installed this box` | The disks hold a Loom pool this stick's key opens. Refusing is the point: a firmware that re-scans removable media would otherwise reinstall over the indexed data. Choose Install from the menu to do it anyway. |
    | `an install was already attempted this boot` | Reboot to try again. |
    | `the boot medium is ambiguous` | A second Loom stick is plugged in. Remove it. |
    | `the stick carries no LUKS key` | Re-flash with `build-appliance-image --flash`. |
    | `there is no eligible internal disk` | Nothing to install onto. |
    | `the disks are too small` | Under 250 GB across all of them. |

4. It partitions every eligible internal disk, pools them into one volume, creates the LUKS container from
    the stick's key, installs the appliance closure entirely offline, enrols a recovery passphrase, makes the
    internal disk the default boot entry, and selects **first-time setup** as the entry that disk boots.
    Copying the closure is the long step — tens of gigabytes — and gets a progress bar with the copy's own
    output scrolling above it, so a slow disk and a stuck install look different from across the room.
5. **Write down the recovery passphrase it prints**, if you are there. It holds the screen for 30 seconds and
    then reboots on its own, so an install nobody comes back to still finishes. Nothing is lost if you miss
    it: the installed box shows the same passphrase on every console login.
6. The box boots into the internal disk and straight into first-time setup — no entry to pick. Leave the
    stick in.

From here the only thing still asked of you is to **move the box** once setup powers it off, which the next
section explains.

The countdown is skipped in one case. If the installer could not make the internal disk the default boot
entry — no NVRAM entry, or its own loader still on the UEFI removable-media path — it says so and waits for
enter instead of rebooting itself, because that warning asks you to change the firmware boot order and it is
the one thing on that screen the installed box does not repeat. A wipe (menu option 2) likewise always waits.

The installer moves its own loader off the UEFI removable-media path afterwards. Without that, most firmware
would boot the installer instead of the appliance on every restart, because the stick never leaves. The
installer stays reachable from the firmware's own boot menu for reinstalls and wipes.

### How the disks are used

**Every eligible internal NVMe becomes one volume.** There is no disk to choose, which is what lets the
install run without asking anything:

```text
nvme0n1  1G ESP  +  the rest  ─┐
nvme1n1  the whole disk       ─┴─>  one volume  ─>  LUKS2  ─>  ext4
```

Eligible means an internal NVMe namespace that is not the boot medium, not removable, not on the USB bus and
not mounted. USB storage enumerates as `sd*` and can never qualify, so the stick you booted from is excluded
by construction as well as by name.

The disks are **concatenated, not mirrored or striped**. Concatenation uses every byte of drives that are not
the same size, where striping would cap the pool at twice the smaller one. Two consequences worth knowing:

- **There is no redundancy.** On a two-disk box, one failed drive loses the whole index — the same outcome as
  losing the stick, and for the same reason: an appliance holds the only copy. If that is not acceptable at
  your site, populate one slot.
- **The encryption is unchanged.** One container, one key on the stick, one recovery passphrase, whether the
  box has one disk or three. The volume is assembled first and encrypted on top, which is what lets a single
  appliance image serve boxes with different numbers of drives.

A wipe (menu option 2) destroys the pool's key material first and then sweeps each disk, so it reaches the
encryption regardless of how many drives were pooled.

## The two boot modes

The appliance has two boot modes, `Loom` and `Loom (first-time-setup)`. **You never pick between them.** The
installer leaves the menu on first-time setup, and the setup run hands it back to `Loom` and deletes its own
entry when it finishes — so a box that has completed setup has exactly one entry, and every box before that
has the only entry that would work anyway.

That is not tidiness. The `Loom` entry serves DHCP and wildcard `*.loom` DNS on the appliance NIC, and the
setup run happens on a network with internet — usually somebody's office LAN. Every wrong pick, and every
accidental reboot part way through a fetch that runs for hours, used to put a DHCP server on that LAN. Now a
reboot mid-fetch comes back into first-time setup and carries on.

| | Run (default) | First-time setup |
| --- | --- | --- |
| Network | Static address, serves DHCP and `*.loom` | DHCP client |
| Loom | Starts offline and exposed on the appliance network | Builds and pulls every container image |
| When | Normal operation | Once, in the lab, with internet |
| Screen | Loom splash, no boot log | Full boot log, no splash |
| Console session | First pane follows `loom` | First pane follows `loom-fetch` |
| Key removed | Powers the box off | Warns only |
| When it finishes | Keeps running | Powers the box off |

A fresh box has no container images, and pulling them needs registries. So the first boot after installation
is into **first-time setup**, which happens by itself — just make sure the box is on a network with internet
before that boot, and press a key at the console to watch: the first pane of the session is that log.

This takes a long time. It populates minikube's image store on the encrypted root and marks itself complete, so
a reboot will not repeat it.

**When it finishes, the box powers itself off** — a minute after the last log line, so an unattended run ends
with a box that is simply off. Before it goes down it promotes `Loom` back to being the boot default and
removes the first-time-setup entry, so what comes back up is a single-entry menu.

**Move the box before powering it on again.** This is the one thing still left to you: run mode serves DHCP and
wildcard `*.loom` DNS on the appliance NIC, and that must not land on the network the fetch ran over. Move it to
where it will be used, power it on there, and it runs offline forever.

If you want the box to stay up instead — to look at something before it goes down — `sudo systemctl stop
loom-fetch` on an `Alt-F2` console during that minute cancels the poweroff. The run is marked complete and the
menu is already promoted either way.

The two modes look different on purpose. `Loom` boots to a splash with no kernel log, because it has nothing to
report and the login screen carries everything an operator needs. `Loom (first-time-setup)` boots verbose — it
runs for hours, and a still logo over all of it would be misleading. Either way the real progress report is the
console session, not the boot screen.

This is also why the stick does not need to carry 60 GB of container images.

### Once setup is done, it is gone

The first-time-setup entry is **deleted**, not merely deselected, and there is no way to bring it back. That is
a deliberate trade, and it has one consequence worth knowing before you hit it: **anything that destroys the
image store costs a reinstall, and a reinstall destroys the indexed data.** See the `minikube delete` entry
under [Troubleshooting](#troubleshooting) — that command is the most likely way to get there.

`Reboot Into Firmware Interface` is untouched by any of this. systemd-boot draws that entry itself rather than
reading it off the disk, so it survives, and the 30-second menu timeout stays generous partly to keep it
reachable on boxes whose display wakes up late.

## The USB key guard

The stick is read once at boot, to unlock the disk. Without anything further, a running box would keep going
for weeks after the stick was pulled — unlocked, with no key present — and the removal would only take effect
at the next boot. So the box keeps watching the key for as long as it runs.

**Remove the key from a running box and it powers itself off ten seconds later.** The countdown is announced
on the console and in the session's status line, and putting the stick back inside those ten seconds cancels
it. It is a clean shutdown, not a yanked cord, so indexed data is not at risk — but it is not instant either,
because tearing minikube and Docker down takes as long as it takes.

What the guard checks is the key itself, not the presence of a stick: it reads the 4096 bytes and tests them
against the disk's own LUKS header. A different stick carrying a partition named `loom-key` does not keep the
box alive.

A few consequences worth knowing:

- **It arms itself, once, after a key has been seen.** A box booted with the recovery passphrase has no stick
  at all, so the guard never arms there and the box stays up for repairs. The login banner says which of the
  two states the box is in.
- **First-time setup only warns.** That mode pulls every container image over several hours, on a box that is
  still in the lab with nothing on it yet; a flaky USB port must not throw all of it away.
- **To swap sticks deliberately**, run `loom-key-guard disarm` at the console first. It stays disarmed until
  the next boot; `loom-key-guard arm` re-enables it, and `loom-key-guard status` prints the current state.

## Using Loom on the appliance

Plug a laptop into the box's ethernet port. It gets an address by DHCP, and `dnsmasq` answers for every name
under `.loom`, so this just works:

```text
https://frontend.loom
```

No hosts file, no configuration on the visitor's side. The other services — `grafana.loom`, `open-webui.loom`,
`elasticvue.loom` and the rest — resolve the same way.

The box is not a gateway and does not advertise itself as one: the lease carries an address, a netmask and a
DNS server, and deliberately no default route. So a laptop that is also on wifi keeps reaching the internet
over the wifi, and only `*.loom` comes from the box.

The one thing the laptop does take from the box is DNS, and the appliance's resolver has no upstream — it
answers under `.loom` and refuses everything else. Most systems query both links and are unaffected; one that
adopts the box as its only resolver will resolve nothing but `*.loom` until it is unplugged. Nothing on the
box can fix that, there being no internet behind it to forward to.

### Ingesting data from USB

Plug a USB stick, card reader or external drive into a running box and its contents are indexed. Nothing has
to be typed: a udev rule starts `loom-usb-ingest@<device>.service`, which mounts every volume it finds,
copies it into the `loom-intake` bucket and lets the ordinary crawler pick it up from there.
`loom-usb-status` prints the last run.

**Watch it on the console.** While a copy is running, the pod-list pane splits in half: `k9s` keeps the top,
and the bottom shows a bar per device — the volume being copied, gigabytes moved, files uploaded. When a
device is finished its row turns green and says `DONE — safe to remove`, with what the whole stick moved
beside it, and **it stays there until that stick is unplugged** — that row is the signal to pull it. Only
when the last device is out is the split undone and `k9s` given the space back. Plug a second stick in while
the first is still going and it gets a line of its own rather than a second pane.

A row that says `stopped before it finished` is a copy whose service died or was stopped with the stick
still in: nothing was pulled early, but nothing is complete either. `journalctl --unit
loom-usb-ingest@<device>` has the reason.

**A stick plugged in before Loom is up waits for it.** A box that has just been switched on spends the best
part of an hour bringing the cluster up, and media handed to it in that window is not refused: the row says
`waiting for Loom`, with what the last attempt to reach the intake bucket reported, and the copy starts by
itself once the bucket answers. An hour is also where it gives up, and then the row says how long it waited
and what it heard.

**A row that failed says why.** A red row carries the first thing that went wrong in its own words — the
storage endpoint refusing a connection, a volume skipped because the box has no driver for it, a certificate
it would not trust — rather than a count of failures on its own. A finished row can carry one too: a stick
whose second partition was skipped still says `DONE`, with the skip in brackets after it. The journal keeps
the untruncated version.

Milestones are also announced in the tmux status bar — ingest started, each volume uploaded, the box short
on disk, and every failure with its reason — and to `wall`, which reaches any console somebody has logged
into. Those lines scroll away; the pane is what persists.

Read the [threat model](#threat-model) bullet about this before deploying a box where strangers can reach a
port.

**The LUKS key stick is never touched.** It is identified by asking the key guard which device it armed on —
the one it proved unlocks this disk — rather than by partition label, which is not unique when two Loom
sticks are attached. The installer stick is excluded the same way, so its ~60 GB of container images never
land in the index. If the box was booted on the recovery passphrase the guard never arms, and the exclusion
falls back to partition labels; the console says so when that happens.

**Media is never written to.** Volumes are mounted read-only, with `nodev,nosuid,noexec`, and
`blockdev --setro` is applied underneath so the kernel refuses writes at the block layer. Journalled
filesystems get `noload` / `norecovery` / `nologreplay` as appropriate — a dirty ext4 or XFS volume mounted
with plain `-o ro` still replays its journal, which modifies the evidence.

Filesystems are handled in three tiers:

| | |
| --- | --- |
| **Refused** | LUKS, BitLocker, ZFS members, LVM physical volumes, MD RAID members, swap. Each needs a key or an assembly step, and the console says which. |
| **Known** | FAT12/16/32, exFAT, NTFS, ext2/3/4, XFS, btrfs, F2FS, HFS, HFS+, ISO9660, UDF, APFS. Explicit driver, explicit options. |
| **Best effort** | Anything else the running kernel supports is attempted with a plain read-only `mount -t auto`. |

NTFS goes through `ntfs-3g` rather than the in-kernel `ntfs3` on purpose: this box parses filesystems it was
handed by strangers, and FUSE keeps that parsing in a process that can crash without taking the kernel with
it. It is slower, and that is the trade. APFS is read-only and best effort — there is no in-kernel driver.

GPT, MBR and Apple partition maps all work, as does unpartitioned "superfloppy" media (most cameras and many
SD cards).

Everything lands under a prefix naming the stick, so it can be searched for as a unit:

```text
usb-crawled/{label-or-vendor}-{serial}/{path on the stick}
usb-crawled/{label-or-vendor}-{serial}/_loom-usb.json
```

`_loom-usb.json` is a provenance record — udev properties, the filesystems found, the mount options actually
used, file and byte counts, and the original spelling of any name that had to be sanitised. It is indexed
alongside the data, so it is searchable next to it.

A stick carrying more than one volume gets a `p1`, `p2`, … level beneath that. Re-plugging the same stick is
cheap: files already uploaded at the same size are skipped.

**Loom archives are imported, not indexed as zips.** The crawler recognises them from their content rather
than their filename, and sends them to the archive importer. An encrypted `.loom` from a _different_ box will
not decrypt — `archive_enc_master_key` is unset by default, so every deployment generates its own — and is
indexed as an opaque encrypted blob rather than being discarded.

**This costs disk twice.** Every ingested byte is stored once in the intake bucket and again in file storage
after indexing, and nothing empties intake automatically. Ingest is never refused on space grounds; the
console warns when the encrypted root is running short, and the copy continues. On a box that has filled up,
purge the intake bucket by hand.

### From the box's own console

The console shows the box's banner before anyone logs in — release, platform, which port to plug a laptop
into, the subnet it serves, how far the bring-up has got, whether the key guard is armed, and the LUKS
recovery passphrase:

<!--
The eyes are pasted from a real console, and their rows are an odd number of
columns in. editorconfig-checker wants every indent to be a multiple of two,
which no uniform shift of this art can satisfy.
-->
<!-- editorconfig-checker-disable -->

```text
   ▄████▄    ▄████▄
  ██▀  ▀██  ██▀  ▀██
  ██ ▄▄ ██  ██ ▄▄ ██
  ██▄  ▄██  ██▄  ▄██
   ▀████▀    ▀████▀

  Loom appliance -- 1.4.0
  GMKtec EVO-X2 (AMD Ryzen AI Max+ 395)
  Plug a laptop into loom0 and browse https://frontend.loom
  This box serves DHCP on 10.13.37.0/24 and answers for *.loom
  Loom: starting -- 12/18 pods ready.

  USB key guard: armed. Removing the USB key powers this
  box off after 10 seconds.

  LUKS recovery passphrase: ka3mn-7pqrs-t4uvw-x9yzb-cd2ef-gh5jk
  Write it down. Without the USB stick it is the only way
  to unlock this disk, and nobody else holds a copy.

[press ENTER to login]
```

<!-- editorconfig-checker-enable -->

**`Loom: starting -- 12/18 pods ready.`** is the one line that changes while the box runs, and it answers the
question somebody walking up to a monitor actually has. A bring-up takes tens of minutes to hours, and until
it is done the appliance serves nothing; this says how far along it is without logging in. It reads
`ready.` once every pod the cluster wants is running, `degraded` if the box was up and something has since
stopped, and `failed to start` if `up.sh` returned non-zero.

The line is **absent** for the first minute or so of every boot, while the cluster has not answered yet, and
absent for the whole of first-time setup, which has no cluster at all. That is deliberate: it earns its row
once it has a number on it. The banner is written straight to the VT with no paging — see
[Why the banner sometimes drops the logo](#why-the-banner-sometimes-drops-the-logo) — so on a `--wifi` box,
where a QR code is already competing for the same rows, a line saying only "waiting" would cost the logo for
nothing.

It is redrawn when it changes, not on a timer, and only while the screen is still showing the login prompt: a
box where somebody has pressed a key is a box with a session on it, and restarting a getty under that session
would blank it. `loom-banner-refresh` on a console reprints it by hand.

The eyes are the same mark the boot splash and the installer stick show, drawn in half blocks and in the
logo's amber — the screenshot above cannot show the colour, but the monitor does. One rendering, everywhere:
the pre-login banner, `loom-info` re-run on an `Alt-F2` console, and the installer menu all print it from the same
command, in the same colour the splash paints its progress bar.

Reaching that exact amber on a console takes redefining a palette entry, because the Linux VT shoehorns even a
24-bit colour request into its 16 basic ones. The appliance therefore rewrites the entry once, when it draws
the login banner, and never restores it — the VT looks a palette up when it paints rather than when the
character was written, so putting it back would recolour the eyes already on screen. Anything else on that
console that asks for yellow gets the amber too, which is the intent. The sequence goes only to a real VT:
it hangs an xterm until somebody presses return, so the panes of the console session get the colour without
it, and come out amber anyway from the palette the banner already set underneath them.

Both screens run in Cozette rather than a kernel built-in console font. What that displaces is coarser than it
sounds: the kernel picks its font from the size of the framebuffer it is handed, and on a large panel it lands
on Terminus 16x32. A 2560x1600 monitor therefore starts out with a 160x50 grid for a three-pane session with
`btop` in one of them. Cozette also covers the box drawing tmux frames its panes with and the graded blocks
`btop` draws its meters out of, which the built-in fonts do not carry in full.

The size is a knob, `loom.consoleFont` in `nixos/branding.nix`. Cozette ships two sizes and nothing between
them, and they are identical in everything but size:

| `loom.consoleFont` | cell | grid on a 2560x1600 panel |
| --- | --- | --- |
| kernel default, for comparison | 16x32 | 160 x 50 |
| `large` | 12x26 | 213 x 61 |
| `small` (the default) | 6x13 | 426 x 123 |

Six pixels is the floor, and the logo is what sets it. The eyes above are made of `█`, `▄` and `▀`, most
console fonts are missing the half blocks, and a build that selects one that is fails rather than shipping a
box whose banner is a screen of holes. The appliance also asks its firmware for the largest console mode it
has, since the column count is only ever the framebuffer width divided by that cell.

### Why the banner sometimes drops the logo

agetty writes the login banner straight to the VT and never pages it, so a banner taller than the grid loses
its top rows — and the grid is not something the image can know in advance. It is the panel's pixel height
over the console cell, anywhere from 33 rows to 123 in the table above.

**`loom-banner-repaint.service`** is what keeps that from cropping the screen. tty1 is painted _while_ the font
is still changing under it: fbcon starts on the kernel's built-in font, `loom-console-font` puts Cozette on,
the DRM driver takes the console and resets it, and `loom-console-font-reapply` puts Cozette back. Each of
those resizes the VT, and **a shrinking VT keeps the bottom of the screen and discards the top** — so the logo
goes first and the banner that survives starts partway down. tty2 and up never show it, because logind only
spawns them when you switch to one, by which point nothing is moving any more.

The repaint watches `/dev/tty1` for the first minute of uptime and redraws the banner whenever the geometry has
been disturbed since it was last drawn — not whenever the row count currently differs, which is a different and
insufficient question: the count an operator finally sees is usually the very one the banner was drawn at, with
its top thrown away in between. It declines to do anything once somebody has logged in, rather than restart a
getty out from under a live session.

The banner itself is always printed whole. An earlier version measured the console and dropped the logo, then
the QR code, to fit — there is no moment in the boot at which that measurement stays true, and it shipped a box
whose login screen had neither on a console with room for both.

If a banner still looks wrong, `loom-info` on the console reprints it against the terminal it is run in.

Setting the font once is not enough to make it stick. `systemd-vconsole-setup` runs before most of the machine
exists, and whatever re-initialises the console afterwards — a real display driver taking over from the
firmware framebuffer, or plymouth letting go of the screen — throws the font away and the kernel's own comes
back. A `loom-console-font` service therefore applies it a second time, after plymouth has released the console
and before any getty paints a character. It has to be before: changing the font resizes the console, so doing
it afterwards would leave the banner in wrapped fragments.

That second pass is late only because plymouth holds it there, which first-time setup — booting without a
splash — does not, so there it landed before the display driver took over and the mode kept the kernel's font
for the whole run. The driver taking over emits no event the console layer keys on, but the card does, so a
udev rule on it starts `loom-console-font-reapply` and the font survives in both modes.

So somebody who only walks past the monitor still gets everything they need. Nothing logs in by itself — the
screen stays here until a key is pressed, which is also why the banner can no longer be scrolled away. Pressing
a key logs in as `loom` with no username and no password, for the same reason `sudo` needs none: there is no
remote access, and physical possession of box and stick is the whole trust boundary.

That keypress opens a three-pane session:

```text
┌─────────────────────┬─────────────┐        ┌─────────────────────┬─────────────┐
│  the bring-up       │             │        │  k9s, on the pods   │             │
│  log, live          │    btop     │  once  │  of the loom        │    btop     │
│  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁  │             │  it is │  namespace          │             │
│  Loom ━━━━  12/18   │             │   up   │                     │             │
├─────────────────────┴─────────────┤        ├─────────────────────┴─────────────┤
│                                   │        │                                   │
│           the assistant           │        │           the assistant           │
│                                   │        │                                   │
└───────────────────────────────────┘        └───────────────────────────────────┘
  LOOM  starting 12/18   Alt-F2 for a shell   × restart pane   × detach
```

The top-left pane follows whichever unit this boot mode runs — `loom` under the default entry, `loom-fetch`
under first-time setup — and hands over to `k9s` once the box is up. `btop` sits beside it.

**A readiness bar is pinned along the bottom of that pane** while the log scrolls past above it: how many of
the pods the cluster wants are ready, and — when something is not going to resolve by waiting — which pod and
why, as `waiting on: loom-ollama-0 (ImagePullBackOff)`. If the count stops moving for five minutes it says so,
which is the failure a percentage hides best: nothing is crashing, nothing is pulling, the number simply sits
there. The bar pulses rather than filling while there is no cluster to ask yet, because a ratio of nothing to
nothing is not zero per cent and must never be drawn as a hundred.

The bar belongs to run mode. First-time setup pulls container images for hours with no cluster to ask and none
coming, so nothing publishes readiness there and that pane is the `loom-fetch` log alone — every line of it,
which is the whole of what that mode has to show for itself.

What it counts is **workloads**, not pods: a Deployment mid-rollout has no pods yet for the replicas it has
not created, so counting pods alone makes the denominator chase the numerator and the bar sits near the end
from the first second. Deployments, StatefulSets, DaemonSets and Jobs each carry both numbers. Two cases are
worth knowing about, because both would otherwise make the bar lie:

- **KEDA scales to zero.** `worker`, `tika`, `gotenberg` and `ollama` are allowed to sit at zero replicas
  when there is nothing queued. A workload that wants none is not counted at all — counted, it would hold the
  bar short of the end for the life of the box.
- **Jobs never become Ready.** The init and pre-install Jobs gate everything behind them and finish as
  `Succeeded`, so a check written in terms of Ready pods never sees them. They count as done when they have
  completed.

**The status line carries the same answer for the life of the session** — `starting 12/18`, then `ready` in
green, or `degraded` in red. That matters because the bar goes when the pane becomes `k9s`, and a box that
comes up fine on Monday and loses a pod on Tuesday would otherwise say nothing anywhere. It is read from a
file rather than from the cluster: `loom-ready.service` does the asking every five seconds, so a cluster that
stops answering can never hang the tmux server. Typing `loom-ready` on an `Alt-F2` console prints the same
panel plus every workload still outstanding, and exits non-zero unless the box is up — which is what makes it
usable from a script. The assistant gets
the full width along the bottom, because it is the only pane anyone types prose into and a chat folded into
half a console is unreadable; the two above it are glanced at rather than read.

`btop` picks its boxes from the size of that pane — the full `cpu mem net proc` set only where there is room
for it — and its **net** box is pinned to the interface carrying the appliance address: `loom0` normally,
`loombr0` on a `--wifi` box, where the wired port and the radio are two ports of the same bridge and only the
bridge sees both. Left to itself `btop` would graph `lo` and keep graphing it, because it picks whichever
interface has moved the most bytes so far and minikube's own loopback traffic wins that outright. Pinning it
also puts the box address in the pane's header. The pin is a starting point, not a lock: `b` and `n` still
cycle interfaces in that box.

On a box that declares a `gpuVendor` — today the EVO-X2 — the **cpu** box also carries the GPU, reading it
through the same vendor library `up.sh` uses for its preflight. It rides inside the cpu box rather than
taking a box of its own, which is why it survives every rung of that ladder down to the smallest: a pane
this size has no room for a fifth box, and `btop` shows the GPU one way or the other but not both. It costs
the image nothing either — the build carries no compute stack for it, only a link to the one already there.
See [GPU support](#gpu-support).

**None of these three panes is a shell.** The middle one used to be. `Alt-F2` is the way to a prompt — see
below.

That left pane does not stay a log. The moment the unit has **succeeded** — `up.sh` exited 0, and the `loom`
namespace exists — it hands the screen over to **`k9s`** on the pods, because from then on the log is a
finished transcript while the pods are the live thing, and _"is it actually up?"_ is a question the log answers
only indirectly: `up.sh` returns long before the last container is ready, and a pod that crash-loops an hour
later says nothing there at all. A bring-up that **failed** keeps its log on screen, which is the one case
where the log is what matters; so does first-time setup, which deploys nothing and powers the box off when it
is done. The log is never lost either way — `journalctl --unit loom --follow` on an `Alt-F2` console brings it
back, and the pane says so as it switches.

### The assistant pane

Only on an image that deploys Ollama, which today means `evo-x2` alone — see
[AI services follow the GPU](#ai-services-follow-the-gpu). Elsewhere the session is two panes and `opencode`
is not in the closure at all.

The bottom pane runs [opencode](https://github.com/anomalyco/opencode) against the Ollama already running in
the cluster, at `https://ollama.loom/v1/`. The box has carried a model on the stick since the first build and
nothing on the console could reach it; this is what reaches it. There is no account, no API key worth the name,
and no traffic off the box.

It goes in through Traefik because that is the only door from outside the cluster — the workers reach the same
Ollama by its in-cluster Service instead. `https`, not `http`: every ingress is bound to the `websecure`
entrypoint alone, so nothing answers for `ollama.loom` on port 80.

That certificate is the one the chart generates for itself at install time, and it is self-signed, which an
HTTP client will not accept on trust the way a human clicks through a browser warning. So `loom-chat` builds a
CA bundle from the certificate secrets the cluster holds and passes it in `NODE_EXTRA_CA_CERTS`. Certificate
verification stays **on**: if the bundle cannot be built the pane says so and waits, rather than falling back
to an unverified connection.

Two things have to be true of that certificate, and they are the two things that have to be true of the Loom
release the box ships.

**It has to name `ollama.loom` explicitly.** A certificate carrying only `DNS:*.loom` does not work: a
wildcard needs at least two dots, so OpenSSL refuses to expand one under a single-label parent and Bun — like
curl — rejects the connection with "no alternative certificate subject name matches target hostname".
Releases whose chart predates `hostnames` in `charts/values.yaml` (everything up to and including
`1.4.0-rc2`) generate a certificate the assistant cannot verify, and the pane says exactly that while it
waits.

**It has to be usable as its own anchor.** Nothing issued it, so trusting it means trusting it as a root, and
a verifier handed a root asks whether it was allowed to sign anything. A certificate whose critical
`keyUsage` omits `keyCertSign` was not, and Bun refuses it with "unable to verify the first certificate" —
after the pane has started, because the wait ahead of it uses `curl`, and OpenSSL accepts such a certificate
without complaint. `1.4.0-rc4` is the one release that generates one; the chart now emits no `keyUsage` at
all on that path, and names `cert sign` on the `certificate.enabled` one.

See [Hostnames and the self-signed certificate](installation.md#hostnames-and-the-self-signed-certificate).
On a box already running an affected release, replacing the `self-signed-cert` secret by hand is the only
fix, and it sticks, because the Job never replaces a certificate that covers every host.

The model is **pinned at build time** to `LOOM_CHAT_MODEL` in `vars.sh`, which must name a model
`ollama/Dockerfile` actually bakes in — on an air-gapped box there is no way to fetch another, and pointing the
pane at a tag the workers do not use would make Ollama load a second model and evict the one it is indexing
with. **`loom-chat`** is the same screen as a command, for an `Alt-F2` console.

The pane waits until Ollama answers at `https://ollama.loom/` over a connection that verifies, so on a cold box
it stays blank-ish for as long as the bring-up takes. It names what it is waiting for while it waits, including
whatever `curl` said — a certificate that does not verify, a route that 404s and a name that resolves to some
other service are different problems, and the pane distinguishes them.

Whether the pinned model is actually in Ollama's inventory is **not** part of that wait. The pane warns once if
it is missing and starts anyway: a Ready `ollama` pod says nothing about its model store (the chart probes
`/api/ps`, which answers on an empty one), so waiting for the model is waiting on something that may never
arrive. The assistant then fails its first question with an error you can read, in a pane that keeps it on
screen and offers `× restart pane` — see `ollama list` in the `ollama` pod for what the box really has.

Sessions and caches go to `tmpfs` under `/run/loom`, not to the encrypted root: what an operator asked about an
evidence set is not something to leave on the disk by accident.

Two things worth knowing before leaning on it:

- **It is an agent, not a chat box.** It can read and write files and run commands as `loom`, which is in
  `wheel` and `docker`. On a box whose trust boundary is physical possession that changes little — but it is a
  different proposition once `--wifi` is on, and worth re-reading [the threat model](#threat-model) in that
  case.
- **The model is small.** It is a 9B, which is capable at short, well-scoped questions and gets unreliable as
  the number of tools in play grows. Treat it as a knowledgeable colleague who has not seen your cluster,
  rather than as something to hand a long autonomous task.

### Driving it with a mouse

Plug a USB mouse in — at any time, including long after boot — and the console gets a pointer: one character
cell in reverse video, following the mouse. There is no X and no Wayland involved; the pointer is drawn by the
kernel and the events are decoded by `gpm`.

**Click a pane to work in it.** The pane under the pointer takes the focus, and the mouse then reaches into
whatever is running there: `btop`'s own menus and boxes respond to clicks, `k9s` selects the row you click,
and the assistant's input box takes focus. The scroll wheel scrolls the pane under the pointer, and dragging a
pane border resizes it.

**The two controls at the bottom right are buttons.** `× detach` ends the session and returns the box to the
banner and the press-a-key prompt — the closest thing this appliance has to a lock screen. `× restart pane`
forces the focused pane's program to start over, for the times something is wedged rather than gone.

A mouse is never required. Everything below still works without one, and a box with no mouse behaves exactly
as it did before any of this existed.

### Panes look after themselves

Each pane runs one application and nothing else, so quitting one is a single keystroke — `q` in `btop`, `:q`
in `k9s`. That no longer costs you the pane: every pane is supervised, and the program comes straight back
with a one-line note saying so.

A program that exits _immediately_, twice running, is treated as broken rather than quit: the gap before each
retry doubles up to thirty seconds, so the error stays on screen long enough to read instead of scrolling past
in a loop. Nothing on this box spins a pane at full tilt.

Inside `k9s`, `d` describes a pod, `l` shows its logs, `0` switches namespace and `:q` restarts it.
**`loom-k9s`** is the same screen as a command, for an `Alt-F2` console.

`Ctrl-b` does nothing: the session is a kiosk, so tmux's prefix and its right-click menus are switched off and
the status line carries the two controls anyone needs. `Alt-F2` through `Alt-F6` give a plain console with no
session at all. Since no pane of the session is a shell, that is both the way back in if anything above
misbehaves **and** the ordinary way to get a prompt — `loom-info`, `loom-k9s`, `loom-chat`, `loom-up` and
`loom-down` are all on the `PATH` there, as is `tmux -S /run/loom/tmux.sock` if the session itself needs
handling. `Alt-F1` returns to the session.

None of that is a security boundary, and it is not meant to be one: every console autologins the operator
account, which holds passwordless root. Physical possession of the box and its USB key is the boundary — see
[Threat model](#threat-model).

`loom-up` and `loom-down` wrap `up.sh` with the flags the appliance needs:

```bash
loom-up --offline
loom-down
```

Use these rather than `./up.sh` directly. Bare `up.sh` would rewrite `/etc/hosts` and `/etc/sysctl.d`, both of
which this appliance declares through NixOS — it would undo its own configuration. `loom-up` passes
`--skip-setup_system --skip-install_host_entries` for exactly that reason, and forwards everything else through.

Note the absence of `up.sh`'s `--expose`. Making Loom reachable from the appliance network is a separate unit,
**`loom-expose`**, and it is not something `loom-up` starts or stops:

```bash
systemctl status loom-expose      # is this box reachable from the network port?
iptables --table nat --list-rules LOOM-EXPOSE
```

It installs two iptables chains that send anything arriving on the box's own address at port 80 or 443 to the
minikube node, where Traefik binds those ports directly. `--expose` does the same job a different way — it runs
`minikube tunnel`, which forwards each port over an `ssh` connection into the node — and the two cannot be
combined, because the DNAT happens before the kernel would hand a packet to a tunnel's socket. If you do want
the tunnel for some reason, stop `loom-expose` first.

Only 80 and 443 are published, which is all the firewall opens. Nothing else Traefik carries (IMAP, AMQP,
Redis, Prometheus) is reachable from the network port.

## Wiping a box

Boot the stick (via the firmware boot menu) and choose **ERASE ALL DATA**. The interlock still applies here and
always will — a wipe never runs unattended. It prints every disk that will be destroyed, and the one that will
not, and asks for the words `ERASE ALL DATA`.

Booting the stick on a box it installed does not start an install, so you land in the menu and can pick this.

The wipe is layered, cheapest first. Because the disk is encrypted, erasing the LUKS keyslots _is_ the wipe and
takes under a second; everything after it is defence in depth:

1. `cryptsetup luksErase` on the pooled container, and on any container sitting directly on a partition
2. random data over the headers, then `wipefs`
3. `sgdisk --zap-all`
4. `blkdiscard`
5. `nvme format --ses=1`, falling back to `--ses=2`

Layers that a given drive does not support are skipped and reported. A full overwrite is deliberately not the
default: on a wear-levelling NVMe it takes hours and still cannot reach retired or over-provisioned blocks, so it
is both slower and weaker than a controller-level erase.

## GPU support

Whether a box offloads Ollama to a GPU is declared once, as `gpuVendor` in `nixos/platforms/<id>.nix`, and
nothing at build time turns it on. There is no `--gpu` flag: asking for a GPU the box does not have would
only produce a stick that fails on first boot. The Spark and the EVO-X2 declare one and the NUC 12 does
not — and because [AI services follow the GPU](#ai-services-follow-the-gpu), that is also what decides which
boxes ship Ollama at all.

**On the EVO-X2** the appliance passes `--gpus amd` to `up.sh`, which selects `charts/values-amd-gpu.yaml`,
enables minikube's `amd-gpu-device-plugin` addon and asks `minikube start` for the GPU. `amdgpu` is mainline
and already loaded — it is what puts the installer menu on the monitor — and it is what exposes `/dev/kfd`
for minikube's docker driver to pass into the node container. The ROCm userspace lives inside the
`ollama/ollama:rocm` image, so the box itself carries only `rocm-smi`, which `up.sh` needs for its preflight.
That same `rocm-smi` is what puts the GPU readout in the console's `btop` pane: `btop` already knows how to
read it and only needs pointing at the copy the box has, so the readout adds nothing beyond the link.

That last point is also what insulates this box from an unsettled corner of the ecosystem: ROCm's support
for this GPU (`gfx1151`) has been uneven enough that published benchmarks disagree about which release is
fastest, and nixpkgs has open bugs against its own ROCm on this part. None of it reaches the appliance,
which needs `amdgpu` and two kernel parameters and nothing else.

Those two parameters are how the iGPU gets its memory: `amdgpu.gttsize` and `ttm.pages_limit`, set in
`nixos/platforms/evo-x2.nix` to a 64 GiB ceiling — half the box, comfortably more than the baked-in models
need, and leaving the rest of the stack more than twice the 25 GiB `LOOM_MIN_MEMORY` that `up.sh` checks.
They raise a ceiling rather than reserving anything: nothing leaves the host until the GPU actually pins
it. Set the firmware's VRAM split to its _minimum_ to go with them, and see
[What you need](#what-you-need) for why that is the right way round.

**On the DGX Spark** the appliance passes `--gpus nvidia` to `up.sh`, which selects
`charts/values-nvidia-gpu.yaml`, enables minikube's `nvidia-gpu-device-plugin` addon and asks
`minikube start` for the GPU. The driver is stock nixpkgs: the pin carries NVIDIA 595.71.05 with the open
kernel modules, which is what a GB10 Blackwell needs, and `nixos/platforms/spark.nix` adds
`hardware.nvidia-container-toolkit` so the device reaches the minikube node container through a CDI spec.
As on the EVO-X2, none of the compute stack lives on the host — the CUDA userspace is inside the `ollama`
image, and the box carries only `nvidia-smi`, which comes out of the driver itself and which `up.sh` needs
for its preflight. That same driver puts the GPU readout in the console's `btop` pane.

> **This has not been confirmed on hardware yet.** Nobody has booted this image on a Spark, so
> `gpuVendor = "nvidia"` is a claim from documentation rather than a measurement. Run
> `loom-platform-info` on the box before relying on it — its **GPU** and **GPU in containers** sections
> exist for exactly this, and [When the GPU does not come up](#when-the-gpu-does-not-come-up) is the way
> back if the claim turns out wrong.

Two things about this box are genuinely unsettled, and neither is the GPU.

The first is **the network port**. The ConnectX-7 presents two QSFP cages with two 100G MACs each, so Linux
is expected to show four `mlx5` interfaces — `netMatch` in `nixos/platforms/spark.nix` matches the driver
and therefore matches all four, and whichever udev processes first becomes `loom0`. There is also a 10GbE
RJ45 that NVIDIA's documentation calls the management port, which is the more natural thing to hand an
operator a cable for. `loom-platform-info` prints the PCI ids and port ids for every interface and warns
when more than one matches; use `--interface NAME` to pin the right one until the platform file can be
narrowed. See [The appliance network interface](#the-appliance-network-interface).

The second is **the kernel**. Every published route to NixOS on this box goes through NVIDIA's kernel fork
via [`graham33/nixos-dgx-spark`](https://github.com/graham33/nixos-dgx-spark), and this image deliberately
does not use it. Their own USB image offers both kernels and describes the difference as _Ethernet_, not
GPU; their fork is NV-Kernels 6.17.13 where our pin ships 6.18.49, so taking it means going back a major
version on the one subsystem in question; and it would be built from source on aarch64 with no cache hits.
What it would buy, besides possibly the NIC, is `cppc_cpufreq.auto_sel_mode=1`, which upstream measures at
roughly 3× single-thread memory bandwidth and which needs their kernel to work — a real cost of the choice
made here. If `loom-platform-info` shows no usable wired NIC on a Spark, that report is the evidence for
reopening this.

**On the NUC 12** there is nothing to enable. Loom has no path to an Intel iGPU, and neither has `btop`.

### When the GPU does not come up

`up.sh` counts GPUs through the vendor's SMI tool — `rocm-smi` or `nvidia-smi` — and hard-exits below
`LOOM_MIN_GPU`. So a box where the GPU does not enumerate does not quietly fall back to the CPU: it serves
nothing, and there is no remote access to repair it with. Worth watching for on first boot on both GPU
platforms — Strix Halo is recent enough on the EVO-X2, and on the Spark nothing has been confirmed on
hardware at all.

The way out is a new stick:

```bash
build-appliance-image --platform evo-x2 --no-gpu --tag 1.4.0 --flash /dev/sdX
```

That image is the CPU-only one this platform used to produce — which, by the rule above, also means no Ollama
and no open-webui. Full-text search, OCR, metadata extraction and archive import all still work. The build
prints what it decided:

```text
      gpu       : disabled by --no-gpu (amd available)
```

`--no-gpu` is refused on a platform that has no GPU to disable, so a stick that came out CPU-only did so for
a reason you can read back off it.

On the Spark the same flag does the same job — `build-appliance-image --platform spark --no-gpu ...` — with
one difference worth knowing: it drops the offload and the AI services but **keeps the NVIDIA driver**,
because on that box the driver is also what puts the console on the monitor. The result is therefore not
"the Spark stick without NVIDIA"; it is the Spark stick without the GPU _offload_.

Before reaching for a new stick, run `loom-platform-info`. On the EVO-X2 it says whether `/dev/kfd` exists
at all, what `rocm-smi` reports, and — the case that looks like a working GPU but performs like none — how
much GTT the kernel actually granted against the ceiling the image asked for. A GTT figure far below that
ceiling means the kernel parameters did not take effect, which is a different problem from ROCm not
enumerating and has a different fix.

On the Spark it answers the equivalent questions in two places. The **GPU** section reports
`/dev/nvidiactl`, the loaded `nvidia*` modules, the driver version out of `/proc/driver/nvidia/version` and
what `nvidia-smi -L` names the board. The **GPU in containers** section covers the half that a working
`nvidia-smi` does not prove: whether a CDI spec was generated, whether `nvidia-ctk` is present, and which
runtimes docker knows about. A box where `nvidia-smi` works but no CDI spec exists will pass `up.sh`'s
preflight and then schedule Ollama onto a node advertising no `nvidia.com/gpu` at all.

## Troubleshooting

**Start with `loom-platform-info`.** It prints what the box actually is beside what the image was told to
expect, which is the fastest route through most of what follows:

```bash
loom-platform-info
```

It reports the wired ports with their drivers and PCI paths — and says outright how many of them matched
the platform's `netMatch`, and whether `loom0` exists; the radios, including whether the driver advertises
AP mode at all, which is what decides whether `--wifi` can work; the GPU, with the firmware VRAM carve-out
and the GTT pool side by side, plus whether `/dev/kfd` is there for `up.sh` to find; and the firmware
version and boot mode. `--json` gives the same thing machine-readably; `--output FILE` writes to a file.

The same command is available in the development shell, where it reports whatever machine you run it on.
That is deliberate: it is how a box gets checked **before** there is an appliance image for it, and it is
what to run on a new box whose values in `nixos/platforms/<id>.nix` are still guesses.

One limitation worth knowing: an installed appliance has no route off its own network, so the report leaves
by photograph, by `--output` onto a mounted filesystem, or by being read aloud. There is no upload.

**The box boots into the installer every time.** The firmware is preferring the stick's removable-media path.
Re-run the install, or set the internal disk first in the firmware boot order.

**The box will not boot and asks for a passphrase.** The stick is missing, in a different port, or its key
partition is empty. Enter the recovery passphrase, then check the stick — the installer menu's status screen
reports whether a key is present.

**The login screen says `loom0 does not exist`.** The platform's interface match selected nothing, so the box
has no address and serves no DHCP or DNS. The warning is printed under the banner, above the press-a-key
prompt, and lists the interfaces that are present; rebuild the stick with `--interface <one of them>`. On the
EVO-X2, first just try the other ethernet port. `loom-platform-info` names the ports and says which of them
the match did and did not select — including the case where it matched more than one, where udev picks and
moving the cable is the fix.

**A laptop gets an address and resolves `*.loom`, but nothing loads.** DHCP and DNS come from `dnsmasq`;
reaching the stack is `loom-expose`, a different unit, so one working says nothing about the other. Check it
with `systemctl status loom-expose` and `iptables --table nat --list-rules LOOM-EXPOSE`. If the rules are
there, the stack itself is probably still coming up — `curl --insecure https://frontend.loom` from an
`Alt-F2` console goes straight to Traefik and bypasses the whole question, so it separates "not exposed" from
"not up yet" in one command.

**A laptop plugged into the box loses the internet on every other interface.** The box's lease is naming it as
the laptop's default gateway, and a wired link outranks wifi nearly everywhere, so everything the laptop sends
anywhere goes to a box with no upstream. Confirm it with `ip route` (`route print` on Windows): a `default via
<box address>` is the symptom. Sticks built before this was fixed all do it — `dnsmasq` sends a router option
of its own accord unless one is explicitly suppressed, so leaving it unconfigured was not the same as leaving
it out. Build a new stick. To finish a session on the stick in hand, delete that route on the laptop
(`sudo ip route del default via <box address>`); it comes back at the next lease renewal.

**`loom-up` refuses to start, complaining about the minikube address.** The `*.loom` names are pinned to
`192.168.49.2` in `/etc/hosts` and minikube came up somewhere else. `minikube delete` and retry.

> **`minikube delete` destroys the container images, and on an appliance that is not recoverable.** The images
> live inside the minikube container's own storage, and nothing on the box keeps a second copy — so deleting
> the cluster drops all ~60 GB of them. Refetching needs the first-time-setup entry, which no longer exists
> once setup has run. The only way back is a reinstall from the stick, and that destroys the LUKS container
> and every indexed document with it. **Copy anything you care about off the box first.**

**Loom does not come up after a reboot in run mode.** The first pane of the console session already shows
`loom`'s log. If the image store is empty, first-time setup either never ran or its images have since been
dropped — see the `minikube delete` warning above, which is the usual cause and the usual bad news.

**The console session will not start.** It prints why and hands over a plain shell on the same screen rather
than looping; `Alt-F2` gives another one regardless. Reattach by hand with `loom-console`, or throw the session
away with `tmux -S /run/loom/tmux.sock kill-server` and run `loom-console` again.
