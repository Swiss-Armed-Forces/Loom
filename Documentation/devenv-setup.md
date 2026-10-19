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
./cicd/setup_devenv.py
```

It is safe to re-run: anything already in place is reported as done rather than asked about again,
which also makes it a way to check a machine. `--dry-run` shows every step and runs nothing.

Two things it leaves to you, because guessing would be worse than asking:

- **Installing docker**, which differs per distribution. It points you at the official instructions.
- **On NixOS**, editing `/etc/nix/nix.conf` — that file is generated, so the script prints the
  `configuration.nix` snippet to paste instead.

The rest of this section is the same setup done by hand.

1. Set up git:
    - Set username (must match your displayed name on gitlab):
      `git config --global user.name "USERNAME"`
    - Set email (must match your email on gitlab):
      `git config --global user.email "EMAIL"`
2. Clone git repository:
    - Clone repo: `git clone --recursive $repository`
    - Development uses the `main` branch. For stable/production deployments, check out the latest release tag instead (see the [installation instructions](../README.md#installation)).
3. Install docker:
    - Install docker-engine (do not install the alternative called docker-desktop) using the [official instructions](https://docs.docker.com/engine/install/)
    - Add user to docker group: `sudo gpasswd -a $USER docker`
    - Reboot your system
4. Configure docker:
    - Create a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token)
      - Check all boxes when selecting the scopes
    - Use the Access token instead of the password in the next steps
    - Login to the docker registry: `docker login registry.gitlab.com`
    - Login to the docker cache: `docker login gitlab.com`
5. Install devenv
    - In /etc/selinux/config, set `SELINUX=disabled` and reboot
    - Install [Nix](https://nixos.org/)

      ```sh
      sh <(curl -L https://nixos.org/nix/install) --daemon
      ```

    - Install [devenv](https://devenv.sh/getting-started/) with `nix-env` from stable channel

      ```sh
      nix-env --install --attr devenv -f https://github.com/NixOS/nixpkgs/tarball/nixos-26.05
      ```

    > ⚠️ **Workaround for Fedora:** After installing Nix, open
    > `/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh`
    > and comment out the first two lines.

6. Install direnv
    - Install direnv using the [official instructions](https://direnv.net/docs/installation.html)
    - Don't forget to hook direnv into your shell [instructions](https://direnv.net/docs/hook.html)
    - Open file `/etc/nix/nix.conf` and add the following lines, exactly as they are —
      there is nothing in them to fill in

    ```bash
    extra-substituters = https://devenv.cachix.org https://loom.cachix.org https://nixpkgs-python.cachix.org
    extra-trusted-public-keys = devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw= loom.cachix.org-1:qK4ugmN5g4Pvhv45OLcXTwG53ZnSauwrHLVA0A7Y0rs= nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU=
    ```

    > **On NixOS**, `/etc/nix/nix.conf` is generated and editing it is undone by the next
    > `nixos-rebuild`. Put the same two settings in `configuration.nix` as
    > `nix.settings.extra-substituters` and `nix.settings.extra-trusted-public-keys`, each a
    > list of strings, and rebuild. `./cicd/setup_devenv.py` prints the snippet ready to paste.
    >
    > **Why this, and not `trusted-users`.** Nix uses a substituter when **either** the caller
    > is in `trusted-users` **or** the daemon's own configuration names it. The lines above are
    > the daemon's own configuration, so the caches work for every account on the machine and
    > nobody has to be trusted — which matters, because the nix manual describes adding a user
    > to `trusted-users` as "essentially equivalent to giving that user root access to the
    > system". If you already have yourself in `trusted-users`, nothing here breaks; it is
    > simply no longer needed.
    >
    > **Name every cache.** `devenv.cachix.org` has to be there because the first
    > `devenv shell` fetches devenv itself, before anything in this repository can apply. The
    > other two are what `devenv.nix` pulls from, and a cache left out of this list is one the
    > daemon does not know — producing `ignoring untrusted substituter '<url>'` on every nix
    > command. Without `loom.cachix.org` in particular, an appliance build compiles its whole
    > closure from source: for `spark`, a qemu-emulated aarch64 kernel, hours against a 32 MB
    > download.
    >
    > **`extra-` matters.** The plain spelling _replaces_ the list, so a block that forgot
    > `cache.nixos.org` would quietly remove it.
    >
    > Keep personal nix settings in `~/.config/nix/nix.conf` rather than in a `NIX_CONFIG` of
    > your own — the shell sets that variable.

    - Run `sudo systemctl restart nix-daemon.service` to restart the Nix daemon
    - Allow direnv to run in the loom directory: `cd loom/ && direnv allow`
    - Check it worked: `./cicd/setup_devenv.py --only verify` reports any cache the daemon
      is still missing

7. Start the development environment:
    - Loom: `cd loom/ && up --development`
    - VS Code: `cd loom/ && code .`

## Setup verification

Wait for the k8s process to settle, it might take a few minutes.
Then navigate to the frontend: <https://frontend.loom>

Upload a file, check if analysis is working and it's indexed.

## Shell

The devenv provides a number of useful commands.
Start a shell with `devenv shell` and run `devenv-help` to get an overview.

## Optimizing Development Deployment

If you don't need certain features during development, you can significantly
speed up deployment time and reduce resource usage by passing flags to `up`.

### Disable AI Features (optional)

If you're not working on AI-related functionality
(summarization, translation, embeddings), disable these services:

```sh
up --development --disable-ai
```

> ⚠️ When services are disabled, any tasks that depend on them will fail.

### Remove Resource Requests and Limits (optional)

By default, Loom deployments include CPU and memory requests and limits for all containers.
On low-memory machines, these limits can cause pods to be OOMKilled or fail to schedule.
Pass `--no-resources` to `up` to deploy without any resource requests or limits:

```sh
up --development --no-resources
```

This flag can be combined with any other `up` flags.

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

## Setting up GITLAB_TOKEN (optional)

Some development tools (like `ai-mr-update`) require a GitLab personal access token. You can
configure this using `devenv.local.nix`, which is automatically loaded by devenv and excluded
from git.

1. Create a [personal access token][pat-docs] with `api` scope

2. Create the file `devenv.local.nix` in the repository root:

    ```nix
    { ... }:
    {
      env.GITLAB_TOKEN = "glpat-xxxxxxxxxxxxxxxxxxxx";
    }
    ```

3. Reload the devenv environment:

    ```sh
    direnv reload
    ```

The `devenv.local.nix` file is gitignored, so your token stays local and won't be committed.
See the [devenv documentation](https://devenv.sh/files-and-variables/) for more options.

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
