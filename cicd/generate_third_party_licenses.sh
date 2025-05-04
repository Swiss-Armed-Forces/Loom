#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
SYFT_TEMPLATE="${SCRIPT_DIR}/syft-template.txt"
THIRD_PARTY_LICENCES="THIRD-PARTY.md"
THIRD_PARTY_LICENCES_OUTPUT="${TOPLEVEL_DIR}/${THIRD_PARTY_LICENCES}"
TRAEFIK_SKAFFOLD_CMD="${TOPLEVEL_DIR}/traefik/skaffold"
# We need this because some images ore too big for /tmp (RAM)
SYFT_TMPDIR="$(mktemp --directory --tmpdir="${PWD}" ".syft-tmp.XXXXXXX" )"
#NIX_DIND_IMAGE="registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/nix-dind:latest"

VERBOSE=false
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


filter_images(){
    sed \
        --quiet \
        --regexp-extended \
        --expression 's/\s*- .+ -> (.+)/\1/p'
}

# build & list all images
list_all_images(){
    # Skipping for now: takes too long
    #echo "${NIX_DIND_IMAGE}"

    # Traefik
    (
        cd "${TOPLEVEL_DIR}/traefik"
        "${TRAEFIK_SKAFFOLD_CMD}" \
            build \
            --profile "${PROFILE}" \
        | filter_images
    )

    # Application
    (
        cd "${TOPLEVEL_DIR}"
        skaffold \
            build \
            --profile "${PROFILE}" \
        | filter_images
    )
}

container_licenses() {
    >&3 echo "[*] Getting: container_licenses"
    (
        local minikube_eval
        minikube_eval=$(minikube -p minikube docker-env)
        eval "${minikube_eval}"

        local image
        for image in $(list_all_images); do
            local image_name
            image_name="${image%:*}"

            >&3 echo "[*] Scanning image: ${image}"

            echo
            echo "### ${image_name}"
            echo
            TMPDIR="${SYFT_TMPDIR}" \
                syft scan \
                    --output template \
                    --template "${SYFT_TEMPLATE}" \
                    "docker:${image}"
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
    > "${THIRD_PARTY_LICENCES_OUTPUT}"
}

#
# Atexit Handler
#

atexit(){
    echo "[*] Exiting.."
    rm -rf "${SYFT_TMPDIR}"
}
trap atexit EXIT

#
# Usage
#

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -h   |--help                        print this help"
    echo "  -v   |--verbose                     make verbose"
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
    -v | --verbose)
        VERBOSE=true
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

"${ACTION}" "${ARGS[@]}"
