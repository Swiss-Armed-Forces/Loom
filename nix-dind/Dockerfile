# Image version
ARG DIND_IMAGE_VERSION="28.5.2-dind-alpine3.22"
ARG DIND_IMAGE_DIGEST="sha256:2a232a42256f70d78e3cc5d2b5d6b3276710a0de0596c145f627ecfae90282ac"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/docker:${DIND_IMAGE_VERSION}@${DIND_IMAGE_DIGEST}

# We will use this image as a gitlab-ci runner image.
# This is why we have to add here the label below, otherwise
# the clear-docker-cache script provided by gitlab will not
# clear stale versions of this image.
#
# see: https://gitlab.com/gitlab-org/gitlab-runner/-/issues/29518
LABEL "com.gitlab.gitlab-runner.managed"=true

#
# Bash
#
ARG BASH_VERSION="5.2.37-r0"
RUN set -exu \
    && apk add --no-cache \
    bash=${BASH_VERSION}
SHELL ["/bin/bash", "--login", "-c"]

#
# Sudo
#
ARG SUDO_VERSION="1.9.17_p2-r0"
RUN set -exu \
    && apk add --no-cache \
    sudo=${SUDO_VERSION}

# We have to install our own version of the sudoers
# file, because the default sudoers does not preserver
# PATHS and does not allow running any binary in /nix/
COPY \
    --chown=root:root \
    --chmod=440 \
    nix-dind/sudoers /etc/sudoers

#
# Install bindfs
#
ARG BINDFS_VERSION="1.18.4-r0"
RUN set -exu \
    && apk add --no-cache \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/main \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing \
    bindfs=${BINDFS_VERSION}

#
# Install tailscale
#
ARG TAILSCALE_VERSION="1.86.2-r3"
RUN set -exu \
    && apk add --no-cache \
    tailscale="${TAILSCALE_VERSION}"

#
# shadow (for groupadd)
#
ARG SHADOW_VERSION="4.17.3-r0"
RUN set -exu \
    && apk add --no-cache \
    shadow=${SHADOW_VERSION}

#
# Workaround for busybox `cp`
# not supporting `--preserve=ownership,timestamps`
#
# see:
#   - https://github.com/NixOS/nix/issues/13480
#   - https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/118
#
ARG COREUTILS="9.7-r1"
RUN set -exu \
    && apk add --no-cache \
    coreutils=${COREUTILS}

#
# Install nix (package version)
#
#ARG NIX_VERSION="2.28.3-r1"
#RUN set -exu \
#    && apk add --no-cache \
#    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
#    nix=${NIX_VERSION}

#
# Install nix (from upstream)
#
ARG CURL_VERSION="8.14.1-r3"
ARG XZ_VERSION="5.8.1-r0"
RUN set -exu \
    && apk add --no-cache \
    curl=${CURL_VERSION} \
    xz=${XZ_VERSION}
