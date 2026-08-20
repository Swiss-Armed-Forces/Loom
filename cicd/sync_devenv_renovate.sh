#!/usr/bin/env bash
set -euo pipefail

#
# Sync devenv.yaml renovate tracking comments with current devenv.lock revisions.
# Run this after `devenv update` so the tracking comments stay in sync.
#

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

for input in devenv git-hooks nixpkgs nixpkgs-python nixpkgs-stable nixpkgs-unstable; do
  rev=$(jq -r ".nodes.\"${input}\".locked.rev" "${GIT_TOPLEVEL}/devenv.lock")
  if [[ "${rev}" != "null" ]]; then
    sed -i "s/\(depName=devenv-${input} .*currentDigest=\)[a-f0-9]*/\1${rev}/" "${GIT_TOPLEVEL}/devenv.yaml"
  fi
done

echo "devenv.yaml tracking comments synced with devenv.lock"
