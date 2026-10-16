#!/usr/bin/env bash
set -euxo pipefail

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)
cd "${GIT_TOPLEVEL}"

# Every project is discovered from its pyproject.toml rather than listed here, so
# that a package added today is locked today. A hardcoded list is how the root
# lockfile went stale when nixos/ready was added: nothing pointed at the omission
# until the devenv refused to start.
#
# `--others --exclude-standard` as well as the index, which is the half that
# makes the sentence above true: `git ls-files` alone lists what is *tracked*,
# so a pyproject.toml that has been written and not yet `git add`ed is still
# skipped -- and that is exactly the state you are in when adding a package. The
# root lock then goes stale, and per CLAUDE.md a stale lock makes `poetry
# install` refuse, which breaks devenv for everyone until somebody regenerates
# it.
#
# Assigned before being split rather than piped: under `shellcheck -o all` a
# pipeline masks the exit status of everything but its last command, and a
# `git ls-files` that fails should stop the script rather than lock nothing.
MANIFESTS=$(git ls-files --cached --others --exclude-standard '*pyproject.toml')
if [[ -z "${MANIFESTS}" ]]; then
    echo "No pyproject.toml found anywhere - is this the Loom repository?" >&2
    exit 1
fi

DIRECTORIES=()
while IFS= read -r manifest; do
    DIRECTORIES+=("$(dirname "${manifest}")")
done <<< "${MANIFESTS}"

# `git ls-files` already sorts, so the only ordering left to impose is the two
# ends: common first, so dependent packages resolve against its updated lock, and
# the root project last, because it path-depends on all the others. One pass
# rather than three over the same list.
HEAD_PROJECTS=()
MIDDLE_PROJECTS=()
TAIL_PROJECTS=()
for dir in "${DIRECTORIES[@]}"; do
    case "${dir}" in
        backend/common) HEAD_PROJECTS+=("${dir}")   ;;
        .)              TAIL_PROJECTS+=("${dir}")   ;;
        *)              MIDDLE_PROJECTS+=("${dir}") ;;
    esac
done
PYTHON_PROJECTS=(
    ${HEAD_PROJECTS[@]+"${HEAD_PROJECTS[@]}"}
    ${MIDDLE_PROJECTS[@]+"${MIDDLE_PROJECTS[@]}"}
    ${TAIL_PROJECTS[@]+"${TAIL_PROJECTS[@]}"}
)

for dir in "${PYTHON_PROJECTS[@]}"; do
    (
        cd "${GIT_TOPLEVEL}/${dir}"
        poetry env remove --all || true
        poetry lock
    )
done
