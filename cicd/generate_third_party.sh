#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
SYFT_TEMPLATE="${SCRIPT_DIR}/syft-template.txt"
THIRD_PARTY_LICENCES="THIRD-PARTY.md"
THIRD_PARTY_LICENCES_PROGRESS="THIRD-PARTY.md.progress"
THIRD_PARTY_CACHE_DIR="${THIRD_PARTY_CACHE_DIR:-third-party-cache}"

TRAEFIK_SKAFFOLD_CMD="${TOPLEVEL_DIR}/traefik/skaffold"
# We need this because some images ore too big for /tmp (RAM)
SYFT_TMPDIR="$(mktemp --directory --tmpdir="${PWD}" ".syft-tmp.XXXXXXX" )"


VERBOSE=false
MINIKUBE_ENABLE=false
MINIKUBE_EVAL=""
ACTION="generate_third_party_licenses"

PROFILE="prod"

component_licenses(){
    >&3 echo "[*] Getting: component_licenses"
    (
        cd "${TOPLEVEL_DIR}"

        shopt -s nullglob
        local license
        for license in  */"${THIRD_PARTY_LICENCES}"; do
            local component_name
            component_name="$(dirname "${license}")"

            echo
            echo "### ${component_name}"
            echo
            cat "${license}"
            echo
        done
    )
}


get_image_tags(){
    jq \
        --raw-output \
        '.builds[].tag'
}

# build & list all images
list_all_images(){
    # Traefik
    (
        cd "${TOPLEVEL_DIR}/traefik"
        "${TRAEFIK_SKAFFOLD_CMD}" \
            build \
            --quiet \
            --profile "${PROFILE}" \
        | get_image_tags
    )

    # Application
    (
        cd "${TOPLEVEL_DIR}"
        skaffold \
            build \
            --quiet \
            --profile "${PROFILE}" \
        | get_image_tags
    )
}

syft_call() {
    local image
    image="${1}" && shift

    local syft_output
    syft_output=$(
        TMPDIR="${SYFT_TMPDIR}" \
        syft scan \
            --output template \
            --template "${SYFT_TEMPLATE}" \
            "docker:${image}"
    )

    # test if syft_output is empty
    # we need to this here because syft does
    # not always return a proper exit status on error.
    # For example on signal SIGINT (CTRL+C) syft exits with 0.
    if [[ -z "${syft_output}" ]]; then
        >&3 echo "[!] No output from syft scan"
        return 1
    fi

    # Return the result
    echo "${syft_output}"
}

scan_image(){
    local image
    image="${1}" && shift

    local image_name
    image_name="${image%%:*}"

    >&3 echo "[*] Scanning image: ${image}"

    echo
    echo "### ${image_name}"
    echo
    syft_call "${image}"
}

get_scan_image_cache_file(){
    local image
    image="${1}" && shift

    local cache_dir
    cache_dir="${THIRD_PARTY_CACHE_DIR}/scan_image"
    mkdir -p "${cache_dir}"

    local image_directory_safe
    image_directory_safe="$(echo "${image}" | tr '/:' '_')"

    echo "${cache_dir}/${image_directory_safe}.txt"
}

container_licenses() {
    >&3 echo "[*] Getting: container_licenses"
    (
        >&3 echo "[*] Listing all images"
        local all_images
        all_images=$(list_all_images)
        readarray -t -d '' all_images < <(xargs --no-run-if-empty printf '%s\0' <<<"${all_images:-}" || true)

        >&3 echo "[*] Scanning all images"
        local image
        for image in "${all_images[@]}"; do
            local cache_file
            cache_file="$(get_scan_image_cache_file "${image}")"

            if [[ -f "${cache_file}" ]]; then
                >&3 echo "[*] Using cache for image: '${image}'"
                cat "${cache_file}"
                continue
            fi

            local scan_image_output
            scan_image_output="$(scan_image "${image}")"
            echo "${scan_image_output}" > "${cache_file}"
            echo "${scan_image_output}"
        done
    )
}

generate_third_party_licenses() {
    echo "[*] Running: generate_third_party_licenses"
    {
        echo '# Third Party Licenses'
        echo '<!-- markdownlint-disable -->'
        echo 'This document serves to provide a comprehensive overview of all third-party software'
        echo 'components utilized in the development and operation of the "Loom" product.'
        echo 'Our intent is to maintain transparency and adhere strictly to the licensing terms'
        echo 'associated with each incorporated software package.'
        echo
        echo 'Within this file, you will find a detailed list of the open-source and proprietary'
        echo 'software libraries, frameworks, and tools that are integrated into Loom, along with'
        echo 'their respective licenses.'
        echo
        echo 'We are committed to respecting the intellectual property rights of others and ensuring'
        echo 'full compliance with all applicable license obligations.'
        echo
        echo 'Should you identify any instance of potential license infringement or trademark violation'
        echo 'related to the third-party software listed herein, we encourage you to promptly notify'
        echo 'the owners of "Loom" by opening a new issue via the following link:'
        echo
        echo '* [Loom Issue Tracker](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/new)'
        echo
        echo 'Your diligence in bringing such matters to our attention is greatly appreciated and will'
        echo 'enable us to take appropriate and timely action to rectify any concerns.'
        echo
        echo "## Components"
        echo
        component_licenses
        echo
        echo "## Python"
        echo
        pip-licenses \
            --order=license \
            --format=markdown
        echo
        echo "## JavaScript"
        echo
        license-report \
            --package "${FRONTEND_DIR}/package.json"  \
            --output markdown \
            --fields name \
            --fields licenseType \
            --fields installedVersion
        echo
        echo "## Container"
        echo
        container_licenses
    } \
    3>&1 \
    > "${THIRD_PARTY_LICENCES_PROGRESS}"
    # copy to final location
    mv "${THIRD_PARTY_LICENCES_PROGRESS}" "${THIRD_PARTY_LICENCES}"
}

#
# Atexit Handler
#

atexit(){
    echo "[*] Exiting.."
    rm -rf \
        "${THIRD_PARTY_LICENCES_PROGRESS}" \
        "${SYFT_TMPDIR}"
}
trap atexit EXIT

#
# Usage
#

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -h|--help               print this help"
    echo "  -m|--minikube           enable minikube environment"
    echo "  -v|--verbose            make verbose"
}

#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h|--help)
        usage
        exit 0
        ;;
    -v|--verbose)
        VERBOSE=true
        ;;
    -m|--minikube)
        MINIKUBE_ENABLE=true
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

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

if [[ "${MINIKUBE_ENABLE}" = true ]]; then
    MINIKUBE_EVAL=$(minikube -p minikube docker-env)
    eval "${MINIKUBE_EVAL}"
fi

"${ACTION}" "${ARGS[@]}"