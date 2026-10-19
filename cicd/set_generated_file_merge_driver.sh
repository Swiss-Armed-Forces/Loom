#!/usr/bin/env bash
#
# Teaches this repository how to merge the files CI generates.
#
# THIRD-PARTY.md, its Frontend/public/ copy and THIRD-PARTY.lock are written by
# `generate-third-party` and committed by a pipeline on every branch, so two
# branches that have each run a pipeline always differ in them -- and a merge of
# main into a feature branch conflicts on a file nobody edited and whose
# resolution nobody can review. Both sides are correct for the branch that
# produced them, which is what makes the conflict unanswerable by hand.
#
# .gitattributes points those three paths at the `keep-ours` driver configured
# here, which keeps the copy of the branch being merged into. That is not a
# judgement that one scan is better than the other: the lock records which
# inputs produced each section, so the next pipeline recomputes the keys, finds
# the ones the merge changed, rescans exactly those images and commits the
# correction. Resolving by hand did the same thing with more steps.
#
# `true` as the driver leaves git's %A -- our version, already in the working
# tree -- in place and exits 0, which is how a merge driver says "this is the
# result". All three paths take it together so that the lock and the document it
# keys cannot end up from different sides of the merge.
#
# Written to --local rather than --worktree: unlike core.hooksPath (see
# set_worktree_hooks_path.sh) this is the same answer in every checkout, and the
# local config is shared by every worktree of the repository.
#
# A checkout that has never entered devenv has no driver by this name. Git falls
# back to the ordinary three-way merge there, silently, and conflicts the way it
# always did -- the files stay mergeable by hand, and nothing is lost by the
# attribute being there.
#
set -euo pipefail

readonly DRIVER="merge.keep-ours"

# Shown in `git config --list` and nowhere else; git requires it before it will
# use the driver.
readonly DRIVER_NAME="keep this checkout's copy of a generated file"

# Written only when it is not already what it should be. The local config is one
# file shared by every worktree of the repository, `git config` takes a lock on
# it with no retry, and several checkouts enter devenv at once on a machine
# where each one is somebody's working tree -- so a run that has nothing to
# change should not be taking that lock at all.
set_once() {
    local key
    local value
    key="${1}" && shift
    value="${1}" && shift

    if [[ "$(git config --local --get "${key}" || true)" == "${value}" ]]; then
        return 0
    fi

    git config --local "${key}" "${value}"
}

main() {
    # Not a repository: nothing to configure, and nothing to complain about.
    # devenv is entered from export tarballs and CI checkouts too.
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        return 0
    fi

    set_once "${DRIVER}.name" "${DRIVER_NAME}"
    set_once "${DRIVER}.driver" true
}

main "$@"
