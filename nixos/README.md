# `nixos/` — the Loom appliance

The declarative definition of a standalone Loom box, and of the USB stick that installs it.
User-facing documentation lives in [../Documentation/appliance.md](../Documentation/appliance.md);
this file is about the code.

## Files

| File | What it is |
| --- | --- |
| `default.nix` | Entry point. Takes `nixpkgs` and `nixosHardware` as arguments and returns the build targets. |
| `platform.nix` | Declares `loom.platform.*`: the per-box dimension, separate from `system`. |
| `platforms/spark.nix` | DGX Spark: aarch64, ConnectX-7. No upstream hardware profile exists. |
| `platforms/evo-x2.nix` | GMKtec EVO-X2: x86_64, Realtek 2.5GbE. Imports the nixos-hardware Strix Halo leaves, and sets the iGPU's GTT ceiling. |
| `platforms/nuc12.nix` | Intel NUC 12 Pro (Wall Street Canyon): x86_64, Intel 2.5GbE (`igc`). Imports `intel/nuc/12wshi7`. |
| `branding.nix` | Shared by box and stick: the name in the boot menu, the logo, the plymouth theme, `loom-eyes`, and the VT font — its size (`loom.consoleFont`), its glyph check, and the unit that re-applies it once the display has settled. |
| `box.nix` | The appliance: host tuning, toolchain, operator account, banner, `loom-up`. |
| `console.nix` | What the operator meets: the press-a-key login, the three-pane session (the log-to-`k9s` handover, and `loom-chat` on the cluster's Ollama), `/dev/console`. No pane is a shell; `Alt-F2` is. |
| `box-hardware.nix` | LUKS root, filesystems, initrd, bootloader — including why the menu timeout stays at 30s. |
| `key-guard.nix` | Watches the USB key while the box runs and powers it off when the key leaves. |
| `modes.nix` | `loom.mode`, the run/setup services, the `first-time-setup` specialisation, and `loom-promote-boot-entry`. |
| `network.nix` | Static address and dnsmasq in run mode, DHCP client in setup mode, the `--wifi` bridge, radios off. Also the `loom0` rename and the fallback that claims a wired NIC when no platform matches. |
| `wifi.nix` | The optional access point: `loom.wifi.*`, hostapd, and the check that says so on the console when the radio never came up. |
| `usb-ingest.nix` | Mounts USB media read-only and ingests it: the udev rule, the templated unit, and the filesystem set. |
| `usb-ingest/` | The program that unit runs — device selection, mount policy, naming, `mc mirror` — with its own pytest suite, run at build time. |
| `vm.nix` | VM-only overrides for the `boxVm` target: what to take off the appliance so it can be booted on a workstation. Never in the flashed closure. |
| `vm-serial.nix` | A getty on `ttyS0`, so a VM's console session can be reached from a terminal that copies and pastes. Never on a real stick; see `--serial` below. |
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `storage.nix` | `loom.storage.*`: the volume group, the logical volume and the device path stage 1 waits for — named once, for both the box and the stick. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer-scripts/` | `common.sh` (device interlock, the auto-install decision, console styling), `install.sh`, `wipe.sh`, `menu.sh`, and a bats suite run at build time. |
| `tests/appliance-hardware.nix` | Not a VM test: asserts what nixos-hardware gives each platform, and that the Loom overrides still take the desktop userspace back off — in the installer's closure as well as the box's. |
| `tests/appliance.nix` | VM test asserting the values `box.nix` restates from `up.sh`, and the console session. |
| `tests/appliance-wifi.nix` | VM test for the `--wifi` build: hostapd on a `mac80211_hwsim` radio, the bridge, and the credentials on the login screen. |
| `tests/appliance-interface-fallback.nix` | VM test for the box no platform matches: one NIC, two NICs, and the fallback switched off. |
| `tests/appliance-usb-ingest.nix` | VM test for USB ingest: real filesystems on scratch disks, and above all that the key stick is never touched. |
| `tests/appliance-install.nix` | VM test for the disk layout: the pool over scratch disks, the container where stage 1 expects it, the reinstall guard, and that the wipe still reaches the key material. |

## Why `default.nix` and not a flake

Two reasons, either one sufficient:

- **Flake inputs strip `.git`.** `up.sh`'s offline mode runs `git describe --exact-match --tags HEAD`
  (`up.sh:236`) inside the embedded checkout. `builtins.path` copies a directory verbatim; flake `path:`
  inputs do not.
- **One nixpkgs pin.** `devenv.lock` plus the `# renovate:` comments in `devenv.yaml` already govern
  nixpkgs, and `cicd/sync_devenv_renovate.sh` only knows about `devenv.lock`. A second lockfile here
  would drift.

The `build-appliance-image` devenv script passes devenv's `inputs.nixpkgs-stable` to
`cicd/build_appliance_image.sh` as `--nixpkgs`, which forwards it as `--arg nixpkgs`.
`inputs.nixos-hardware` takes the identical route as `--nixos-hardware` / `--arg nixosHardware`, and so
does `appliance-test` via `cicd/run_appliance_tests.sh`. Both arguments are **required** — there is no
`null` fallback, because a closure built without one would evaluate perfectly and quietly produce a
different box from every other stick.

## Why nixos-hardware, and what is forced back off

Two of the three platforms are covered upstream, and the coverage is uneven enough to be worth stating:

| Platform | Upstream | Effect |
| --- | --- | --- |
| `nuc12` | `intel/nuc/12wshi7` — literally this box, down to the chassis letter | `thermald`, and `i915` in the initrd |
| `evo-x2` | no EVO-X2; the `common/*` Strix Halo leaves that `framework/desktop/amd-ai-max-300-series` is built from | `amd_pstate=active`, and `amdgpu` in the initrd |
| `spark` | **nothing.** No GB10, Grace or Tegra content exists upstream (issue #303) | — |

`evo-x2` imports the leaves rather than the Framework profile on purpose: that profile also pulls
`framework/framework-tool.nix`, which installs `pkgs.framework-tool` on a GMKtec box.

The early-KMS half is the part worth having beyond the obvious: it gets the console onto the panel's own
mode from stage 1 instead of a firmware framebuffer, which is what `box-hardware.nix`'s
`consoleMode = "max"` and `branding.nix`'s banner-repaint unit are both working around.

Everything else upstream sets assumes a desktop session, so each x86 platform forces it back off —
`hardware.graphics.extraPackages`, `extraPackages32` and `enable32Bit`. There is no X, no Wayland and no
32-bit anything here, and the ROCm userspace Ollama needs lives inside `ollama/ollama:rocm`. The override
lands in the **installer's** closure as well as the box's, because `evalConfig` gives the platform module
to both — which is also why no restructuring of `default.nix` was needed to keep the stick lean.

`nixos-hardware` has **no release branches** and tracks nixos-unstable while this builds against
`nixos-26.05`, and nothing in CI builds this image. `tests/appliance-hardware.nix` is the tripwire: it
reads the evaluated configuration, costs seconds, needs no KVM, and runs for any platform on any host.
Run it after every renovate bump of the pin.

## The two axes: `system` and `platform`

`system` is the architecture; `platform` is the box. They are deliberately separate — two platforms could
share an architecture, and most of what actually differs between the Spark and the EVO-X2 (which NIC to
claim, which initrd modules to add) is a property of the machine.

`platform` defaults to `spark`, so every pre-existing invocation behaves as before. Each platform declares
the `nixSystem` it belongs to, and `default.nix` asserts it against `system`, so a mismatch fails during
evaluation with a readable message rather than producing a box that will not boot. An unknown platform name
lists the valid ones.

Adding another box means one file under `platforms/`, one entry in the `platformModules` table in
`default.nix`, and one case each in `platform_system()` and `platform_gpu()` in
`cicd/build_appliance_image.sh`. If nixos-hardware carries a profile for it, that file also imports it
from the `nixosHardware` argument and adds a branch to `tests/appliance-hardware.nix`; if it does not —
as with the Spark — it imports nothing, and that is the ordinary case rather than an omission.

### `gpuVendor`, and what follows from it

A platform declares `gpuVendor = "amd"` (or `"nvidia"`, unused so far) when somebody has confirmed the box
both binds the kernel driver *and* enumerates the device through the vendor's compute stack. The driver alone
proves nothing — every platform here loads one, since that is what puts the installer menu on the monitor.

Three things follow, and only the first is obvious:

- `modes.nix` passes `--gpus <vendor>` to `up.sh`, in both boot modes.
- `box.nix` adds the vendor's SMI tool to `loom.toolchain`, because `up.sh` refuses to run without it once
  `--gpus` is set. `tests/appliance.nix` asserts this, so declaring a vendor and forgetting the tool fails in
  CI rather than on the box.
- `runsAiServices` defaults to `gpuVendor != null`, so a CPU-only platform also drops Ollama and open-webui.
  That is deliberate: the embedding step runs over every indexed file, and on a CPU the queue never drains.

`build-appliance-image --no-gpu` forces the vendor back to `null` through an `mkForce` in `default.nix`, which
is why nothing else has to know the flag exists. Note that it takes the AI services with it, by the same rule.

## `loom0`, and the two things that can produce it

A platform's `netMatch` is a **driver** match, applied by a `.link` file. That is the fast path and the one
every supported box takes.

It is not the only path, because a driver match is exactly as narrow as it sounds: an image installed on
hardware nobody wrote a platform for renames nothing, and a box with no `loom0` has no address, no DHCP and
no `*.loom`. There is no sshd and no `nixos-rebuild` to fix that with, so the only recovery was building
another stick. `loom-interface-fallback` closes that: when the match selected nothing, it picks a wired NIC
itself and renames it before `network-pre.target`, which puts it ahead of every address, bridge and dnsmasq
unit without naming any of them.

Two things about it are worth knowing before changing it.

**It picks rather than refuses when there are several.** That looks reckless and is the opposite:
`platforms/evo-x2.nix` already makes the argument, because both its Realtek ports match `r8169` and udev
decides between them. A box that came up on the wrong port is fixed by moving the cable. A box with no
`loom0` at all is not fixable at the console. Picking is strictly the better failure, and the pick is by PCI
path so it is at least the same port on every boot.

**`--interface` is applied by the same unit, not by the `.link` file**, even though the `.link` file still
carries an `OriginalName` match for it. `OriginalName=` matches the udev `INTERFACE` property *while* the
link policy is being decided — which is the kernel's `eth0`. The predictable name an operator actually reads
off the box, `enp2s0`, is the *output* of that decision, produced by `NamePolicy` in `99-default.link`, which
sorts after ours. So `--interface enp2s0` matched nothing and produced a box with no `loom0` — the exact
failure the flag exists to prevent. Applying it at runtime, after udev has settled, is what makes the name an
operator can discover the name that works.

`loom.autoSelectInterface` turns the automatic half off; the explicit `--interface` half runs regardless,
because naming a port is an instruction rather than a guess. `tests/appliance.nix` sets it false, since it
asserts a VM comes up *without* `loom0`; `tests/appliance-interface-fallback.nix` is where the behaviour is
actually tested.

## Building by hand

Normally you would use `build-appliance-image`. To drive it directly:

```bash
NIXPKGS=...                        # a nixpkgs checkout
NIXHW=...                          # a nixos-hardware checkout
HOSTS=$(source ./vars.sh && printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" | jq -R . | jq -sc .)

# Evaluate only -- catches most mistakes in seconds, for any platform,
# without the corresponding hardware.
nix-instantiate ./nixos -A box \
  --arg nixpkgs "$NIXPKGS" --arg nixosHardware "$NIXHW" \
  --argstr system x86_64-linux --argstr platform evo-x2 \
  --arg repoSrc ./. --argstr tag dev --argstr loomHostsJson "$HOSTS"

# A bootable VM of the appliance, to poke at by hand. `appliance-vm box` wraps
# this with a state directory, port forwards and a serial socket -- see below.
nix-build ./nixos -A boxVm --argstr system x86_64-linux --argstr platform evo-x2 ...
./result/bin/run-*-vm

# The stick image.
nix-build ./nixos -A installerImage ...
```

Both store paths are in `devenv.lock`; the devenv scripts pass them for you, and
`nix flake metadata --json github:NixOS/nixos-hardware/<rev>` resolves one by hand.

Targets: `box`, `boxVm`, `installerImage`, `tests.appliance`, plus `boxSystem` and `installerSystem`
for poking at evaluated configuration.

## Booting one by hand

The tests answer questions you can write down in advance. `appliance-vm` is for the other kind —
what the console session actually looks like, whether the installer menu reads the way it should,
what happens when you pull the key stick — on a workstation with no appliance hardware near it.

```bash
appliance-vm box                    # fast: the appliance closure, no tag, no image
appliance-vm installer              # the real stick image, flashed onto a file, booted under UEFI
appliance-vm installer --serial     # ...and reachable from a terminal that copies and pastes
appliance-vm attach                 # connect to a running VM's serial port
appliance-vm reset                  # throw this platform's disks and stick away
```

Both VMs refuse to cross-build, for the reason the tests do: a VM boots a real kernel.

| | `box` | `installer` |
| --- | --- | --- |
| Boots | the closure, through nixpkgs' qemu-vm runner | the stick image, through UEFI |
| Needs a tag | no | yes — `up.sh`'s offline mode wants one |
| Console session, branding, units | yes | yes |
| Bootloader, boot menu, specialisation | no | yes |
| LUKS root, the key stick, the key guard | no | yes |
| The installer itself | no | yes |
| Survives a reboot | yes | yes |
| Time to first screen | a minute | an image build, then a minute |

`box` is the loop to iterate in. What it cannot show you is everything below the disk: nixpkgs'
`qemu-vm.nix` replaces `fileSystems` wholesale and clears `boot.initrd.luks.devices` (both
`mkVMOverride`), so the LUKS root, the partlabel mounts and systemd-boot are all out of frame.
`nixos/vm.nix` takes three more things off — the interface fallback, the static address and dnsmasq
— because otherwise the box claims the VM's only NIC as `loom0` and there is no route back to the
host. Each of the three has a test of its own; none of them is going unexercised.

### Why the installer rig can exist at all

`tests/appliance-install.nix` says the image "is deliberately not booted. It wants an NVMe the test
framework cannot supply". qemu can supply one. `target_disks` (`installer-scripts/common.sh`) wants
`/dev/nvmeXn1`, non-removable, and not the disk it booted from — `-device nvme` with the stick on
`usb-storage` satisfies all three, so the real `install.sh` runs against a real pool.

Flashing onto a file needs no root either: it is the same two steps `build_appliance_image.sh`
performs on a stick — write the image, then write 4096 bytes of key into the `loom-key` partition —
and `sfdisk --json` reads a partition table out of an ordinary file. The firmware keeps its own
variables in the state directory, so the `Loom appliance` entry `fix_boot_order` writes at install
time is still there on the next boot.

State lives in `.appliance-vm/<platform>/` and is gitignored: two sparse qcow2 disks, the flashed
stick, the UEFI variables and the two qemu sockets. Sparse is what makes the 250 GB `check_pool_size`
demands free — a full install writes a few gigabytes.

Pull the key stick from the qemu monitor to watch the key guard fire; `appliance-vm` prints the two
commands on every run.

### `--serial`, and what it costs

`console.nix` gates the console session on `$(tty)` being `/dev/tty1`, so a serial login lands in a
plain shell. The way in is the socket: `loom.consoleSocket` is a fixed path precisely so the tmux
server survives a logout, and `nixos/vm-serial.nix` has the serial login run `loom-console -d` —
attaching to the very session tty1 is showing, as the only client. `-d` because tmux sizes a window
to its smallest client, and `loom-btop` has already picked its box set from the pane it started in.
The ping-pong is deliberate: pressing ENTER on tty1 takes the session back.

Two things in that module are load-bearing and neither is obvious:

- **The unit is instantiated with the template's `ExecStart` copied into it.** systemd collects
  drop-ins by *basename*, and every drop-in NixOS generates is `overrides.conf`, so an instance-level
  one replaces the template-level one rather than merging with it. The file it replaces is nixpkgs'
  own `serial-getty@` override — the one carrying the real `agetty` path and the appliance's
  `--autologin` / `--login-pause` arguments. Masked, the unit falls back to upstream's
  `ExecStart=-/sbin/agetty`, which on NixOS is nothing at all: agetty exits with `Unable to locate
  executable '/usr/bin/agetty'`, systemd restarts it about eight times, the start limit stops it for
  good, and anyone attaching later finds a dead port and no explanation outside the guest's journal.
- **The login negotiates its own window size.** A serial line carries no size and delivers no
  SIGWINCH, so agetty assumes 80×24; tmux splits that into panes of about 39×23, and `loom-btop`
  needs 60×8 for even its smallest box set, so the monitoring pane comes up saying "Terminal size too
  small" instead of drawing. The login therefore does what xterm's `resize` does — park the cursor
  past the bottom right, ask where it stopped, `stty` the answer — with the terminal briefly out of
  canonical mode, because the reply carries no newline and a line-buffering discipline would never
  hand it over.

What this deliberately does not do is set `console=`. `console.nix` rejects that outright — a serial
port named there becomes the *primary* console, so a panic on a box with nothing plugged into it goes
nowhere at all — and `tests/appliance.nix` asserts `fgconsole` is 1 so it cannot come back. A getty
is not a console: tty1 stays foreground and the installer menu keeps the `TTYPath = /dev/tty1` that
`installer.nix` gives it.

`box` always has the getty, because nixpkgs' runner already puts `console=ttyS0 console=tty0` on the
command line there — tty0 last, so still primary — and copies the boot log to both. The installer rig
boots the image's own command line, so there `--serial` is an opt-in that adds one unit the shipped
image does not have. `build-appliance-image --vm-serial` is how it gets there, and it refuses
`--flash`: that image is for a VM, not for a stick.

Serial shows no firmware, no boot menu and no splash. To copy text off the graphical console anyway,
read it as text the way `tests/appliance-wifi.nix` does:

```bash
cat /dev/vcsa1        # tty1's screen contents, from a serial shell
```

## Running the tests

```bash
appliance-check                     # everything that boots nothing, about a minute
appliance-test                      # all of them, cheapest first
appliance-test wifi usb-ingest      # or by name
```

`appliance-check` is the cheap half, and the half that runs in CI on every pipeline. It boots
nothing, so it needs neither KVM nor a host of the platform's architecture. Three checks, and
`appliance-check eval` (or `bats`, or `pytest`) runs one of them:

| Check | What it does |
| --- | --- |
| `eval` | Instantiates `installerImage` for every platform — which covers the appliance too, since `installer.nix` puts its toplevel in the stick's store image — plus `tests` for this one. Catches a module that no longer evaluates, a renamed option, a failed assertion, and a typo in a test file that would otherwise surface twenty minutes into a VM boot. |
| `bats` | `nixos/installer-scripts/tests`, the `auto_install_decision` truth table. |
| `pytest` | `nixos/usb-ingest/tests`, the name sanitiser, the filesystem table and the exclusion rules. |

Both suites also run inside the derivations that own them — `bats` in `installerScripts`, `pytest`
in the `loom-usb-ingest` `checkPhase` — so a mistake fails an image build as well. Running them
here costs a second instead of a closure.

`appliance-test` is the other half: the six short names and what each is for:

| Name | Attribute | What it asserts |
| --- | --- | --- |
| `hardware` | `tests.applianceHardware` | What nixos-hardware gives this platform, and that the Loom overrides still take the desktop userspace back off. **Not a VM test** — see below. |
| `appliance` | `tests.appliance` | The values `box.nix` restates from `up.sh` and `vars.sh`, the console session, and the key guard. |
| `install` | `tests.applianceInstall` | The disk layout: the pool, the container where stage 1 expects it, and the wipe. |
| `wifi` | `tests.applianceWifi` | The `--wifi` build, which `tests.appliance` deliberately does not cover: it forces off dnsmasq and the static addresses that this one exercises. |
| `usb-ingest` | `tests.applianceUsbIngest` | Scratch disks carrying real filesystems, and the exclusion rules — above all that the LUKS key stick is never touched. |
| `interface-fallback` | `tests.applianceInterfaceFallback` | The box no platform matches: one NIC, two NICs, and the fallback switched off. |

The script picks the platform matching the host architecture, passes the `*.loom` host list, the
namespace and the chat model from `vars.sh` — `tests/appliance.nix` asserts the appliance restates
those correctly, so defaults would fail the test for the wrong reason — and asks nix to collect
garbage rather than run the disk out (see **Disk budget** below). `--platform`, `--min-free`, `--gc`,
`--nixpkgs` and `--nixos-hardware` are the flags; `appliance-test --help` lists them.

`hardware` is the exception to everything in this section. It boots nothing — it reads the evaluated
configuration and exits — so it does not need KVM, does not build the appliance closure, and is not
bound to the host's architecture. It therefore runs first, and a selection made up only of it lifts the
cross-architecture refusal:

```bash
appliance-test hardware --platform spark      # works on an x86_64 workstation
appliance-test hardware --platform all        # or all three at once
```

That is the one to run after a renovate bump of the `nixos-hardware` pin: all three platforms checked
from one machine, in seconds. `--platform all` is refused for any selection that includes a VM test,
which has to boot the kernel it built.

Underneath it is one `nix-build` per target, which is still the way to run one by hand:

```bash
NIXPKGS=...                        # a nixpkgs checkout
NIXHW=...                          # a nixos-hardware checkout
HOSTS=$(source ./vars.sh && printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" | jq -R . | jq -sc .)

nix-build ./nixos -A tests.appliance \
  --arg nixpkgs "$NIXPKGS" --arg nixosHardware "$NIXHW" \
  --argstr system x86_64-linux --argstr platform evo-x2 \
  --arg repoSrc ./. --argstr loomHostsJson "$HOSTS" \
  --no-out-link
```

The pure logic behind `usb-ingest.nix` -- the name sanitiser, the filesystem table and the exclusion
rules -- is not tested in that VM. It is a pytest suite under `usb-ingest/tests/`, run in the package's
`checkPhase`, so a mistake there fails the build in seconds rather than at boot. `nix-build ./nixos -A box`
is enough to run it, and `appliance-check pytest` runs it with nothing built at all.

The installer scripts have the same arrangement, for the same reason: `auto_install_decision` in
`installer-scripts/common.sh` decides whether a disk is destroyed with nobody watching, so its truth table
is a bats suite under `installer-scripts/tests/`, run in the scripts' own derivation. `nix-build ./nixos -A
installerImage` runs it -- as does `appliance-check bats`, or `bats nixos/installer-scripts/tests`.

There is one evaluation per invocation and no `forAllSystems`, so covering both platforms means running it
twice — and each run needs a host of the matching architecture, since the test boots a real VM. In practice
that is `evo-x2` on any x86_64 workstation and `spark` on a Spark. `hardware` is exempt, as above: it boots
nothing, so all three platforms are reachable from whichever machine you have.

Wants a host with KVM, and says so: `appliance-test` probes `/dev/kvm` and prints `kvm=true` or
`kvm=false` with each target it starts. `--kvm` makes a machine without it an error instead; `--no-kvm`
forces the slow path on a machine that has it, which is the only way to rehearse what a runner does.

What "without KVM" actually drops is one line of scheduling. nixpkgs starts qemu with
`-machine accel=kvm:tcg`, so it falls back to software emulation by itself, and the test driver never
opens the device — the thing that refuses is nix, which will not run a derivation asking for a system
feature the builder does not advertise. So the fallback is to stop asking, which is what
`requireKvm = false` does in `default.nix`, and nothing else about the build changes: only
`requiredSystemFeatures` differs, every input is identical, and the closure is shared with a KVM run.
Five to ten times slower, and it runs.

```bash
nix-build ./nixos -A tests.appliance --arg requireKvm false ...   # what --no-kvm passes
```

## In CI

Two jobs in `.gitlab-ci.yml`, split along the same line as the two scripts:

- `appliance_check` runs `appliance-check` and `appliance-test hardware --platform all` on every
  pipeline. Neither needs KVM nor a matching architecture, so it runs on any runner, and it is the
  only coverage the Spark image gets there — the runners are all x86_64.
- `appliance_test` runs the VM tests on `evo-x2`, and is the one job in that file gated with
  `rules: changes:` — `nixos/**/*`, `cicd/run_appliance_tests.sh`, `vars.sh`, `up.sh`, `devenv.nix`
  and `devenv.lock`. It holds a shared runner for minutes with KVM and potentially hours without, and
  those are the files that can change what it asserts. A path missing from that list is what
  `appliance_check` is there to catch; outside a merge request the job is `when: manual`, because
  GitLab counts every file as changed on a tag or a new branch.

`appliance_check` prints one line naming the runner's architecture, whether `/dev/kvm` is usable and
the free space on the store. That line is how the KVM question gets answered for a runner nobody can
log into.

## Disk budget

A run costs disk in two ways, and both land on the filesystem holding `/nix`:

- **The closure.** Each target builds a whole appliance system — around 3.5 GB, because `box.nix`
  carries up.sh's entire toolchain (docker, minikube, skaffold, helm) alongside a kernel and an
  initrd. Most of that is shared between runs and between targets, but an edit to anything under
  `nixos/` rebuilds a few hundred megabytes and re-copies the checkout that `loomSrc` embeds
  (~120 MB from a working tree, filtered — `nixos/` is inside the tree being copied), every time,
  and nothing reclaims the previous one.
- **The VM disks.** The test framework writes each node's qcow2 into the Nix *build* directory —
  `/nix/var/nix/builds` on Nix 2.2x and later, `$TMPDIR` before that. Not `/tmp`, on either.
  `virtualisation.diskSize` is a cap on a sparse file, so the cost is what the guest writes, not the
  number in the test, and that turns out to be small:

| Test | Nodes | Written by the guest |
| --- | --- | --- |
| `appliance` | 1 | 165 MB — the heaviest, and mostly the key guard's loop images |
| `install` | 1 | the two 2 GB scratch disks it partitions, sparsely |
| `wifi` | 1 | 19 MB |
| `usb-ingest` | 1 | 28 MB, plus four 256 MB scratch disks it puts filesystems on |
| `interface-fallback` | 3 | 20 MB each |

A whole five-target run moved this host's free space by **2.8 GB**, nearly all of it closure and
none of it VM disks. The guest's own `/nix/.rw-store` is a tmpfs, so what a node writes to the store
costs RAM, not disk.

Nix frees none of it on its own unless it is told to. On NixOS:

```nix
nix.gc = {
  automatic = true;
  dates = "weekly";
  options = "--delete-older-than 14d";
};
nix.settings.min-free = 25 * 1024 * 1024 * 1024;
nix.settings.max-free = 100 * 1024 * 1024 * 1024;
nix.optimise.automatic = true;
```

Anywhere else — Debian, Fedora, macOS, a CI runner — the same two settings belong in
`/etc/nix/nix.conf`, and a timer or cron job covers the scheduled half:

```ini
min-free = 26843545600
max-free = 107374182400
```

`min-free` is the one that keeps a run from dying at a full disk: the daemon collects garbage
*during* the build once free space drops below it. `appliance-test` also passes both on the command
line, which nix honours only for a user in `trusted-users`; everyone else gets a warning and the
daemon's own settings, which is why the permanent form is worth setting anyway.

A CI job is the case where the command line is enough. The `nix-dind` image puts its `nix` user in
`trusted-users`, `/nix` there is the container's own writable layer — no volume, no quota, shared with
nothing and surviving nothing — and the job therefore passes a far smaller margin than a workstation
wants: `--min-free 10 --max-free 20`. Collecting to 100 GB free in a container would delete the devenv
closure the next step needs.

To reclaim by hand:

```bash
nix-collect-garbage          # unreachable store paths
nix-collect-garbage -d       # ...and old profile generations
nix store optimise           # hardlink identical files
```

An interrupted run leaves its build sandbox behind as `/nix/store/<drv>.chroot`, still holding that
run's disk images. A garbage collection clears those too.

## Keeping in sync with `up.sh`

`box.nix` restates things that live in `up.sh` and `vars.sh`:

- the eight sysctls from `setup_system` (`up.sh:616-684`)
- the `*.loom` host list, generated from `vars.sh` at build time rather than copied
- every binary `up.sh` needs — the `validate_environment` list (`up.sh:402-428`), plus the `awk` it pipes
  through at `up.sh:380` above those checks, plus the `tar` and `mktemp` that `cicd/skaffold` reaches for
- `NAMESPACE`, passed through the same way the host list is and consumed by `console.nix`'s `k9s` view
- `LOOM_CHAT_MODEL`, the same route again, consumed by `console.nix`'s `loom-chat` pane. It has a harder
  constraint than the rest: it must name a model `ollama/Dockerfile` bakes into the production image, because
  an air-gapped box cannot pull one, and it should match `_llmDefaults.model` in `charts/values.yaml` so the
  pane does not make Ollama evict the model the workers are indexing with.

`tests/appliance.nix` asserts all five, so a change on either side is caught rather than shipped. If you
add a `check_command` to `up.sh`, add the package to `loom.toolchain` in `box.nix` and the name to the test.

`loom.toolchain` is one list on purpose. It feeds both `environment.systemPackages` and the `path` of the
units in `modes.nix`, because a unit's PATH is built solely from its own `path` plus a minimal default
(coreutils, findutils, gnugrep, gnused, systemd) — `/run/current-system/sw/bin` is never on it. When the
two were maintained separately they drifted, and the box shipped with a `loom.service` that died on
`awk: command not found` while the same command worked fine in the operator's shell. For the same reason
the test resolves each binary against `loom.service`'s own PATH rather than the login shell's.

## Which boot entry a box comes up on

A fresh box has to boot `Loom (first-time-setup)`; a box that has finished setup must never boot it again. Both
ends are automatic, and they use **different mechanisms** — which looks inconsistent until you read the
bootloader builder.

`systemd-boot-builder.py` decides the default entry like this:

```python
is_default = Path(bootspec.init).parent == Path(args.default_config)
...
if is_default:
    write_loader_conf(*gen)          # no specialisation argument
```

`is_default` is only ever compared against the **main** toplevel, and `write_loader_conf` is called with the
generation alone. So `default` can only name `nixos-generation-<N>.conf`. Passing a specialisation's toplevel
as `DEFAULT-CONFIG` does not select it — it matches nothing, and loader.conf is never written at all. (A newer
builder in nixpkgs does support this. The appliance does not use that one; it builds against devenv's
`inputs.nixpkgs-stable`.)

Hence:

- **Into setup**, `install.sh`'s `select_setup_entry` writes the `default` line itself. The filename it writes
  is derived, not guessed: the builder's own `generation_conf_filename` composes
  `nixos-generation-<N>-specialisation-<name>.conf`, so the name is the run entry's with a suffix. The
  specialisation's name comes from `/etc/loom/setup-specialisation`, which `installer.nix` reads off the
  evaluated configuration — a rename in `modes.nix` follows through instead of drifting, and an extra
  specialisation fails the build rather than being picked arbitrarily.
- **Back to run mode**, `loom-promote-boot-entry` (`modes.nix`) can just use the builder, because the run
  closure *is* the main toplevel. It then deletes the specialisation entry and checks what it leaves behind:
  one entry, and `default` naming it.

Both rest on the same property: **nothing re-runs the bootloader builder on an installed box.** There is no
`nixos-rebuild`, no channel and no evaluation there, so a hand-written `default` and a deleted entry both stay
put. A reinstall runs the builder again and correctly restores both.

`Reboot Into Firmware Interface` is synthesised by systemd-boot rather than stored in `loader/entries`, so the
deletion cannot reach it. The glob is scoped to `nixos-generation-*-specialisation-*.conf` anyway, which makes
that true by construction rather than by luck.

## One pool, one container

Every eligible internal NVMe is concatenated into a single volume group, and the LUKS container sits on the
logical volume that fills it. That is the inverse of the usual NixOS recipe, and the reason is the invariant
this whole directory is built around: **one system closure serves every box.**

`boot.initrd.luks.devices` is static configuration, but how many M.2 slots a box has populated is not known
when that closure is built. LVM-inside-LUKS would need one `luks.devices` entry per disk, and a one-disk box
booting a two-entry closure blocks in stage 1 forever on a `.device` unit that never appears. Pooling first
leaves exactly one container, one keyslot, one recovery passphrase and one device path — for one disk or for
three. It also removes the only question the installer used to have to ask, which is what lets it run
unattended.

Nothing has to be enabled for it to boot. nixpkgs' `luksroot.nix` sets `services.lvm.enable` and
`boot.initrd.services.lvm.enable` unconditionally whenever any LUKS device is declared, so lvm2's udev rules
and binaries are already in the appliance's initrd and event-based autoactivation brings the volume up before
`systemd-cryptsetup` asks for it.

The names live in `storage.nix` and nowhere else. `key-guard.nix` takes `rootDevice` from there (and
`box-hardware.nix` from `key-guard.nix`, as it already did), and `installer.nix` passes the same three values
to the stick's scripts through `wrapProgram` — the same trick it uses for the setup specialisation. So the
installer cannot create a volume the box will not look for. Keep both names free of dashes: LVM escapes `-`
as `--` in `/dev/mapper`, and `rootDevice` does not.

## The USB key, in two places

Stage 1 needs the key to unlock the root; `key-guard.nix` needs the same key, on the same device, for as
long as the box runs. So `loom.keyGuard.keyDevice`, `.rootDevice` and `.keyBytes` are options declared in
`key-guard.nix` and consumed by `box-hardware.nix`, rather than two copies of `loom-key`, `loom-root-luks`
and `4096`. A box whose initrd and whose guard disagreed about which device is the key would boot perfectly
and then power itself off ten seconds later, which is not a failure anybody would enjoy diagnosing in the
field. The same three options are what let `tests/appliance.nix` point the guard at loop devices.

`loom.keyGuard.action` follows `loom.progressUnit`: declared here, set in `modes.nix` next to the mode it
belongs to — `poweroff` in run mode, `warn` in first-time setup. `loom.consoleSocket` is the same idea in
the other direction: `console.nix` owns the operator's tmux session, and the guard writes its countdown
into it.

The stick side of the same numbers lives in `installer-scripts/common.sh` (`LOOM_KEY_BYTES`, the partition
labels) and in `cicd/build_appliance_image.sh` (`KEY_BYTES`, `KEY_PARTLABEL`). Those cannot share the Nix
options — they run from the stick, before any of this exists — so they are the one pair that still has to
be kept in step by hand.

### Why USB ingest asks the guard rather than udev

`usb-ingest.nix` has to know which disk is the key, and the obvious answer —
`/dev/disk/by-partlabel/loom-key` — is the wrong one, for the reason stated above: that path is not unique,
and with two Loom sticks attached it resolves to whichever udev linked last. Ingesting the key stick because
a *second* stick shadowed the symlink would power the box off ten seconds later.

So the exclusion reads `/run/loom/key-guard/device` instead. That file holds the node the guard armed on,
and it got there by opening the LUKS header with `--test-passphrase` — proof that this stick unlocks *this*
disk, which no symlink can give. `loom.keyGuard.stateDir` is already an option for the same reason the
banner reads it: one path, not three copies.

The fallback matters too. A box booted on the recovery passphrase never arms, so there is no proven key
device, and the ingest service drops back to refusing any disk carrying a Loom partition label. That is
weaker — it is the very thing the guard exists to improve on — so the console says so when it happens.
