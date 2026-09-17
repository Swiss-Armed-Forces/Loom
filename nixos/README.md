# `nixos/` — the Loom appliance

The declarative definition of a standalone Loom box, and of the USB stick that installs it.
User-facing documentation lives in [../Documentation/appliance.md](../Documentation/appliance.md);
this file is about the code.

## Files

| File | What it is |
| --- | --- |
| `default.nix` | Entry point. Takes `nixpkgs` as an argument and returns the build targets. |
| `box.nix` | The appliance: host tuning, toolchain, operator account, `loom-up`. |
| `box-hardware.nix` | LUKS root, filesystems, initrd, bootloader. |
| `modes.nix` | `loom.mode`, the run/setup services, and the `setup` specialisation. |
| `network.nix` | Static address and dnsmasq in run mode, DHCP client in setup mode, radios off. |
| `repo.nix` | Seeds the embedded checkout into the operator's home, writable. |
| `installer.nix` | The USB stick: `image.repart` layout and the installer system. |
| `installer-scripts/` | `common.sh` (device interlock), `install.sh`, `wipe.sh`, `menu.sh`. |
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

## Building by hand

Normally you would use `build-appliance-image`. To drive it directly — note that `system` defaults to the
host, which is what makes x86_64 testing possible:

```bash
export LOOM_NIXPKGS=...            # a nixpkgs checkout
HOSTS=$(source ./vars.sh && printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" | jq -R . | jq -sc .)

# Evaluate only -- catches most mistakes in seconds.
nix-instantiate ./nixos -A box \
  --arg nixpkgs "$LOOM_NIXPKGS" --argstr system x86_64-linux \
  --arg repoSrc ./. --argstr tag dev --argstr loomHostsJson "$HOSTS"

# A bootable VM of the appliance, to poke at by hand.
nix-build ./nixos -A boxVm --argstr system x86_64-linux ...
./result/bin/run-*-vm

# The stick image.
nix-build ./nixos -A installerImage ...
```

Targets: `box`, `boxVm`, `installerImage`, `tests.appliance`, plus `boxSystem` and `installerSystem`
for poking at evaluated configuration.

## Running the test

```bash
nix-build ./nixos -A tests.appliance --argstr system x86_64-linux ...
```

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
- every binary `validate_environment` checks for (`up.sh:402-428`)

`tests/appliance.nix` asserts all three, so a change on either side is caught rather than shipped. If you
add a `check_command` to `up.sh`, add the package to `box.nix` and the name to the test.
