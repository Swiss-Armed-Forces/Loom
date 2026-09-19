# `nixos/` — the Loom appliance

The declarative definition of a standalone Loom box, and of the USB stick that installs it.
User-facing documentation lives in [../Documentation/appliance.md](../Documentation/appliance.md);
this file is about the code.

## Files

| File | What it is |
| --- | --- |
| `default.nix` | Entry point. Takes `nixpkgs` as an argument and returns the build targets. |
| `platform.nix` | Declares `loom.platform.*`: the per-box dimension, separate from `system`. |
| `platforms/spark.nix` | DGX Spark: aarch64, ConnectX-7. |
| `platforms/evo-x2.nix` | GMKtec EVO-X2: x86_64, Realtek 2.5GbE. |
| `platforms/nuc12.nix` | Intel NUC 12 Pro (Wall Street Canyon): x86_64, Intel 2.5GbE (`igc`). |
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
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `storage.nix` | `loom.storage.*`: the volume group, the logical volume and the device path stage 1 waits for — named once, for both the box and the stick. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer-scripts/` | `common.sh` (device interlock, the auto-install decision, console styling), `install.sh`, `wipe.sh`, `menu.sh`, and a bats suite run at build time. |
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

`cicd/build_appliance_image.sh` passes devenv's `inputs.nixpkgs-stable` through as `LOOM_NIXPKGS`.

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
`cicd/build_appliance_image.sh`.

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
export LOOM_NIXPKGS=...            # a nixpkgs checkout
HOSTS=$(source ./vars.sh && printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" | jq -R . | jq -sc .)

# Evaluate only -- catches most mistakes in seconds, for either platform,
# without the corresponding hardware.
nix-instantiate ./nixos -A box \
  --arg nixpkgs "$LOOM_NIXPKGS" \
  --argstr system x86_64-linux --argstr platform evo-x2 \
  --arg repoSrc ./. --argstr tag dev --argstr loomHostsJson "$HOSTS"

# A bootable VM of the appliance, to poke at by hand.
nix-build ./nixos -A boxVm --argstr system x86_64-linux --argstr platform evo-x2 ...
./result/bin/run-*-vm

# The stick image.
nix-build ./nixos -A installerImage ...
```

Targets: `box`, `boxVm`, `installerImage`, `tests.appliance`, plus `boxSystem` and `installerSystem`
for poking at evaluated configuration.

## Running the test

```bash
nix-build ./nixos -A tests.appliance \
  --argstr system x86_64-linux --argstr platform evo-x2 ...

# The --wifi build, which tests.appliance deliberately does not cover: it forces
# off dnsmasq and the static addresses that this one exists to exercise.
nix-build ./nixos -A tests.applianceWifi \
  --argstr system x86_64-linux --argstr platform evo-x2 ...

# USB ingest: scratch disks carrying real filesystems, and the exclusion rules.
nix-build ./nixos -A tests.applianceUsbIngest \
  --argstr system x86_64-linux --argstr platform evo-x2 ...

# The box no platform matches: one NIC, two NICs, and the fallback switched off.
nix-build ./nixos -A tests.applianceInterfaceFallback \
  --argstr system x86_64-linux --argstr platform evo-x2 ...

# The disk layout: the pool, the container where stage 1 expects it, and the wipe.
nix-build ./nixos -A tests.applianceInstall \
  --argstr system x86_64-linux --argstr platform evo-x2 ...
```

The pure logic behind `usb-ingest.nix` -- the name sanitiser, the filesystem table and the exclusion
rules -- is not tested in that VM. It is a pytest suite under `usb-ingest/tests/`, run in the package's
`checkPhase`, so a mistake there fails the build in seconds rather than at boot. `nix-build ./nixos -A box`
is enough to run it.

The installer scripts have the same arrangement, for the same reason: `auto_install_decision` in
`installer-scripts/common.sh` decides whether a disk is destroyed with nobody watching, so its truth table
is a bats suite under `installer-scripts/tests/`, run in the scripts' own derivation. `nix-build ./nixos -A
installerImage` runs it -- as does `bats nixos/installer-scripts/tests`, which needs nothing built at all.

There is one evaluation per invocation and no `forAllSystems`, so covering both platforms means running it
twice — and each run needs a host of the matching architecture, since the test boots a real VM. In practice
that is `evo-x2` on any x86_64 workstation and `spark` on a Spark.

Needs a host with KVM. On one without nested virtualisation, drop the requirement and let qemu fall back
to software emulation — much slower, but it runs:

```nix
(import ./nixos { ... }).tests.appliance.overrideTestDerivation (_: {
  requiredSystemFeatures = [ "nixos-test" ];
})
```

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
builder in nixpkgs does support this. The appliance does not use that one; `LOOM_NIXPKGS` is devenv's
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
