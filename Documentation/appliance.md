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
- **The console runs an AI agent that can act on the box.** The bottom pane is `opencode` wired to the
  cluster's own Ollama — it reads and writes files and runs commands as `loom`, which is in `wheel` and
  `docker`. It talks to nothing outside the box, so this adds no network exposure; what it adds is a way for
  anyone already at the keyboard to act through natural language instead of a shell. Given the bullet above,
  that is not a new boundary being crossed — but it is one more reason the box must not be left unattended
  with the stick in it.
- **Bluetooth is disabled** by module blacklist and `rfkill`, in every image. **WiFi is disabled the same way
  unless the image was built with `--wifi`**, which turns the box into an access point — read
  [The WiFi access point](#the-wifi-access-point) before using it, because it changes most of the bullets
  above. Either way this is a software guarantee; disable the radios in the box's own firmware as well if the
  site requires it.

## Supported platforms

Two boxes are supported. Pick one with `--platform`; it decides the architecture and everything else that
differs between them.

| | `spark` (default) | `evo-x2` |
| --- | --- | --- |
| Box | NVIDIA DGX Spark | GMKtec EVO-X2 (AMD Ryzen AI Max+ 395) |
| Architecture | `aarch64-linux` | `x86_64-linux` |
| Build host | aarch64 — a Spark can build sticks for its siblings | any ordinary x86_64 machine |
| Console | monitor and USB keyboard | monitor and USB keyboard |
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
| `--wifi` | Also run an access point, bridged onto the wired port. Radios are disabled without it. Read [The WiFi access point](#the-wifi-access-point) first. |
| `--wifi-ssid SSID` | Network name. Defaults to a generated `loom-xxxx`. |
| `--wifi-psk PSK` | WPA passphrase. Defaults to a generated one. Letters, digits, `-` and `_` only. |
| `--wifi-country CC` | ISO country code. Moves the AP to 5GHz; without it the AP stays on 2.4GHz. |
| `--wifi-interface NAME` | Pin the radio by kernel name. It is renamed to `loomwl0` either way. |
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
and shown on the console's login screen.

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
the dnsmasq binding and the console banner all pin to that name. If nothing matches, a `loom-network-check`
service says so on the console at every boot and lists the interfaces that do exist.

The EVO-X2 has two ethernet ports and both are Realtek, so the match cannot single one out: whichever udev
processes first becomes `loom0`, and the other keeps its kernel name. If the box comes up unreachable, try the
other port. To pin a specific one, read its stable path off the box and rebuild with `--interface`:

```bash
udevadm info /sys/class/net/<iface> | grep -E 'ID_PATH=|ID_NET_DRIVER='
```

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

## Installing

1. Plug the stick into the box and boot from it.
2. The installer menu appears on the console. Its header
    names the **Loom release and the platform the stick was built for**, so check there that you booted the
    right stick before going further; two sticks are otherwise indistinguishable. Below that it shows which
    disk is the boot medium (never touched), whether the stick's LUKS key is present, and which disk is the
    install target.
3. Choose **Install**. If the box has **more than one internal disk**, as the EVO-X2's two M.2 slots allow, it
    lists them all and asks which one — rather than silently picking the first. It then names the disk it is
    about to destroy and asks for the word `INSTALL`, which is not something typed by accident.
4. It partitions the internal disk, creates the LUKS container from the stick's key, installs the appliance
    closure entirely offline, enrols a recovery passphrase, makes the internal disk the default boot entry, and
    selects **first-time setup** as the entry that disk boots.
5. **Write down the recovery passphrase it prints.** It holds the screen for 30 seconds and then reboots on
    its own, so an install nobody comes back to still finishes. Nothing is lost if you miss it: the installed
    box shows the same passphrase on every console login.
6. Press enter to reboot immediately, or let the countdown run out. The box boots into the internal disk and
    straight into first-time setup — no entry to pick — so have it on a network with internet by then. Leave
    the stick in.

The countdown is skipped in one case. If the installer could not make the internal disk the default boot
entry — no NVRAM entry, or its own loader still on the UEFI removable-media path — it says so and waits for
enter instead of rebooting itself, because that warning asks you to change the firmware boot order and it is
the one thing on that screen the installed box does not repeat. A wipe (menu option 2) likewise always waits.

The installer moves its own loader off the UEFI removable-media path afterwards. Without that, most firmware
would boot the installer instead of the appliance on every restart, because the stick never leaves. The
installer stays reachable from the firmware's own boot menu for reinstalls and wipes.

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

The box is not a gateway and does not advertise itself as one, so the laptop keeps whatever other networking it
has.

### From the box's own console

The console shows the box's banner before anyone logs in — release, platform, which port to plug a laptop
into, the subnet it serves, whether the key guard is armed, and the LUKS recovery passphrase:

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

  USB key guard: armed. Removing the USB key powers this
  box off after 10 seconds.

  LUKS recovery passphrase: ka3mn-7pqrs-t4uvw-x9yzb-cd2ef-gh5jk
  Write it down. Without the USB stick it is the only way
  to unlock this disk, and nobody else holds a copy.

[press ENTER to login]
```

<!-- editorconfig-checker-enable -->

The eyes are the same mark the boot splash and the installer stick show, drawn in half blocks and in the
logo's amber — the screenshot above cannot show the colour, but the monitor does. One rendering, everywhere:
the pre-login banner, `loom-info` re-run in the shell pane, and the installer menu all print it from the same
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
│                     │             │  it is │  namespace          │             │
├─────────────────────┴─────────────┤   up   ├─────────────────────┴─────────────┤
│                                   │        │                                   │
│           the assistant           │        │           the assistant           │
│                                   │        │                                   │
└───────────────────────────────────┘        └───────────────────────────────────┘
  LOOM    Ctrl-b d detach | Alt-F2 for a shell
```

The top-left pane follows whichever unit this boot mode runs — `loom` under the default entry, `loom-fetch`
under first-time setup — and hands over to `k9s` once the box is up. `btop` sits beside it. The assistant gets
the full width along the bottom, because it is the only pane anyone types prose into and a chat folded into
half a console is unreadable; the two above it are glanced at rather than read.

`btop` picks its boxes from the size of that pane — the full `cpu mem net proc` set only where there is room
for it — and its **net** box is pinned to the interface carrying the appliance address: `loom0` normally,
`loombr0` on a `--wifi` box, where the wired port and the radio are two ports of the same bridge and only the
bridge sees both. Left to itself `btop` would graph `lo` and keep graphing it, because it picks whichever
interface has moved the most bytes so far and minikube's own loopback traffic wins that outright. Pinning it
also puts the box address in the pane's header. The pin is a starting point, not a lock: `b` and `n` still
cycle interfaces in that box.

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

The bottom pane runs [opencode](https://github.com/anomalyco/opencode) against the Ollama already running in
the cluster, at `https://ollama.loom/v1/`. The box has carried a model on the stick since the first build and
nothing on the console could reach it; this is what reaches it. There is no account, no API key worth the name,
and no traffic off the box.

It goes in through Traefik because that is the only door from outside the cluster — the workers reach the same
Ollama by its in-cluster Service instead. `https`, not `http`: every ingress is bound to the `websecure`
entrypoint alone, so nothing answers for `ollama.loom` on port 80.

That certificate is the wildcard `*.loom` one the chart generates for itself at install time, and it is
self-signed, which an HTTP client will not accept on trust the way a human clicks through a browser warning.
So `loom-chat` builds a CA bundle from the certificate secrets the cluster holds and passes it in
`NODE_EXTRA_CA_CERTS`. Certificate verification stays **on**: if the bundle cannot be built the pane says so
and waits, rather than falling back to an unverified connection.

The model is **pinned at build time** to `LOOM_CHAT_MODEL` in `vars.sh`, which must name a model
`ollama/Dockerfile` actually bakes in — on an air-gapped box there is no way to fetch another, and pointing the
pane at a tag the workers do not use would make Ollama load a second model and evict the one it is indexing
with. **`loom-chat`** is the same screen as a command, for an `Alt-F2` console.

The pane waits until Ollama serves that model and says so while it waits, so on a cold box it stays blank-ish
for as long as the bring-up takes. Sessions and caches go to `tmpfs` under `/run/loom`, not to the encrypted
root: what an operator asked about an evidence set is not something to leave on the disk by accident.

Two things worth knowing before leaning on it:

- **It is an agent, not a chat box.** It can read and write files and run commands as `loom`, which is in
  `wheel` and `docker`. On a box whose trust boundary is physical possession that changes little — but it is a
  different proposition once `--wifi` is on, and worth re-reading [the threat model](#threat-model) in that
  case.
- **The model is small.** It is a 9B, which is capable at short, well-scoped questions and gets unreliable as
  the number of tools in play grows. Treat it as a knowledgeable colleague who has not seen your cluster,
  rather than as something to hand a long autonomous task.

`Ctrl-b` then an arrow key moves between panes. Inside `k9s`, `d` describes a pod, `l` shows its logs, `0`
switches namespace and `:q` quits to a dead pane that `Ctrl-b :respawn-pane` brings back. **`loom-k9s`** is the
same screen as a command, for an `Alt-F2` console.

`Ctrl-b d` detaches and returns to the press-a-key prompt; the panes keep running, and the next keypress comes
straight back to them. `Alt-F2` through `Alt-F6` give a plain console with no session at all. Since no pane of
the session is a shell any more, that is both the way back in if anything above misbehaves **and** the ordinary
way to get a prompt — `loom-info`, `loom-k9s`, `loom-chat`, `loom-up` and `loom-down` are all on the `PATH`
there. `Alt-F1` returns to the session.

`loom-up` and `loom-down` wrap `up.sh` with the two flags the appliance needs:

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

**The login screen says `loom0 does not exist`.** The platform's interface match selected nothing, so the box
has no address and serves no DHCP or DNS. The warning is printed under the banner, above the press-a-key
prompt, and lists the interfaces that are present; rebuild the stick with `--interface <one of them>`. On the
EVO-X2, first just try the other ethernet port.

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