RUN set -exu \
    && sh <(curl -L https://nixos.org/nix/install) --daemon

ARG NIX_GROUP_ID="1000"
ARG NIX_GROUP_NAME="nix"
ENV NIX_GROUP_NAME="${NIX_GROUP_NAME}"

ARG NIX_USER_ID="1000"
ARG NIX_USER_NAME="nix"
ENV NIX_USER_NAME="${NIX_USER_NAME}"

ARG NIX_USER_HOMEDIR="/home/nix"
ENV NIX_USER_HOMEDIR=${NIX_USER_HOMEDIR}

# Add nix user, allowed to use sudo
# we then also, configure nix to:
# - add the user to the trusted-users
# - disable the sandbox
# hadolint ignore=DL3004
RUN set -exu \
    && groupadd \
    --force \
    --gid "${NIX_GROUP_ID}" \
    "${NIX_GROUP_NAME}" \
    && adduser \
    -u "${NIX_USER_ID}" \
    -S "${NIX_USER_NAME}" \
    -G "${NIX_GROUP_NAME}" \
    -s /bin/bash \
    -h "${NIX_USER_HOMEDIR}" \
    && adduser "${NIX_USER_NAME}" docker \
    && sudo -i -u "${NIX_USER_NAME}" \
    mkdir -p "${NIX_USER_HOMEDIR}/.docker" \
    && echo "trusted-users = root ${NIX_USER_NAME}" >> /etc/nix/nix.conf \
    && echo "sandbox = false" >> /etc/nix/nix.conf \
    && echo "${NIX_USER_NAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

#
# Nix-daemon setup
#
# Applies to the image build only, entrypoint.sh starts the runtime daemon.
# Empty by default: the daemon debug output blows up the CI job log, which
# GitLab truncates at 4MB.
ARG NIX_DAEMON_ARGS=""
ENV NIX_DAEMON_ARGS=${NIX_DAEMON_ARGS}
# Note: optimizing nix store takes a long time...
ARG NIX_STORE_OPTIMIZE=true
ENV NIX_STORE_OPTIMIZE=${NIX_STORE_OPTIMIZE}

# This channel must match the one specified in the devenv setup instructions
ARG NIX_CHANNEL="nixos-26.05"
#ARG NIX_CHANNEL="nixpkgs-unstable"
#ARG NIX_CHANNEL="02b9ebc695596cdcd7d58b1180e1be4b0d6735f8"
# hadolint ignore=DL3004
RUN set -exu \
    && fork() { (setsid "$@" &); } && fork nix-daemon ${NIX_DAEMON_ARGS} \
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-channel --add "https://github.com/NixOS/nixpkgs/archive/${NIX_CHANNEL}.tar.gz" "nixpkgs"\
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-channel --update \
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-env -iA nixpkgs.devenv \
    && nix-collect-garbage --quiet --delete-old \
    && if [ "${NIX_STORE_OPTIMIZE}" == "true" ]; then nix-store --quiet --optimise; fi \
    && nix-store --verify --check-contents

# Copy Lockfiles

# nix
COPY --chown=${NIX_USER_NAME} \
    devenv.lock \
    devenv.nix \
    devenv.yaml \
    nix-dind/devenv.local.nix \
    "${NIX_USER_HOMEDIR}"/
COPY --chown=${NIX_USER_NAME} \
    nix-dind/devenv.local.nix \
    "${NIX_USER_HOMEDIR}"/nix-dind/


# Realise the whole devenv package set, so that a job using this image does
# not have to download it, and clean up the store afterwards.
#
# Entering the shell is what realises the package set.  We disable
# install.enable for all languages, because we do not want any of the project
# packages installed into the image.
#
# Note: this has to stay a single RUN.  Garbage collection only pays off for
# paths the same RUN created: deleting anything an earlier layer wrote leaves
# its bytes in that layer and merely stacks a whiteout on top.  The same holds
# for `nix-store --optimise`, which has to copy a file up out of the lower
# layers before it can hardlink it, so across layers it grows the image
# instead of shrinking it.
#
# The collection also drops the sources that evaluating the devenv shell
# needs, such as the devenv-nixpkgs tree and the patches applied to it.  No GC
# root points at them while the nix fetcher cache keeps referring to them,
# which makes a later evaluation fail with "path '/nix/store/...' is not
# valid".  The `devenv build shell` after the collection restores them, so
# nothing may collect garbage past that point.  As a build it is a no-op - the
# shell is already realised and rooted by then - we run it for the evaluation.
# hadolint ignore=DL3004
RUN set -exu \
    && fork() { (setsid "$@" &); } && fork nix-daemon ${NIX_DAEMON_ARGS} \
    && sudo -i -u "${NIX_USER_NAME}" \
    devenv shell \
    --option languages.python.poetry.install.enable:bool false \
    --option languages.javascript.pnpm.install.enable:bool false \
    -- true \
    && nix-collect-garbage --quiet --delete-old \
    && sudo -i -u "${NIX_USER_NAME}" \
    devenv build shell \
    && if [ "${NIX_STORE_OPTIMIZE}" == "true" ]; then nix-store --quiet --optimise; fi \
    && nix-store --verify --check-contents

# ignore ownership of directory
# ref: https://stackoverflow.com/questions/75878318
# hadolint ignore=DL3004
RUN set -exu \
    && sudo -i -u "${NIX_USER_NAME}" \
    git config \
    --global \
    --add \
    safe.directory "*"

#
# Entrypoint
#
COPY --chmod=0755 nix-dind/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["bash", "--login", "/usr/local/bin/entrypoint.sh"]
