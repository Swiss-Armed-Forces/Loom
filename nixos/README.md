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
| `console.nix` | What the operator meets: the press-a-key login, the three-pane session (the log-to-`k9s` handover, and `loom-chat` on the cluster's Ollama), `/dev/console`. No pane is a shell; `Alt-F2` is. Also `loom-pane`, which restarts a pane's program when it exits, the kiosk key policy and the clickable status-line controls. |
| `console-mouse.nix` | The mouse on a console that has none: `gpm`, the ordering that keeps its one-shot console measurement honest, and the `loom-console-mouse` package. See the section below. |
| `console-mouse/` | The pty shim `loom-console` runs the tmux client under — the gpm client protocol, SGR translation and the pointer sequencing — with its own pytest suite, run at build time. |
| `box-hardware.nix` | LUKS root, filesystems, initrd, bootloader — including why the menu timeout stays at 30s. |
| `key-guard.nix` | Watches the USB key while the box runs and powers it off when the key leaves. |
| `keymap.nix` | `--keymap`: the console keymap for the box, the installer and stage 1, and the build-time check that the name resolves. Inert when unset, which means US QWERTY. |
| `key-store.nix` | The `--lock-key` build: the stick's key inside a LUKS2 container, and the initrd unit that asks for its passphrase and unlocks it before the root is opened. Inert in every other image; see `--lock-key` below. |
| `modes.nix` | `loom.mode`, the run/setup services, the `first-time-setup` specialisation, and `loom-promote-boot-entry`. |
| `ready.nix` | How far the bring-up has got: the `loom-ready` package, and the unit that polls the cluster and publishes readiness for the three screens that draw it. Run mode only. |
| `ready/` | The program that unit runs — what counts as a workload, what counts as ready, the stage machine, the bar in the bring-up pane and the tmux status segment — with its own pytest suite, run at build time. |
| `network.nix` | Static address and dnsmasq in run mode, DHCP client in setup mode, the `--wifi` bridge, radios off. Also the `loom0` rename and the fallback that claims a wired NIC when no platform matches, and `loom-expose`, which DNATs the appliance address onto the minikube node instead of using `up.sh --expose`. |
| `wifi.nix` | The optional access point: `loom.wifi.*`, hostapd, and the check that says so on the console when the radio never came up. |
| `usb-ingest.nix` | Mounts USB media read-only and ingests it: the udev rule, the templated unit, and the filesystem set. |
| `usb-ingest/` | The program that unit runs — device selection, mount policy, naming, `mc mirror`, and the console pane the copy is drawn in — with its own pytest suite, run at build time. |
| `vm.nix` | VM-only overrides for the `boxVm` target: what to take off the appliance so it can be booted on a workstation. Never in the flashed closure. |
| `vm-serial.nix` | A getty on `ttyS0`, so a VM's console session can be reached from a terminal that copies and pastes. Never on a real stick; see `--serial` below. |
| `debug.nix` | The `--debug` build: an sshd keyed to one generated key, `loom-debug-bundle`, and the five places the box says what it is. Inert in every other image; see `--debug` below. |
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `storage.nix` | `loom.storage.*`: the volume group, the logical volume and the device path stage 1 waits for — named once, for both the box and the stick. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer/` | The three programs the stick runs — `loom-menu`, `loom-install`, `loom-wipe` — as one Python package: the device interlock, the auto-install decision, the console drawing (rich), and a pytest suite run at build time. |
| `scripts/platform_info.sh` | `loom-platform-info`: what the box actually is, next to what the platform file claims. Plain bash with no Nix dependency, because the box it most needs to run on is one that is not running Loom yet. |
| `tests/appliance-hardware.nix` | Not a VM test: asserts what nixos-hardware gives each platform, and that the Loom overrides still take the desktop userspace back off — in the installer's closure as well as the box's. |
| `tests/appliance.nix` | VM test asserting the values `box.nix` restates from `up.sh`, and the console session. |
| `tests/appliance-wifi.nix` | VM test for the `--wifi` build: hostapd on a `mac80211_hwsim` radio, the bridge, and the credentials on the login screen. |
| `tests/appliance-interface-fallback.nix` | VM test for the box no platform matches: one NIC, two NICs, and the fallback switched off. |
| `tests/appliance-usb-ingest.nix` | VM test for USB ingest: real filesystems on scratch disks, and above all that the key stick is never touched. |
| `tests/appliance-install.nix` | VM test for the disk layout: the pool over scratch disks, the container where stage 1 expects it, the reinstall guard, and that the wipe still reaches the key material. |
| `tests/appliance-key-store.nix` | VM test for the `--lock-key` build's key guard: it arms on a container rather than on a key it can test against the root, and still tells one stick from another. |
| `tests/appliance-debug.nix` | VM test for the `--debug` build: two nodes, and whether the generated key gets the second one in. The counterpart to `tests/appliance.nix`, which asserts no sshd for every other image. |
| `tests/scripts.nix` | The tests as a Python package, built for the test driver's own interpreter and installed through its `extraPythonPackages`. |
| `tests/scripts/` | The tests themselves (`loom_tests`), as Python the repository's own hooks lint and type-check. A module per test node, `vt.py` and `tmux.py` shared between them, `driver.py` the typing shim for what the driver hands them, and a pytest suite for the two helpers that parse something. |
| `../cicd/appliance_common.sh` | Sourced by all four appliance scripts (`build_appliance_image.sh`, `appliance_eval.sh`, `run_appliance_tests.sh`, `run_appliance_vm.sh`): `check_command`, the platform-to-architecture table `platform_system`, and `resolve_loom_values`, which reads the host list, the namespace and the chat model out of `vars.sh`. The table is the reason it exists — a fourth platform is one edit here, not four with nothing to catch a missed one. |

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

## The `poetry.lock` beside each Python package

`console-mouse/`, `installer/`, `ready/`, `usb-ingest/` and `tests/scripts/` are Poetry projects
like every other Python package in the repository — `poetry-core` build backend, a `poetry.lock` beside the
`pyproject.toml`, and `poetry-lock` regenerating them along with the rest.

Those lockfiles do **not** govern the appliance. `buildPythonApplication` resolves `rich` from the
pinned nixpkgs, so what a stick ships is whatever that pin carries, and the version in `poetry.lock`
is free to differ. Read them as a statement about the development environment, not the image.

What they are for is making the `pyproject.toml` beside them load-bearing. That manifest used to be
free to drift from the `dependencies` list in the `.nix` file — `ready/` and `usb-ingest/` both
imported `rich` while declaring no dependencies at all — because Nix supplied the import either way
and nothing else read the manifest. The root `pyproject.toml` installs them all as path
dependencies, so an undeclared import is now visible in the devenv rather than only at a box.

## Why nixos-hardware, and what is forced back off

Two of the three platforms are covered upstream, and the coverage is uneven enough to be worth stating:

| Platform | Upstream | Effect |
| --- | --- | --- |
| `nuc12` | `intel/nuc/12wshi7` — literally this box, down to the chassis letter | `thermald`, and `i915` in the initrd |
| `evo-x2` | no EVO-X2; the `common/*` Strix Halo leaves that `framework/desktop/amd-ai-max-300-series` is built from | `amd_pstate=active`, and `amdgpu` in the initrd |
| `spark` | **nothing.** No GB10, Grace or Tegra content upstream, and `common/gpu/nvidia/*` is desktop-dGPU and PRIME-laptop oriented | its GPU is configured by hand from plain nixpkgs — see below |

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

### And why no DGX Spark input

The Spark is the one box with an obvious upstream to pin —
[`graham33/nixos-dgx-spark`](https://github.com/graham33/nixos-dgx-spark), MIT, actively maintained,
exposing its module as a plain path import. `platforms/spark.nix` deliberately does not, and the full
reasoning is in that file's header; the short version is that the GPU half is already in nixpkgs (595.71.05
with the open modules, the same driver package upstream takes), and what the fork actually buys is the
ConnectX-7 — at NV-Kernels 6.17.13 against our pin's 6.18.49, built from source on aarch64 with no cache
hits, and with a kernel config that turns on IOMMU passthrough.

The two asymmetries worth remembering if this is revisited:

- The Spark's `gpuVendor` is asserted the same way the x86 platforms' overrides are, in
  `tests/appliance-hardware.nix`. Its `kernel is still the nixpkgs default` check is what proves the fork
  has not quietly arrived: an image that gained a from-source 6.17 aarch64 kernel would otherwise be
  discovered by whoever was waiting for the build.
- `hardware.graphics.extraPackages32` must be forced empty on that platform, not merely left at its
  default. nixpkgs populates it from `pkgs.pkgsi686Linux`, which **throws** on aarch64, so anything that
  reads the option — the test above does — fails to evaluate unless the platform file forces it.

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

A platform declares `gpuVendor = "amd"` or `"nvidia"` when somebody has confirmed the box both binds the
kernel driver *and* enumerates the device through the vendor's compute stack. The driver alone proves
nothing — every platform here loads one, since that is what puts the installer menu on the monitor.
`loom-platform-info` is what confirms it: `/dev/kfd` or `/dev/nvidiactl`, the SMI tool's output, and
whether a CDI spec exists for the container runtime to pass the device through with.

Three things follow, and only the first is obvious:

- `modes.nix` passes `--gpus <vendor>` to `up.sh`, in both boot modes.
- `box.nix` adds the vendor's SMI tool to `loom.toolchain`, because `up.sh` refuses to run without it once
  `--gpus` is set. `tests/appliance.nix` asserts this, so declaring a vendor and forgetting the tool fails in
  CI rather than on the box.
- `runsAiServices` defaults to `gpuVendor != null`, so a CPU-only platform also drops Ollama.
  That is deliberate: the embedding step runs over every indexed file, and on a CPU the queue never drains.

The second point is spelled differently per vendor, because the vendors package the tool differently:
`rocm-smi` is a standalone package, while `nvidia-smi` is an output of the driver. So the nvidia branch in
`box.nix` names `config.hardware.nvidia.package.bin` — a platform that declares the vendor without
configuring `hardware.nvidia` gets an evaluation error rather than a `loom.service` that dies on
`nvidia-smi: command not found`.

`build-appliance-image --no-gpu` forces the vendor back to `null` through an `mkForce` in `default.nix`, which
is why nothing else has to know the flag exists. Note that it takes the AI services with it, by the same rule.

It does **not** take the driver with it. On the Spark `hardware.nvidia` is what puts the console on the
monitor, so it is configured by the platform file rather than gated on `gpuVendor`, and `--no-gpu` there
means "no offload" rather than "no NVIDIA". `loom-platform-info`'s `runtimeInputs` is keyed on
`hardware.nvidia.enabled` for exactly that reason: a `--no-gpu` box is the box somebody is diagnosing, and
the report needs `nvidia-smi` to say why the GPU did not enumerate.

### `runsAutoscaling`, and `loom.chartOverrides`

`runsAutoscaling` defaults to `meetsResourceMinimum` and adds `--scaling` to the `up.sh` arguments
`modes.nix` builds. The default is load-bearing rather than tidy: `up.sh` refuses `--scaling` alongside the
`--no-resources` an undersized box needs, and on an appliance that refusal is not a message on a terminal but
a box that never comes up. `modes.nix` asserts the two agree, so the mistake fails `appliance-eval` instead of
a stick.

The flag reaches **both** boot modes, like `--gpus` does, and for a reason specific to this one: `--scaling`
is the only thing that installs KEDA, so a first-time setup that ran without it leaves no KEDA images in
minikube's store, and run mode is air-gapped. `tests/scripts/loom_tests/appliance/modes.py` asserts both
scripts agree.

`loom.chartOverrides` is the other half. Some facts are true of the box rather than of Loom — today, that
scaling Ollama is pointless where there is one GPU to schedule it on — and they fit neither a values file
under `charts/` (shared with every cluster install) nor an `up.sh` flag (an argument to have on machines
nobody here is building). `modes.nix` puts them in that option, `repo.nix` writes them into
`charts/values-overwrites.yaml` while it seeds the checkout, and Skaffold applies that file after everything
else. The written file carries a header saying where it came from; it is written once, so an operator can
edit it afterwards.

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

## The mouse, and the three things that are not obvious about it

A Linux virtual console has no mouse driver. `console_codes(4)` says mouse reports reach the console
input stream "only when the virtual terminal driver receives a mouse update ioctl", generated by "a
mouse-aware user-mode application such as the `gpm(8)` daemon" — so an intermediate program is the
mechanism, not a design choice. Three findings shape `console-mouse.nix` and the shim beside it, and
each cost a while to establish:

**gpm does not do what that sentence implies.** Its whole on-screen behaviour is
`src/daemon/do_selection.c`, which only ever calls `selection_copy()` with `sel_mode` 3 (highlight
the pointer) or `event->clicks`. Nothing in the tree references `TIOCL_SELMOUSEREPORT`. So gpm plus
`set -g mouse on` gives a visible pointer and *zero* tmux events, silently. What gpm is good for is
everything below that — decoding the device, tracking an absolute position, the wheel, drawing the
pointer — and `loom-console-mouse` supplies the rest as a gpm client.

**The pointer is not repaint-safe, so the shim has to own the output stream.** The kernel draws it
in `complement_pos()` (`drivers/tty/vt/vt.c`), which caches the character *and* attribute under the
pointer and writes that cache back when the pointer next moves. A pane repainting underneath a
stationary pointer — btop and k9s do so continuously — therefore gets a stale character painted over
it on the next mouse movement, and tmux never reads the screen back, so nothing repairs it. The shim
is a pty between tty1 and the tmux client for exactly this reason: it can clear the pointer, write,
and put it back. Anything sitting *beside* the session cannot.

**gpm's SIGWINCH path segfaults, so the console resize is handled by restarting it.** gpm measures
the console once at startup and re-reads it only on `SIGWINCH` (`src/daemon/old_main.c`) — which is
delivered to a tty's foreground process group, and a daemon is never in one. Nothing sends gpm that
signal in ordinary use, the resize path is effectively dead code upstream, and dead code rots:
sending it makes gpm log `gpm pid N is resizing :-)` and die in `old_main`. `loom-console-font-reapply`
therefore `try-restart`s the unit instead, which re-reads the size on a path exercised at every boot.
`loom-console-mouse` reconnects on its own, so a restart costs nothing once a session is open.

The ordering matters for the same reason: `gpm.service` is `After=loom-console-font.service`, because
`branding.nix` resizes this console four times during boot and a gpm started before the last of those
clamps its pointer to a grid that no longer exists — on the 2560x1600 panel the appliance was tested
on, the difference between 160x50 and 426x123.

Since navigation is by mouse, `console.nix` also sets `prefix None`. It deliberately does **not** use
`unbind-key -a`: every mouse behaviour tmux has lives in the root key table as an ordinary binding —
`MouseDown1Pane { select-pane -t=; send -M }` *is* click-to-focus and forward-into-pane — so
unbinding everything would silently remove the feature. The `MouseDown3` bindings are unbound
by name, because they open `display-menu` with Kill, Respawn, Split, New Session and a command
prompt. None of this is a security boundary: every getty autologins the operator and `Alt-F2` reaches
a root-capable shell. Detach and respawn are clickable regions in the status line
(`#[range=user|...]`, which fires the `Status` mouse key, not `StatusRight`).

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
framework cannot supply". qemu can supply one. `target_disks` (`installer/loom_installer/devices.py`) wants
`/dev/nvmeXn1`, non-removable, and not the disk it booted from — `-device nvme` with the stick on
`usb-storage` satisfies all three, so the real `install.sh` runs against a real pool.

Flashing onto a file needs no root either: it is the same two steps `build_appliance_image.sh`
performs on a stick — write the image, then write 4096 bytes of key into the `loom-key` partition —
and `sfdisk --json` reads a partition table out of an ordinary file. That is also the limit of it:
an image built with `--lock-key` cannot be booted this way, because formatting a container inside
the virtual stick needs `losetup` and `cryptsetup`, which need root. The locked path is covered by
`tests/appliance-install.nix` and `tests/appliance-key-store.nix` instead, where root is free. The firmware keeps its own
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

### `--debug`, and what it costs

`debug.nix` is the other module whose whole point is that it is not in a shipped image, and it is a
larger deviation than `--serial`: it runs an sshd. The operator guide has the threat-model half
([Documentation/appliance.md](../Documentation/appliance.md#debug-images)); what matters here is how
the module hangs together.

- **`box.nix` says `services.openssh.enable = lib.mkDefault false`**, and `debug.nix` is the one
  thing allowed to define it as `true`. The `mkDefault` is deliberate over a `mkForce` on the other
  side: the policy statement should stay readable as a policy, and the exception as an exception.
- **The markers and the access are gated differently.** `system.nixos.tags`, the motd and
  `loom-debug-bundle` key on `loom.debug.enable`, so a debug stick booted into first-time-setup
  still says what it is for the hours that fetch takes. The sshd, the key-guard downgrade and the
  missing splash key on `enable && mode == "run"` — setup mode is a DHCP client on somebody else's
  network, which is the worst place to open a port that hands out root.
- **`modes.nix` is where `quiet` is decided, not `debug.nix`.** A module can add a kernel parameter
  and never subtract one, so a debug build has to *not acquire* `quiet` and `udev.log_level=3` in
  the first place. `debug.nix` adds `plymouth.enable=0` on top, the same pair setup mode uses.
- **The firewall hole is global, not `interfaces.loom0`.** In run mode the appliance segment is the
  only network the box has, so the two are the same packets — but `--wifi` moves the address onto
  the bridge, and `vm.nix` clears `networking.interfaces` entirely, so an interface-scoped rule
  would silently exclude both the air and the VM.
- **Only the public key crosses into Nix.** `cicd/build_appliance_image.sh` generates the pair into
  a directory it prints and never cleans up, and passes `--argstr debugSshAuthorizedKey`. Unlike the
  WiFi passphrase there is no secret in `/nix/store` and none on the stick.

The banner block is rendered by `box.nix`, at the **end** of `loom-info`, and the position is load
bearing: agetty writes the issue straight to the VT with no paging, so a banner taller than the
console loses its *first* rows. The tail is the only place a warning cannot scroll away from.

`appliance-vm box --debug` builds the same module and forwards `localhost:2222`, keeping its keypair
in the VM's state directory so it survives a rebuild. `appliance-test debug` is the VM test.

## Running the tests

```bash
appliance-check                     # everything that boots nothing, about a minute
appliance-test                      # all of them, cheapest first
appliance-test wifi usb-ingest      # or by name
```

`appliance-check` is the cheap half, and the half that runs in CI on every pipeline. It boots
nothing, so it needs neither KVM nor a host of the platform's architecture. It is two commands,
each runnable on its own, and it runs both even when the first one fails:

| Command | What it does |
| --- | --- |
| `appliance-pytest` | The suites under `nixos/`: `installer/tests` (the device interlock and the auto-install truth table), `usb-ingest/tests` (the name sanitiser, the filesystem table, the exclusion rules and the progress records), `console-mouse/tests` (the gpm wire format and the SGR translation), `ready/tests` (what counts as a workload, and the stage machine) and `tests/scripts/tests` (the VM tests' own screen and pane parsers). Extra arguments go to pytest. |
| `appliance-eval` | Instantiates `installerImage` for every platform — which covers the appliance too, since `installer.nix` puts its toplevel in the stick's store image — plus `tests` for this one. Catches a module that no longer evaluates, a renamed option, a failed assertion, and a typo in a test file that would otherwise surface twenty minutes into a VM boot. |

Every suite also runs inside the derivation that owns it — each package's `checkPhase` — so a
mistake fails an image build as well. Running them here costs a second instead of a closure. They
are in `devenv.nix` rather than in a shell runner for the same reason every other test in this
repository is; `cicd/appliance_eval.sh` stays a script because it is `nix-instantiate` plumbing
rather than a test.

### How a VM test is loaded

Each `tests/*.nix` installs `tests/scripts.nix` through the driver's `extraPythonPackages` and its
`testScript` is two lines — an import and the call:

```nix
  extraPythonPackages = p: [ (import ./scripts.nix { pythonPackages = p; }) ];

  testScript = ''
    from loom_tests.wifi import Params, run

    run(appliance, start_all=start_all, subtest=subtest, params=Params(...))
  '';
```

The package is built from the callback's own argument rather than from this repository's `pkgs`,
which is the part worth keeping: that argument is the *driver's* Python package set, so the package
is built for the interpreter that will import it by construction rather than by assuming the two
match.

What this replaced was `builtins.readFile`, which pasted each script into the one namespace the
driver `exec`s. That arrangement cost more than it looked: two files could not both `import json`
without the driver's ruff rejecting the pair as a redefinition, a reference from one file to another
was a pylint `used-before-assignment` that had to be worked around by passing functions as
arguments, and nothing could be shared *between* tests at all — which is how two of them ended up
with their own copy of the `/dev/vcsa1` decoder and three with their own copy of the tmux socket
path. `vt.py` and `tmux.py` are those, now written once. Being ordinary modules, the parsing in
them is also unit-tested in `tests/scripts/tests/` against a fake `Machine`, so an off-by-one in a
screen offset fails in milliseconds rather than ten minutes into a boot.

`driver.py` stays a Protocol rather than the driver's real `test_driver.machine.Machine`: that
package exists only inside the driver's closure, and importing it would mean the devenv could not
type-check any of this. Which is also why every test sets `skipTypeCheck = true` — exactly one of
the two type checks can run, and the one that runs on every commit is worth more.

`appliance-test` is the other half: the six short names and what each is for:

| Name | Attribute | What it asserts |
| --- | --- | --- |
| `hardware` | `tests.applianceHardware` | What nixos-hardware gives this platform, and that the Loom overrides still take the desktop userspace back off. **Not a VM test** — see below. |
| `appliance` | `tests.appliance` | The values `box.nix` restates from `up.sh` and `vars.sh`, the console session, and the key guard. |
| `install` | `tests.applianceInstall` | The disk layout: the pool, the container where stage 1 expects it, and the wipe. |
| `wifi` | `tests.applianceWifi` | The `--wifi` build, which `tests.appliance` deliberately does not cover: it forces off dnsmasq and the static addresses that this one exercises. Being the only test where dnsmasq runs, it is also where the DHCP offer itself is read — a lease that names a default gateway would take a visitor's laptop off the internet. |
| `mouse` | `tests.applianceMouse` | Point-and-click, end to end: a `uinput` mouse in the guest, through mousedev and gpm and the pty shim, to the pane tmux focuses — plus the detach control and the unreachable prefix. |
| `usb-ingest` | `tests.applianceUsbIngest` | Scratch disks carrying real filesystems, and the exclusion rules — above all that the LUKS key stick is never touched. |
| `interface-fallback` | `tests.applianceInterfaceFallback` | The box no platform matches: one NIC, two NICs, and the fallback switched off. |
| `key-store` | `tests.applianceKeyStore` | The `--lock-key` build's key guard, which arms on a weaker check than every other image's: a locked stick carries no plaintext key to test against the root. Getting that branch wrong leaves the guard idle for the life of the box, silently. |

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
is enough to run it, and `appliance-pytest` runs it with nothing built at all.

The installer has the same arrangement, for the same reason: `decide` in
`installer/loom_installer/decision.py` decides whether a disk is destroyed with nobody watching, so its
truth table is a pytest suite under `installer/tests/`, run in the package's own `checkPhase`.
`nix-build ./nixos -A installerImage` runs it — as does `appliance-pytest`.

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
  `rules: changes:` — `nixos/**/*`, `cicd/run_appliance_tests.sh`, `vars.sh`, `up.sh`,
  `charts/values.yaml` (which is where `vars.sh` reads the domain, the host list and the console's
  chat model from), `devenv.nix` and `devenv.lock`. It holds a shared runner for minutes with KVM and potentially hours without, and
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
| `key-store` | 1 | 96 MB — three 32 MB loop images, the same shape as `appliance`'s |

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
  constraint than the rest: it must name a model `ollama/Dockerfile.models` bakes into the production image, because
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

The stick side of the same numbers lives in `installer/loom_installer/constants.py` (`KEY_BYTES`, the partition
labels) and in `cicd/build_appliance_image.sh` (`KEY_BYTES`, `KEY_PARTLABEL`). Those cannot share the Nix
options — they run from the stick, before any of this exists — so they are the one pair that still has to
be kept in step by hand.

### And a third place, under `--lock-key`

`key-store.nix` adds a step in front of all of it: the partition holds a LUKS2 container, and an initrd unit
unlocks it onto a ramfs before `systemd-cryptsetup@cryptroot` runs. What keeps that from multiplying the
places that know about the key is a single invariant — **every consumer wants a path holding the 4096
plaintext bytes at offset 0**, and only the path changes:

| | Path |
| --- | --- |
| initrd | `loom.keyStore.plainKeyFile`, written by `key-store.nix`'s unit |
| installer | `/dev/mapper/<loom.keyStore.mapping>`, opened by `installer/loom_installer/keystore.py` |
| key guard | the partition itself, unchanged |

So `install.encrypt`, `install.enroll_recovery_passphrase` and `storage.pool_claimed_by_key` are untouched
by the flag: all three already took the key device as a parameter. `installer.nix` passes
`loom.keyStore.enable` and `.mapping` through `wrapProgram` beside the storage names, for the same reason.

The unit is shaped like nixpkgs' clevis unit (`luksroot.nix`, `cryptsetup-clevis-*`) rather than like a
second `boot.initrd.luks.devices` entry, and that is not a style choice. nixpkgs renders every entry into one
flat `/etc/crypttab` with no ordering between the lines, and systemd's generator derives dependencies from
the *device* column, not the key file column — so a nested mapping would race the root that depends on it.

The guard is the one consumer that does not follow the invariant, deliberately: it keeps reading the
partition, because what it is watching is a stick being pulled. On a locked box it cannot run its
`--test-passphrase` oracle — there is no plaintext key and it keeps none — so `loom.keyGuard.requireKeyOracle`
goes false and it arms on `cryptsetup isLuks` plus the fingerprint. The first 4096 bytes of a LUKS2 header
are unique per container and never zero, so identity and the "unprovisioned" sentinel both survive.
`tests/appliance-key-store.nix` is that branch.

The unlock script itself is the one part of this appliance that no test can reach -- nixpkgs'
qemu-vm module replaces the bootloader and the root device, so nothing under `tests/` ever runs an
initrd of ours. Two things stand in for that. It is a named binding rather than an inline `script`
string so that the same text can be handed to `shellcheck --enable=all` in a build check, with the
`set -e` preamble `makeJobScript` wraps it in -- an inline unit script is linted by nothing, the
same gap CLAUDE.md records for shell inlined into Helm templates. And `loom.keymap` is checked the
same way, by resolving the name with `loadkeys` at build time: `systemd-vconsole-setup` falls back
to US silently at boot, which is the precise failure the option exists to remove.

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

## The USB ingest test stick

`usb-ingest/loom_usb_ingest/filesystems.py` decides, per volume, whether the appliance mounts media
someone handed it and with which driver and options: six container formats in `REFUSED`, fifteen
filesystem types in `KNOWN`, and a generic `mount -t auto` for anything else the running kernel
admits to supporting. `devices.py` then takes every partition on every USB disk.

Almost none of that was ever exercised against real media. `tests/scripts/loom_tests/usb_ingest.py`
makes four filesystems — vfat, ext4, ntfs and a LUKS container — on *virtio* disks, so even the
`ID_BUS=="usb"` udev rule is bypassed.

`build-ingest-test-stick` closes that gap. It turns any USB stick of 4 GiB or more into 26
partitions, one filesystem each, so that plugging the result into an appliance takes every branch of
`plan_mount` at once:

It writes partition tables, so it runs under `sudo`. `sudo` resets `PATH`, and the devenv script is
on the devenv profile's `PATH` rather than the system's — hence `command -v` to resolve it first:

```bash
# Prints the plan and the stick's serial; writes nothing.
sudo "$(command -v build-ingest-test-stick)" \
  --device /dev/disk/by-id/usb-<vendor>_<model>_<serial>-0:0

# Builds it. The serial the plan printed has to be typed back.
sudo "$(command -v build-ingest-test-stick)" \
  --device /dev/disk/by-id/usb-<vendor>_<model>_<serial>-0:0 \
  --i-know-this-erases <serial>
```

Without `--i-know-this-erases` nothing is written. Typing the serial back is what keeps a
device-agnostic script safe: it cannot be satisfied without having looked at which disk is about to
be erased. Before that point the script also refuses anything that is not a `/dev/disk/by-id/usb-*`
whole disk, anything under 4 GiB, anything carrying `/`, `/boot` or `/nix/store`, anything mounted,
and anything with a Loom partition label or a LUKS container on it.

Nothing about the device is baked in: the table is a fixed 2976 MiB whatever the capacity, the
remainder is left unallocated, and re-running it on another stick produces the identical layout.
`--only N` reformats one partition without re-cutting the table, which is how you retry a single row.

Partitions 1–15 are the `KNOWN` types (`vfat` twice, as FAT16 and FAT32), 17–19 are tier-3
candidates, and 20–26 are the refusal signatures plus one deliberately blank partition. Each
mountable one carries a copy of `integrationtest/assets`.

Four things about it are worth knowing before reading the script:

- **The filesystem label is what reaches the operator.** `__main__.py` feeds
  `naming.volume_component` the *filesystem* label, not the partition label, so it becomes the S3
  path component `p<N>-<LABEL>`. The labels are `LOOM<NN><FS>`: eleven characters is the FAT and
  exFAT ceiling, and `[A-Z0-9]` passes `naming.sanitize_component` unchanged, so no hash suffix is
  appended.
- **The partition labels must never start with `loom-`.** A single `loom-esp` would make
  `classify_disk` refuse the whole disk and the stick would test nothing. They are `fstestNN-<fs>`,
  and the script refuses to touch a disk already carrying a Loom label — that is Loom's own media.
- **Every partition gets GPT type `0700`.** `devices.py` never reads the type GUID, so a truthful
  one buys nothing, while `8200`, `8E00`, `FD00` and `8309` would invite
  `systemd-gpt-auto-generator`, lvm2 and mdadm udev rules to act on the stick on the build host.
- **Two signatures cannot be made by a real tool.** BitLocker has no Linux creator: libblkid reads
  eleven bytes at offset 0 and, for the Vista form, consults no FVE metadata, so
  `\xeb\x52\x90-FVE-FS-` on a zeroed partition is the whole recipe. ZFS needs a pool, which needs the
  kernel module, which a NixOS host routinely lacks — so `ingest_test_stick_zfs_label.bin` is 256 KiB
  captured once from a real vdev label built by `ztest`, which runs libzpool entirely in userland
  (`ztest -f DIR -p LOOM21ZFS -s 128m -v 1`). libblkid reads label L0 at a fixed offset 16384, which
  is inside those 256 KiB, so the copy stands alone. Everything else uses the real tool — `mkswap`,
  `pvcreate`, `mdadm --create --metadata=1.2`, `cryptsetup luksFormat`.
- **MD RAID is built on a loop device and copied across.** `mdadm` opens its member `O_EXCL`, which
  the `mkfs` tools do not, and on a stick that has just had 26 partitions written to it something
  reliably holds that partition open — udev, udisks, whatever the desktop runs — so `mdadm --create`
  aborts with "Device or resource busy" no matter how long it waits. The loop file is created at the
  partition's exact size, and a 1.2 superblock sits at a fixed offset 4096 with `super_offset`
  recorded as 8 sectors, so the copy is exact rather than an approximation.

Each row asserts its own `blkid` type immediately after creation, and a row that fails is blanked
rather than left half-written: a partial signature would report as neither the intended filesystem
nor blank, which would corrupt the reading of partition 26 and of the "no recognisable filesystem"
branch generally.

### What the stick found

Three things, before it was even built:

- **`iso9660` cannot mount at all.** `filesystems.py` puts it in `NEEDS_OWNER`, so `plan_mount`
  appends `umask=0077` — and isofs has no `umask` option. Its parameter table is `block check conv
  cruft dmode hide interleave iocharset mode nocompress nojoliet norock overriderockperm sbsector
  session showassoc unhide`; `udf.ko` next door does have `umask`. An unrecognised key makes
  `mount(8)` return `-EINVAL`, so every ISO on every stick is skipped with "wrong fs type, bad
  option". Partition 14 makes that reproducible. The fix is `mode=0400,dmode=0500` for iso9660 only.
- **Tier 3 is effectively unreachable.** `mounts.kernel_filesystems()` reads `/proc/filesystems`,
  which lists only *loaded* filesystems, and `run()` snapshots it once before the volume loop.
  squashfs, erofs and minix are all modules, so an unknown type always takes the "the kernel has no
  driver" branch. Partitions 17 and 18 exist to show it: stock they are refused, and after
  `modprobe squashfs erofs` on the box they mount. The difference is the finding.
- **`ntfs3` in `KNOWN` is unreachable from media.** libblkid's NTFS prober only ever emits `ntfs`.

## Readiness, in one place and three screens

`ready.nix` and `ready/` answer "is Loom up yet?" — a question the console could not answer before it, because
the bring-up log says what is happening rather than how much is left, and `k9s` appears when `up.sh` returns,
which is well before the pods are Ready.

One unit computes it and writes two files into `/run/loom/ready`; three readers draw them and none of them
asks the cluster anything:

| File | Who reads it | Why |
| --- | --- | --- |
| `state.json` | the bring-up pane, the tmux status segment | everything: counts, workloads, blockers, stage |
| `summary` | `loom-info`, for the pre-login banner | one line of plain ASCII, so the banner needs no `jq` |

The split is the same one `usb-ingest/` uses, and for the same reason: the writer needs the cluster and runs
as root, while two of the readers are spawned by the operator's tmux server. A file is the whole of what they
share. The status segment is the sharp case — it runs from the tmux server on `status-interval`, so a
`kubectl` there could hang the session on a cluster that has stopped answering.

Three decisions in `ready/loom_ready/cluster.py` are worth knowing before changing anything:

- **Workloads, not pods.** A pod list cannot express "desired": a Deployment rolling out has no pods yet for
  the replicas it has not created, so a pod count makes the denominator chase the numerator.
- **A workload that wants zero replicas is not counted.** That is a KEDA-idle Deployment in its healthy steady
  state (`charts/templates/{worker,tika,gotenberg,ollama}/*scaledobjects.yaml`), and counting it would park the
  bar short of the end for the life of the box.
- **Jobs count as done when they have succeeded.** The init and pre-install Jobs gate everything behind them
  and never become Ready, so a check written in terms of Ready pods never sees them at all.

`Readiness.settled` — the `rolling-out`/`ready`/`degraded` stages — is the appliance's one definition of "up.sh
has returned and the namespace exists". `console.nix`'s pane used to evaluate that for itself; it now reads
this, which is what keeps the pane, the status line and the banner from disagreeing.

The banner is the one reader with a hard budget. agetty writes it straight to the VT with no paging, so
`summary` is deliberately **empty** while the cluster has not answered — the line earns its row once it has a
number on it, and `box.nix` tests `-s` rather than `-r`. The publisher redraws the banner through
`loom-banner-refresh` on a stage change and never on a count change, and never for the first stage a box
reaches: at boot `loom-banner-repaint` is already watching the console for a minute, and a second getty
restart inside that window would eat the keypress that opens the operator's session.
