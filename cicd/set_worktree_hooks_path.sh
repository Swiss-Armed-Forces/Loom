#!/usr/bin/env bash
#
# Points this checkout's git hooks at its own git directory.
#
# Git shares .git/hooks across every worktree, and git-hooks.nix pins
# core.hooksPath to that shared directory on each install, so the hooks belong
# to whichever checkout last entered devenv. A commit made anywhere is then
# validated by that tree's hook set, excludes and pinned tool versions, and
# removing that tree leaves the remaining ones pointing at a config file that no
# longer exists.
#
# The value written is the hooks subdirectory of the tree's *own* git directory:
#
#   main worktree    .git/hooks                     (unchanged)
#   linked worktree  .git/worktrees/<name>/hooks
#
# Both live inside the git directory, so neither needs a .gitignore entry.
#
# This is written to the per-worktree config, which requires the
# extensions.worktreeConfig repository extension and outranks the --local value
# git-hooks.nix writes back after installing. The script runs before
# devenv:git-hooks:install so that the first entry into a tree already installs
# into the right place.
#
set -euo pipefail

main() {
    local git_dir

    # Not a repository: nothing to configure, and nothing to complain about.
    # devenv is entered from export tarballs and CI checkouts too.
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        return 0
    fi

    # Per-worktree configuration is opt-in per repository and only has to be
    # enabled once; enabling it again is a no-op.
    git config extensions.worktreeConfig true

    git_dir="$(git rev-parse --absolute-git-dir)"
    if [[ ! -d "${git_dir}" ]]; then
        echo >&2 "[!] Error: could not resolve the git directory of this checkout"
        return 1
    fi

    git config --worktree core.hooksPath "${git_dir}/hooks"
}

main "$@"
