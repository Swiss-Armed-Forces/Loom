#!/usr/bin/env bash

set -euo pipefail

# Configuration
MAIN_BRANCH="${MAIN_BRANCH:-main}"
DRY_RUN=false
DELETE_MODE="all"  # Options: all, squash, merged

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Delete local git branches that have been merged into the main branch.

OPTIONS:
    -n, --dry-run           Dry run mode (don't actually delete branches)
    -m, --main-branch NAME  Specify main branch (default: main)
    -t, --type TYPE         Delete type: all, squash, merged (default: all)
    -h, --help              Show this help message

DELETE TYPES:
    all     - Delete both squash-merged and regularly merged branches
    squash  - Delete only squash-merged branches
    merged  - Delete only regularly merged branches

EXAMPLES:
    $0 -n                   # Dry run to see what would be deleted
    $0 -m develop           # Use 'develop' as main branch
    $0 -t squash            # Only delete squash-merged branches
    $0 -n -t merged         # Dry run for regularly merged branches
    $0                      # Delete all merged branches

EOF
}

delete_squash_merged_branches() {
    local main_branch="$1"
    local dry_run="$2"
    local current_branch

    # Get current branch to avoid deleting it
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    echo "Checking for squash-merged branches (current branch: ${current_branch})..."

    # Get all local branches
    git for-each-ref refs/heads/ "--format=%(refname:short)" | while read -r branch; do
        # Skip the main branch and current branch
        if [[ "${branch}" == "${main_branch}" ]] || [[ "${branch}" == "${current_branch}" ]]; then
            continue
        fi

        # Find the merge base between main and the branch
        local merge_base
        merge_base=$(git merge-base "${main_branch}" "${branch}")

        # Get the tree of the branch
        local branch_tree
        branch_tree=$(git rev-parse "${branch}^{tree}")

        # Create a temporary commit with the branch's tree and merge base as parent
        local temp_commit
        temp_commit=$(git commit-tree "${branch_tree}" -p "${merge_base}" -m "_")

        # Check if the branch changes are already in main
        local cherry_result
        cherry_result=$(git cherry "${main_branch}" "${temp_commit}")

        # If cherry returns a line starting with "-", the branch is merged
        if [[ "${cherry_result}" == "-"* ]]; then
            if [[ "${dry_run}" == "true" ]]; then
                echo "[DRY RUN] Would delete squash-merged branch: ${branch}"
            else
                echo "Deleting squash-merged branch: ${branch}"
                git branch -D "${branch}"
            fi
        fi
    done
}

delete_regularly_merged_branches() {
    local main_branch="$1"
    local dry_run="$2"
    local current_branch

    # Get current branch to avoid deleting it
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    echo "Checking for regularly merged branches (current branch: ${current_branch})..."

    # Get merged branches, excluding protected branches
    local branches_to_delete
    branches_to_delete=$(git branch --merged "${main_branch}" | grep -Ev "(^\*|^\+)")

    if [[ -z "${branches_to_delete}" ]]; then
        echo "No regularly merged branches to delete"
        return
    fi

    while IFS= read -r branch; do
        # Trim whitespace
        branch=$(echo "${branch}" | xargs)

        # Skip the main branch and current branch
        if [[ "${branch}" == "${main_branch}" ]] || [[ "${branch}" == "${current_branch}" ]]; then
            continue
        fi

        if [[ "${dry_run}" == "true" ]]; then
            echo "[DRY RUN] Would delete regularly merged branch: ${branch}"
        else
            echo "Deleting regularly merged branch: ${branch}"
            git branch -d "${branch}"
        fi
    done <<< "${branches_to_delete}"
}

#
# Argument parsing
#

while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            usage
            exit 0
        ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
        ;;
        -m|--main-branch)
            shift
            MAIN_BRANCH="${1}"
            shift
        ;;
        -t|--type)
            shift
            DELETE_MODE="${1}"
            shift
        ;;
        *)
            >&2 echo "Unknown option: ${1}"
            >&2 echo "Use -h or --help for usage information"
            exit 1
        ;;
    esac
done

#
# Main
#

if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY RUN MODE - No branches will be deleted"
fi

case "${DELETE_MODE}" in
    all)
        delete_squash_merged_branches "${MAIN_BRANCH}" "${DRY_RUN}"
        echo ""
        delete_regularly_merged_branches "${MAIN_BRANCH}" "${DRY_RUN}"
    ;;
    squash)
        delete_squash_merged_branches "${MAIN_BRANCH}" "${DRY_RUN}"
    ;;
    merged)
        delete_regularly_merged_branches "${MAIN_BRANCH}" "${DRY_RUN}"
    ;;
    *)
        >&2 echo "Error: Invalid delete mode '${DELETE_MODE}'"
        >&2 echo "Valid options: all, squash, merged"
        exit 1
    ;;
esac
