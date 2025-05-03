ARG DIND_IMAGE_VERSION="27.5.1-dind"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/docker:${DIND_IMAGE_VERSION}

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
ARG SUDO_VERSION="1.9.16_p2-r0"
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
ARG BINDFS_VERSION="1.17.7-r0"
RUN set -exu \
    && apk add --no-cache \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing \
    bindfs=${BINDFS_VERSION}

#
# Install tailscale
#
ARG TAILSCALE_VERSION="1.76.6-r8"
RUN set -exu \
    && apk add --no-cache \
    tailscale="${TAILSCALE_VERSION}"

#
# Install nix (package version)
#
#ARG NIX_VERSION="2.23.3-r2"
#RUN set -exu \
#    && apk add --no-cache \
#    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
#    nix=${NIX_VERSION}

#
# Install nix (from upstream)
#
ARG CURL_VERSION="8.12.1-r1"
ARG SHADOW_VERSION="4.16.0-r1"
ARG XZ_VERSION="5.6.3-r0"
RUN set -exu \
    && apk add --no-cache \
    curl=${CURL_VERSION} \
    shadow=${SHADOW_VERSION} \
    xz=$XZ_VERSION
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
ARG NIX_DAEMON_ARGS="--debug --verbose"
ENV NIX_DAEMON_ARGS=${NIX_DAEMON_ARGS}
# Note: optimizing nix store takes a long time...
ARG NIX_STORE_OPTIMIZE=true
ENV NIX_STORE_OPTIMIZE=${NIX_STORE_OPTIMIZE}


#ARG NIX_CHANNEL="nixos-24.11"
ARG NIX_CHANNEL="nixpkgs-unstable"
# hadolint ignore=DL3004
RUN set -exu \
    && fork() { (setsid "$@" &); } && fork nix-daemon ${NIX_DAEMON_ARGS} \
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-channel --add "https://nixos.org/channels/${NIX_CHANNEL}" "nixpkgs"\
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-channel --update \
    && sudo -i -u "${NIX_USER_NAME}" \
    nix-env -iA nixpkgs.devenv \
    && nix-collect-garbage --delete-old \
    && if [ "${NIX_STORE_OPTIMIZE}" == "true" ]; then nix-store --optimise; fi \
    && nix-store --verify --check-contents

COPY --chown=${NIX_USER_NAME} \
    devenv.lock \
    devenv.nix \
    devenv.yaml \
    nix-dind/devenv.local.nix \
    "${NIX_USER_HOMEDIR}"/
COPY --chown=${NIX_USER_NAME} \
    nix-dind/devenv.local.nix \
    "${NIX_USER_HOMEDIR}"/nix-dind/

# hadolint ignore=DL3004
RUN set -exu \
    && fork() { (setsid "$@" &); } && fork nix-daemon  ${NIX_DAEMON_ARGS} \
    && sudo -i -u "${NIX_USER_NAME}" \
    devenv --verbose build \
    && nix-collect-garbage --delete-old \
    && if [ "${NIX_STORE_OPTIMIZE}" == "true" ]; then nix-store --optimise; fi \
    && nix-store --verify --check-contents

# For a FAT devenv base image comment/uncomment this:
# hadolint ignore=DL3004
RUN set -exu \
    && fork() { (setsid "$@" &); } && fork nix-daemon  ${NIX_DAEMON_ARGS} \
    && sudo -i -u "${NIX_USER_NAME}" \
    devenv --verbose shell -- true \
    && nix-collect-garbage --delete-old \
    && if [ "${NIX_STORE_OPTIMIZE}" == "true" ]; then nix-store --optimise; fi \
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
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
