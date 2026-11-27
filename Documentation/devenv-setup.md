# Loom Development Environment

This guide walks through setting up the Loom development environment using devenv (Nix-based),
covering prerequisites, initial configuration, and optional tooling for development.

[[_TOC_]]

## Prerequisites

- An `x86_64` or `aarch64` Linux host. Both are fully supported for development; see
  [Supported architectures](installation.md#supported-architectures) for the two features
  that are degraded on `aarch64`.
- `git` installed [official instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- ssh and/or https access to git repository
- Internet connection (for package/modules updates)

## Setting up Loom

The quickest path is the setup script. It walks the rest of this section, checks what is already
there, and asks before each step — showing the exact command first, so nothing happens that you
have not read. A bare Enter declines.

```sh
git clone --recursive $repository
cd loom/
./cicd/setup-devenv
```

It is safe to re-run: anything already in place is reported as done rather than asked about again,
which also makes it a way to check a machine.

**The steps are not listed here.** Each one prints what it is for and the exact thing it will do
before asking, `--help` names them all in order along with every flag, and `--dry-run` walks the
whole run without touching anything — it writes nothing, asks for nothing and contacts nothing.
A list in this file would be a second copy of that, drifting from the first.

Three things it leaves to you, because guessing would be worse than asking:

- **Installing docker**, which differs per distribution. It points you at the official instructions.
- **On NixOS**, editing `/etc/nix/nix.conf` — that file is generated, so the script prints the
  `configuration.nix` snippet to paste instead.
- **A `devenv.local.nix` that already holds other settings.** The token step will not rewrite one,
  because that file is also where `cicd-mode-enter` and CI put `{ env.cicd = true; }`. It prints
  the line to add instead.

### Doing it by hand

`./cicd/setup-devenv --dry-run` prints every command it would run, so it doubles as the
instructions — including the two things it leaves to you. What follows is only what a command
cannot tell you about itself.

**Docker.** Install docker-engine, _not_ docker-desktop, by the
[official instructions](https://docs.docker.com/engine/install/). The group change needs a
re-login before it takes effect. To pull from the registry you also need a
[personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token)
with the `read_registry` scope, used as the password for `docker login registry.gitlab.com` and
`docker login gitlab.com`.

**The binary caches.** The `nix-caches` step writes two settings into `/etc/nix/nix.conf`;
`--only nix-caches --dry-run` prints the exact block, and on NixOS prints a `configuration.nix`
snippet instead, because that file is generated there and a direct edit is undone by the next
`nixos-rebuild`. Four things about them are worth knowing and are not visible in the block:

- **Why the daemon's config and not `trusted-users`.** Nix uses a substituter when **either** the
  caller is in `trusted-users` **or** the daemon's own configuration names it. Writing the
  daemon's configuration makes the caches work for every account on the machine while nobody has
  to be trusted — which matters, because the nix manual describes adding a user to
  `trusted-users` as "essentially equivalent to giving that user root access to the system". If
  you are already in `trusted-users` nothing breaks; it is simply no longer needed.
- **Every cache has to be named.** `devenv.cachix.org` because the first `devenv shell` fetches
  devenv itself, before anything in this repository can apply; the other two are what `devenv.nix`
  pulls from. One left out is one the daemon does not know, which prints
  `ignoring untrusted substituter '<url>'` on every nix command. Without `loom.cachix.org`, an
  appliance build compiles its whole closure from source — for `spark`, a qemu-emulated aarch64
  kernel, hours against a 32 MB download.
- **`extra-` matters.** The plain spelling _replaces_ the list, so a block that forgot
  `cache.nixos.org` would quietly remove it.
- **Writing them by hand and then running the script gives you two copies.** The script owns what
  lies between its `# >>> loom devenv setup >>>` markers and cannot recognise a block you typed
  yourself. Let it write them, or delete yours first.

Keep personal nix settings in `~/.config/nix/nix.conf` rather than in a `NIX_CONFIG` of your own —
the shell sets that variable.

> ⚠️ **On Fedora**, after installing Nix, open
> `/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh` and comment out the first two lines.

Then start the development environment: `cd loom/ && up --development`, and `code .` for VS Code.

## Setup verification

Wait for the k8s process to settle, it might take a few minutes.
Then navigate to the frontend: <https://frontend.loom>

Upload a file, check if analysis is working and it's indexed.

## Shell

The devenv provides a number of useful commands.
Start a shell with `devenv shell` and run `devenv-help` to get an overview.

## Optimizing Development Deployment

`up --help` lists every flag. Two are worth knowing about before you need them, because what
they cost is not obvious from their names:

- **`--disable-ai`** skips summarization, translation and embeddings, which is most of a
  deployment's time and memory. Any task that depends on those services then _fails_ rather than
  degrading, so it is only for work that does not touch them.
- **`--no-resources`** drops every CPU and memory request and limit. On a low-memory machine the
  defaults are what make pods OOMKilled or unschedulable, so this is usually the fix for a
  deployment that will not come up at all.

## Tailscale (optional)

If you need to connect to one of the gitlab runners, refer to [the detailed instructions](./tailscale.md).

## GitLab Duo Support (optional)

The Loom development environment supports GitLab Duo's AI-powered code completion feature
out of the box. The GitLab Workflow extension is pre-installed as part of the `devenv.nix`
setup, allowing seamless integration with GitLab repositories. To enable GitLab Duo, ensure
you're authenticated using a **personal access token**—OAuth-based authentication is
**not supported** in this setup. When prompted, log in with your GitLab.com credentials
using the access token as the password. Once authenticated, GitLab Duo will be able to
provide contextual code suggestions directly within your development environment.

## Setting up GITLAB_TOKEN by hand

`aitools`, `up.sh`'s online probe and the setup script's own `ssh-key` step all need a GitLab
personal access token, in `devenv.local.nix` — a file devenv loads automatically and git ignores.

The `gitlab-token` step writes it for you, so this section is for the two cases where it does
not: when you passed `--skip-gitlab-token`, and when `devenv.local.nix` already holds other
settings — `cicd-mode-enter` and CI both put `{ env.cicd = true; }` there, and the step will not
overwrite that.

Create a [personal access token][pat-docs] with the `api` scope, put it in `devenv.local.nix` in
the repository root, and add the binding to whatever is already in the file rather than replacing
it:

```nix
{ ... }:
{
  env.GITLAB_TOKEN = "glpat-xxxxxxxxxxxxxxxxxxxx";
}
```

It holds a credential, so `chmod 600 devenv.local.nix`, then `direnv reload`. See the
[devenv documentation](https://devenv.sh/files-and-variables/) for more options.

The file is gitignored, so it does not follow a checkout into a git worktree, and without it every
`aitools` GitLab call there fails. When `aitools` adds a worktree of its own it copies this file in
from the primary checkout, and never overwrites one that is already there — a worktree you added by
hand needs the copy made by hand.

[pat-docs]: https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token

## OpenCode (optional)

[OpenCode](https://opencode.ai/) is an AI coding assistant available in the devenv. It is
pre-configured to use the Infomaniak AI provider. To use it, you need to set two environment
variables with your Infomaniak credentials.

Add the following exports to your `~/.bashrc` (or equivalent shell configuration file):

```sh
export INFOMANIAK_PRODUCT_ID="your-product-id"
export INFOMANIAK_API_KEY="your-api-key"
```

Then reload your shell or run `source ~/.bashrc`.

The devenv automatically sets `OPENCODE_CONFIG` to point to the project's configuration file
(`cicd/opencode.json`), so no additional configuration is needed. Once the environment variables
are in place, run `opencode` from the repository root to start a session.

## More Documentation and Links

Get further information by reading the [documentations](../README.md#-more-documentation-and-links)
