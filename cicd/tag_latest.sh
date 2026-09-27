#!/usr/bin/env bash
# This script is meant to be used as skaffold
# after-build lifecycle hook.
# see:
# - https://skaffold-latest.firebaseapp.com/docs/pipeline-stages/lifecycle-hooks/
set -euo pipefail

#
# Env
#
SKAFFOLD_IMAGE="${SKAFFOLD_IMAGE?Missing SKAFFOLD_IMAGE}"
SKAFFOLD_IMAGE_REPO="${SKAFFOLD_IMAGE_REPO?Missing SKAFFOLD_IMAGE_REPO}"

#
# Computed
#
# Note: We cannot use SKAFFOLD_IMAGE_REPO with Skaffold v2.17.0 because it incorrectly
# strips the image name from the repository path. For example:
# Expected: registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/traefik
# Actual:   registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom
# This appears to be a bug in v2.17.0 where SKAFFOLD_IMAGE_REPO only includes the
# registry and project path, omitting the final image name component.
#
# Extract repository by removing tag and digest from SKAFFOLD_IMAGE
IMAGE_REPO="${SKAFFOLD_IMAGE%%:*}"  # Remove everything after first ':'
IMAGE_REPO="${IMAGE_REPO%%@*}"      # Remove everything after first '@'

# A `:latest` alias can only point at an image in the local daemon store, and a
# multi-platform build never leaves one under SKAFFOLD_IMAGE. Skaffold builds each
# platform separately under a derived tag - "<tag>_linux_amd64", "<tag>_linux_arm64"
# (build/platform.go, buildImageForPlatforms) - pushes those, then assembles the
# manifest list itself from the registry copies (docker/manifest_list.go,
# CreateManifestList). Nothing is ever tagged "<tag>" locally.
#
# Note there is deliberately no check for a "_linux_<arch>" suffix here: this hook
# runs once per artifact and is handed the base tag, because build/builder_mux.go
# builds its hook environment from `tag` before the per-platform suffix is derived.
# A platform-suffixed SKAFFOLD_IMAGE never reaches this script.
if [[ "${SKAFFOLD_PLATFORM:-}" == *","* ]]; then
    echo "[*] Skipping tag_latest for multi-platform build: ${SKAFFOLD_PLATFORM}"
    exit 0
fi

# enable minikube-env (if available)
if MINIKUBE_EVAL=$(minikube -p minikube docker-env 2>/dev/null); then
    eval "${MINIKUBE_EVAL}"
fi

# Tag as latest. Every build that reaches this point is single-platform, so the
# image must be in the local store - a miss means the build did not do what we
# think it did, and silently skipping would leave a stale :latest behind.
docker tag "${SKAFFOLD_IMAGE}" "${IMAGE_REPO}:latest"
