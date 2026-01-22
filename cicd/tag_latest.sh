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

# enable minikube-env (if available)
if MINIKUBE_EVAL=$(minikube -p minikube docker-env 2>/dev/null); then
    eval "${MINIKUBE_EVAL}"
fi

# Tag as latest
docker tag "${SKAFFOLD_IMAGE}" "${IMAGE_REPO}:latest"