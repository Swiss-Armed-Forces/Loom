# `nixos/` — the Loom appliance

The declarative definition of a standalone Loom box, and of the USB stick that installs it.
User-facing documentation lives in [../Documentation/appliance.md](../Documentation/appliance.md);
this file is about the code.

## Files

| File | What it is |
| --- | --- |
| `default.nix` | Entry point. Takes `nixpkgs` as an argument and returns the build targets. |
| `platform.nix` | Declares `loom.platform.*`: the per-box dimension, separate from `system`. |
| `platforms/spark.nix` | DGX Spark: aarch64, serial console, ConnectX-7. |
| `platforms/evo-x2.nix` | GMKtec EVO-X2: x86_64, no serial port, Realtek 2.5GbE. |
| `branding.nix` | Shared by box and stick: the name in the boot menu, the logo, the plymouth theme. |
| `box.nix` | The appliance: host tuning, toolchain, operator account, console banner, `loom-up`. |
| `box-hardware.nix` | LUKS root, filesystems, initrd, bootloader. |
| `modes.nix` | `loom.mode`, the run/setup services, and the `first-time-setup` specialisation. |
| `network.nix` | Static address and dnsmasq in run mode, DHCP client in setup mode, radios off. |
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer-scripts/` | `common.sh` (device interlock, console styling), `install.sh`, `wipe.sh`, `menu.sh`. |
| `tests/appliance.nix` | VM test asserting the values `box.nix` restates from `up.sh`. |

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
claim, whether there is a serial port, which initrd modules to add) is a property of the machine.

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

`tests/appliance.nix` asserts all three, so a change on either side is caught rather than shipped. If you
add a `check_command` to `up.sh`, add the package to `loom.toolchain` in `box.nix` and the name to the test.

`loom.toolchain` is one list on purpose. It feeds both `environment.systemPackages` and the `path` of the
units in `modes.nix`, because a unit's PATH is built solely from its own `path` plus a minimal default
(coreutils, findutils, gnugrep, gnused, systemd) — `/run/current-system/sw/bin` is never on it. When the
two were maintained separately they drifted, and the box shipped with a `loom.service` that died on
`awk: command not found` while the same command worked fine in the operator's shell. For the same reason
the test resolves each binary against `loom.service`'s own PATH rather than the login shell's.
