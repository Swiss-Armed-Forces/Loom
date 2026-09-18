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
| `branding.nix` | Shared by box and stick: the name in the boot menu, the logo, the plymouth theme, `loom-eyes`, and the VT font — its size (`loom.consoleFont`), its glyph check, and the unit that re-applies it once the display has settled. |
| `box.nix` | The appliance: host tuning, toolchain, operator account, banner, `loom-up`. |
| `console.nix` | What the operator meets: the press-a-key login, the three-pane session (the log-to-`k9s` handover, and `loom-chat` on the cluster's Ollama), `/dev/console`. No pane is a shell; `Alt-F2` is. |
| `box-hardware.nix` | LUKS root, filesystems, initrd, bootloader — including why the menu timeout stays at 30s. |
| `key-guard.nix` | Watches the USB key while the box runs and powers it off when the key leaves. |
| `modes.nix` | `loom.mode`, the run/setup services, the `first-time-setup` specialisation, and `loom-promote-boot-entry`. |
| `network.nix` | Static address and dnsmasq in run mode, DHCP client in setup mode, the `--wifi` bridge, radios off. |
| `wifi.nix` | The optional access point: `loom.wifi.*`, hostapd, and the check that says so on the console when the radio never came up. |
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer-scripts/` | `common.sh` (device interlock, console styling), `install.sh`, `wipe.sh`, `menu.sh`. |
| `tests/appliance.nix` | VM test asserting the values `box.nix` restates from `up.sh`, and the console session. |
| `tests/appliance-wifi.nix` | VM test for the `--wifi` build: hostapd on a `mac80211_hwsim` radio, the bridge, and the credentials on the login screen. |

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

Adding a third box means one file under `platforms/`, one entry in the `platformModules` table in
`default.nix`, and one case in `platform_system()` in `cicd/build_appliance_image.sh`.

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
```

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
