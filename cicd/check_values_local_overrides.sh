#!/usr/bin/env bash
# Checks that local-override Helm values files contain no actual content.
#
# Four files are committed as empty templates and must stay that way:
#
#   charts/values-overwrites.yaml  the operator's last word, on a box or a laptop
#   charts/values-user.yaml        what `build-appliance-image --values/--set` writes
#   charts/values-up-flags.yaml    written by up.sh from its own flags
#   charts/values-appliance.yaml   written by nixos/repo.nix from the box's own facts
#
# The first three are also `--skip-worktree` (devenv.nix), so a local edit is
# invisible to git; the fourth deliberately is not, which makes this check the
# only thing standing between a seeded checkout's box-specific values and a
# commit. Any non-comment, non-blank line means content was accidentally staged.
#
# Usage:
#   ./check_values_local_overrides.sh <file1> [file2] ...
#
set -euo pipefail

exit_code=0
for file in "$@"; do
    violations=$(grep --line-number --extended-regexp --invert-match '^\s*(#.*)?$' "${file}" || true)
    if [[ -n "${violations}" ]]; then
        >&2 echo "ERROR: ${file} contains content that should not be committed:"
        >&2 echo "${violations}"
        >&2 echo "This file is a local-override template and must remain empty."
        >&2 echo "Put your local overrides there but do not stage or commit them."
        exit_code=1
    fi
done

exit "${exit_code}"
