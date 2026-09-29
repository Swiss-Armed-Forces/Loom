# Image version
ARG GOTENBERG_IMAGE_VERSION="8.36.0"
# Manifest-list digest, not a per-platform one: the old pin was the amd64
# manifest, so arm64 builds silently got amd64 contents.
ARG GOTENBERG_IMAGE_DIGEST="sha256:87c16b9f364279d321bc9772d31fa58aa6abe036423c270698bd636c3a8e9466"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/gotenberg/gotenberg:${GOTENBERG_IMAGE_VERSION}@${GOTENBERG_IMAGE_DIGEST}
