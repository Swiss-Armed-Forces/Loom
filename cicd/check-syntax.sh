#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
GIT_TOPLEVEL=$(git rev-parse --show-toplevel)
TOP_PYPROJECT_TOML="${GIT_TOPLEVEL}/pyproject.toml"

RUN_PYTHON_LINT=true
PYTHON_PROJECTS="$(git -C "${GIT_TOPLEVEL}" ls-files '**/pyproject.toml')"
readarray -t PYTHON_PROJECTS <<<"${PYTHON_PROJECTS}"
PYTHON_SOURCES_IGNORES=(.pylintrc)

RUN_TYPESCRIPT_LINT=true
TYPESCRIPT_PROJECTS="$(git -C "${GIT_TOPLEVEL}" ls-files '**/package.json')"
readarray -t TYPESCRIPT_PROJECTS <<<"${TYPESCRIPT_PROJECTS}"

DO_FIX=false
VERBOSE=false

when_fixing() {
    if [[ "${DO_FIX}" = false ]]; then
        return 1
    fi
    if [[ "${#@}" -gt 0 ]]; then
        echo "${@}"
    fi
}

when_not_fixing() {
    if [[ "${DO_FIX}" = true ]]; then
        return 1
    fi
    if [[ "${#@}" -gt 0 ]]; then
        echo "${@}"
    fi
}

run_poetry_tool() {
    local cmd
    cmd=("${@}")

    echo "Running: ${cmd[0]}"
    poetry \
        -C "${GIT_TOPLEVEL}" \
        run "${cmd[@]}"
}

# In this function we use the: when_fixing and when_not_fixing
# functions whichare designed to be used with word splitting.
# Hence, we have to disable those shellcheck checkers
# shellcheck disable=SC2046,SC2312
process_python_files() {

    local files
    files=("${@}")

    local project
    project=$(basename "$(pwd)")

    echo "processing files: ${files[*]}"

    # hybrid: checkers / fixers
    run_poetry_tool \
        isort \
        --config-root "${GIT_TOPLEVEL}" \
        --resolve-all-configs \
        $(when_not_fixing --check-only) \
        "${files[@]}"

    run_poetry_tool \
        autoflake \
        --config "${TOP_PYPROJECT_TOML}" \
        $(when_not_fixing --check-diff) \
        "${files[@]}"

    run_poetry_tool \
        docformatter \
        --config "${TOP_PYPROJECT_TOML}" \
        $(when_not_fixing --check) \
        $(when_not_fixing --diff) \
        "${files[@]}"

    run_poetry_tool \
        black \
        --config "${TOP_PYPROJECT_TOML}" \
        --preview \
        $(when_not_fixing --check) \
        $(when_not_fixing --diff) \
        "${files[@]}"

    # only: checkers
    run_poetry_tool \
        flake8 \
        --config "${GIT_TOPLEVEL}/.flake8" \
        "${files[@]}"

    run_poetry_tool \
        pylint \
        --rcfile "${GIT_TOPLEVEL}/.pylintrc" \
        "${files[@]}"

    run_poetry_tool \
        mypy \
        -p "${project}" \
        --exclude "tests/*"
}

process_python_project() {
    local project
    project="${1}" && shift

    local dir
    dir=$(dirname "${project}")

    echo "processing project: ${dir}"
    (
        cd "${GIT_TOPLEVEL}/${dir}"

        local python_sources
        python_sources=$("${SCRIPT_DIR}/find_file_of_type.sh" '.' '(python|\.py)' "${PYTHON_SOURCES_IGNORES[@]}")
        readarray -t python_sources <<<"${python_sources}"

        process_python_files "${python_sources[@]}"
    )
}

run_pnpm_tool() {
    local cmd
    cmd=("${@}")

    echo "Running: ${cmd[0]}"
    pnpm \
        exec "${cmd[@]}"
}

process_typescript_project() {
    local project
    project="${1}" && shift

    local dir
    dir=$(dirname "${project}")

    echo "processing project: ${dir}"
    (
        cd "${GIT_TOPLEVEL}/${dir}"

        if [[ "${DO_FIX}" = true ]]; then
            pnpm run lint:fix
        else
            pnpm run lint
        fi
    )
}

usage() {
    echo "usage: $0 [OPTIONS] [PROJECTS]"
    echo
    echo "With OPTIONS:"
    echo "  -f |--fix               try auto-fix issues"
    echo "  -v |--verbose           make verbose"
    echo "  -sp|--skip-python       skip python project linting"
    echo "  -st|--skip-typescript   skip typescript project linting"
    echo "  -h |--help              print this help"
    echo
    echo "With PROJECTS:"
    echo "  Python project to check. Must contain pyproject.toml"
}

#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h | --help)
        usage
        exit 0
        ;;
    -f | --fix)
        DO_FIX=true
        ;;
    -v | --verbose)
        VERBOSE=true
        ;;
    -sp | --skip-python)
        RUN_PYTHON_LINT=false
        ;;
    -st | --skip-typescript)
        RUN_TYPESCRIPT_LINT=false
        ;;
    *)
        ARGS+=("${1}")
        ;;
    esac
    shift
done

#
# Main
#

SUCCESS=true

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

if [[ "${#ARGS[@]}" -gt 0 ]]; then
    PYTHON_PROJECTS=()
    for arg in "${ARGS[@]}"; do
        pyproject_toml="${arg}/pyproject.toml"
        package_json="${arg}/package.json"
        if [[ -f "${pyproject_toml}" ]]; then
            PYTHON_PROJECTS=("${pyproject_toml}")
        elif [[ -f "${package_json}" ]]; then
            TYPESCRIPT_PROJECTS=("${package_json}")
        else
            echo 1>&2 "Error: missing pyproject.toml or package.json in: ${arg}"
            exit 1
        fi

    done
fi

if [[ "${RUN_PYTHON_LINT}" = true ]]; then
    for project in "${PYTHON_PROJECTS[@]}"; do
        process_python_project "${project}"
    done
fi

if [[ "${RUN_TYPESCRIPT_LINT}" = true ]]; then
    for project in "${TYPESCRIPT_PROJECTS[@]}"; do
        process_typescript_project "${project}"
    done
fi

if [[ "${SUCCESS}" != true ]]; then
    exit 1
fi
