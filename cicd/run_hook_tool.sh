#!/usr/bin/env bash
#
# Runs a git-hook tool against the files of one subdirectory, from inside that
# subdirectory.
#
# The repository root is resolved here, at hook run time, instead of being baked
# into the hook entry when devenv builds it. Git shares .git/hooks across every
# worktree, so the installed hooks belong to whichever tree last entered devenv
# -- a root fixed at build time points the tools at that tree rather than at the
# one the commit is being made from.
#
# %ROOT% in --command or in any --arg is replaced with that root, which is how a
# tool is handed a config file that lives at the top of the tree.
#
# Note git exports GIT_DIR while a commit runs, which makes `rev-parse
# --show-toplevel` report the working directory; that is the repository root
# here, because prek chdirs to the top level before running a hook.
#
# Usage:
#   ./run_hook_tool.sh --subdir backend/api --command black \
#       --arg --config --arg %ROOT%/pyproject.toml backend/api/api/main.py
#
set -euo pipefail

ROOT_PLACEHOLDER="%ROOT%"

SUBDIR=""
COMMAND=""
ARGS=()
FILES=()

usage(){
    cat <<EOF
Usage: $(basename "${0}") --subdir DIR --command CMD [--arg ARG]... [FILE...]

Runs CMD from inside DIR with every FILE rewritten relative to DIR; a FILE
outside DIR is skipped with a warning. Each ${ROOT_PLACEHOLDER} in CMD and in
every ARG is replaced with the root of the repository the hook ran in.

OPTIONS:
  --subdir DIR   directory to run CMD in, relative to the repository root
  --command CMD  tool to run, from PATH or as a path of its own
  --arg ARG      argument for CMD, placed before the file list; repeatable
  -h|--help      show this help
EOF
}

repository_root(){
    local root
    root="$(git rev-parse --show-toplevel)"
    if [[ ! -d "${root}" ]]; then
        echo >&2 "[!] Error: could not resolve the repository root"
        return 1
    fi
    printf '%s\n' "${root}"
}

main(){
    local root arg file
    local argv=()
    local relative_files=()

    if [[ -z "${SUBDIR}" ]]; then
        echo >&2 "[!] Error: --subdir is required"
        usage >&2
        return 1
    fi
    if [[ -z "${COMMAND}" ]]; then
        echo >&2 "[!] Error: --command is required"
        usage >&2
        return 1
    fi

    root="$(repository_root)"

    for arg in "${COMMAND}" "${ARGS[@]}"; do
        argv+=("${arg//"${ROOT_PLACEHOLDER}"/"${root}"}")
    done

    for file in "${FILES[@]}"; do
        if [[ "${file}" == "${SUBDIR}/"* ]]; then
            relative_files+=("${file#"${SUBDIR}/"}")
        else
            echo >&2 "[!] Warning: skipping file outside ${SUBDIR}: ${file}"
        fi
    done

    cd "${root}/${SUBDIR}"
    "${argv[@]}" "${relative_files[@]}"
}

while (( $# )); do
    case "${1}" in
        --subdir)
            shift
            SUBDIR="${1?Missing DIR}"
            shift
        ;;
        --command)
            shift
            COMMAND="${1?Missing CMD}"
            shift
        ;;
        --arg)
            shift
            ARGS+=("${1?Missing ARG}")
            shift
        ;;
        -h|--help)
            usage
            exit 0
        ;;
        -*)
            echo >&2 "[!] Error: unknown argument: ${1}"
            usage >&2
            exit 1
        ;;
        *)
            FILES+=("${1}")
            shift
        ;;
    esac
done

main
