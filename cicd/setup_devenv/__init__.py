"""Interactive first-time setup for the Loom development environment.

Walks a fresh clone through everything `Documentation/devenv-setup.md` asks for: a
GitLab token and identity, Nix, the binary caches, devenv, direnv and docker. Every
step states what it is about to do and shows the real thing before asking, so nothing
happens that the operator has not read first. A bare Enter declines.

Nothing here needs the development environment it sets up: **standard library only**,
no Nix, no project venv. That is the whole point -- it runs before any of them exist.
For the same reason **Python 3.9 is the floor**, which is what Debian 11 and RHEL 9
ship. `Optional`/`List`/`Tuple` rather than `|` and the builtin generics, and no
`match` statement, are that floor being respected rather than old habits; pylint
cannot check it, because it infers its target from the devenv interpreter.

Re-running is safe. Each step decides for itself whether it is already satisfied and
says so instead of asking again, so this doubles as a way to check a machine.

## Assess, then act

A `Step` splits in two, and the split is what makes the promise above keepable.

`assess` **reads local state only** -- the filesystem, `git config`, what is on PATH.
It never prompts and never writes. Everything that changes the machine is an `Action`
(see `setup_actions.py`), which can `describe()` itself before it is consented to and
`perform()` itself afterwards. `--dry-run` runs every assessment and no action.

There is one carve-out, and it is deliberate: a step may make a **read-only** GitLab
call while assessing, when a token is **already stored locally**, because "is this key
already on the account" and "what is this account called" have no local answer. Those
calls are skipped under `--dry-run`, so a dry run still opens no socket, asks for
nothing and writes nothing.

## The binary caches

The one step worth explaining. Nix refuses a substituter a *client* asks for unless the
caller is in `trusted-users` -- which the nix manual calls "essentially equivalent to
giving that user root access to the system". A daemon that names the caches in its own
`/etc/nix/nix.conf` serves them to everybody without granting anybody anything, so that
is what this writes. `extra-` because the plain spelling replaces the list rather than
adding to it, and a block that forgot `cache.nixos.org` would silently remove it.

Without this the Loom cache is unreachable and `build-appliance-image` compiles the
appliance closure from source -- for `spark`, a qemu-emulated aarch64 kernel, hours
against a 32 MB download.
"""
