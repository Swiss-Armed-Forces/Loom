#!/usr/bin/env bash
# Run the inline-shell cap over the appliance's Nix modules.
#
# A wrapper so the git hook has a stable entry point that needs no interpreter
# path, matching cicd/check_resources.sh beside it. Everything of substance is
# in the Python; see the module docstring there for what the check is and why.
set -euo pipefail

CONTEXT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
readonly CONTEXT_DIR

exec python3 "${CONTEXT_DIR}/cicd/check_nix_inline_shell.py" "${CONTEXT_DIR}/nixos" "${@}"
