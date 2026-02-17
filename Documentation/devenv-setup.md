# Loom Development Environment

## Prerequisites

- `git` installed [official instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- ssh and/or https access to git repository
- Internet connection (for package/modules updates)

## Setting up Loom

1. Set up git:
   - Set username (must match your displayed name on gitlab):
   `git config --global user.name "USERNAME"`
   - Set email (must match your email on gitlab):
   `git config --global user.email "EMAIL"`
2. Clone git repository:
   - Clone repo: `git clone --recursive $repository`
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
   - Install devenv using the [official instructions](https://devenv.sh/getting-started/)
   - ❗**Workaround for fedora-41**:
   After installing nix open the file `/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh`
   and comment out the first two lines
6. Install direnv
   - Install direnv using the [official instructions](https://direnv.net/docs/installation.html)
   - Don't forget to hook direnv into your shell [instructions](https://direnv.net/docs/hook.html)
   - Open file `/etc/nix/nix.conf` and add the following lines

   ```bash
   extra-substituters = https://devenv.cachix.org
   extra-trusted-public-keys = devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=
   ```

   - Run `sudo systemctl restart nix-daemon.service` to restart the Nix daemon
   - Allow direnv to run in the loom directory: `cd loom/ && direnv allow`
7. Start the development environment:
   - Loom: `cd loom/ && up --development`
   - VS Code: `cd loom/ && code .`

## Setup verification

Wait for the k8s process to settle, it might take a few minutes.
Then navigate to the frontend: <http://frontend.loom>

Upload a file, check if analysis is working and it's indexed.

## Shell

The devenv provides a number of useful commands.
Start a shell with `devenv shell` and run `devenv-help` to get an overview.

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

## More Documentation and Links

Get further information by reading the [documentations](../README.md#-more-documentation-and-links)
