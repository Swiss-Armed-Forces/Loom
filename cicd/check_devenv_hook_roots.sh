#!/usr/bin/env bash
# Checks that no git hook bakes the build-time repository root into its entry.
#
# config.devenv.root is the tree that last entered devenv, and git shares
# .git/hooks across every worktree -- so a hook that interpolates it points the
# tools at that tree instead of the one the commit is made from. Hook entries
# therefore leave the root to cicd/run_hook_tool.sh, which resolves it at run
# time and substitutes it for %ROOT%. Everywhere else in devenv.nix -- env vars,
# processes, scripts -- the build-time root is the correct thing to use and
# stays allowed.
#
# CI cannot catch this: it runs a single checkout where config.devenv.root is
# the real root, so a reintroduced interpolation passes every pipeline.
#
# Usage:
#   ./check_devenv_hook_roots.sh
#
set -euo pipefail

nix_file="devenv.nix"

# An `entry = ...;` statement may be wrapped across several lines, so track the
# statement rather than grepping line by line. The create*Wrapper helpers build
# those entries and are held to the same rule.
violations=$(
    awk '
        /^[[:space:]]*(entry|create[A-Za-z]*Wrapper)[[:space:]]*=/ { region = 1 }
        region && /config\.devenv\.root/ { printf "%d: %s\n", NR, $0 }
        region && /;[[:space:]]*$/ { region = 0 }
    ' "${nix_file}"
)

if [[ -n "${violations}" ]]; then
    >&2 echo "ERROR: ${nix_file} bakes the build-time repository root into a git hook:"
    >&2 echo "${violations}"
    >&2 echo "Hooks must leave the root to cicd/run_hook_tool.sh: write %ROOT% in a"
    >&2 echo "wrapper argument, use createToolWrapper for a tool on PATH, and"
    >&2 echo "createRepoScriptWrapper for a script inside the repository."
    exit 1
fi
