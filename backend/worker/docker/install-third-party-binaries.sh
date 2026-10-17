#!/usr/bin/env bash
#
# Installs the third-party binaries the worker image downloads from GitHub
# releases: trufflehog, ripsecrets and the seaweedfs `weed` client.
#
# Runs once while building backend/worker/Dockerfile. Versions, checksums and
# the target architecture arrive as arguments, so the Dockerfile keeps the
# pinned values and this file stays a plain script that linting and review can
# read.
#
# Every archive is checksum-verified before it is unpacked: the build must fail
# rather than install a binary that does not match the pinned digest.
set -euo pipefail

#
# Vars
#
# Passed by the Dockerfile from its ARGs, and checked below rather than
# defaulted: a missing one means the Dockerfile and this script have drifted
# apart, and an empty checksum verifies nothing.
TARGET_ARCH=""
TRUFFLEHOG_VERSION=""
TRUFFLEHOG_AMD64_SHA256=""
TRUFFLEHOG_ARM64_SHA256=""
RIPSECRETS_VERSION=""
RIPSECRETS_AMD64_SHA256=""
SEAWEEDFS_VERSION=""
SEAWEEDFS_AMD64_SHA256=""
SEAWEEDFS_ARM64_SHA256=""

BIN_DIR="/usr/local/bin"

#
# Usage
#
usage(){
    echo "usage: ${0} --target-arch ARCH \\"
    echo "           --trufflehog-version VERSION \\"
    echo "           --trufflehog-amd64-sha256 SHA256 \\"
    echo "           --trufflehog-arm64-sha256 SHA256 \\"
    echo "           --ripsecrets-version VERSION \\"
    echo "           --ripsecrets-amd64-sha256 SHA256 \\"
    echo "           --seaweedfs-version VERSION \\"
    echo "           --seaweedfs-amd64-sha256 SHA256 \\"
    echo "           --seaweedfs-arm64-sha256 SHA256"
    echo "  --target-arch ARCH                 Docker TARGETARCH: 'amd64' or 'arm64'"
    echo "  --trufflehog-version VERSION       trufflehog release tag, e.g. 'v3.90.6'"
    echo "  --trufflehog-amd64-sha256 SHA256   sha256 of the linux_amd64 trufflehog archive"
    echo "  --trufflehog-arm64-sha256 SHA256   sha256 of the linux_arm64 trufflehog archive"
    echo "  --ripsecrets-version VERSION       ripsecrets release version without the 'v'"
    echo "  --ripsecrets-amd64-sha256 SHA256   sha256 of the x86_64 ripsecrets archive"
    echo "  --seaweedfs-version VERSION        seaweedfs release tag"
    echo "  --seaweedfs-amd64-sha256 SHA256    sha256 of the linux_amd64 seaweedfs archive"
    echo "  --seaweedfs-arm64-sha256 SHA256    sha256 of the linux_arm64 seaweedfs archive"
    echo "  -h|--help                          show this help"
}

#
# Functions
#
unsupported_architecture() {
    echo >&2 "[!] Error: unsupported architecture: ${TARGET_ARCH}"
    exit 1
}

download_and_verify() {
    local url="${1}"
    local archive="${2}"
    local expected_sha256="${3}"
    local actual_sha256

    echo "[*] Downloading ${url}"
    curl --silent --show-error --fail --location "${url}" --output "${archive}"

    actual_sha256="$(sha256sum "${archive}")"
    actual_sha256="${actual_sha256%% *}"
    if [[ "${actual_sha256}" != "${expected_sha256}" ]]; then
        echo >&2 "[!] Error: checksum mismatch for ${url}"
        echo >&2 "    expected: ${expected_sha256}"
        echo >&2 "    actual:   ${actual_sha256}"
        exit 1
    fi
    echo "[*] Checksum verified: ${url}"
}

install_trufflehog() {
    local archive="/tmp/trufflehog.tar.gz"
    local arch_slug
    local expected_sha256

    case "${TARGET_ARCH}" in
        amd64)
            arch_slug="linux_amd64"
            expected_sha256="${TRUFFLEHOG_AMD64_SHA256}"
        ;;
        arm64)
            arch_slug="linux_arm64"
            expected_sha256="${TRUFFLEHOG_ARM64_SHA256}"
        ;;
        *)
            unsupported_architecture
        ;;
    esac

    download_and_verify \
        "https://github.com/trufflesecurity/trufflehog/releases/download/${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION#v}_${arch_slug}.tar.gz" \
        "${archive}" \
        "${expected_sha256}"

    tar -xzf "${archive}" -C "${BIN_DIR}" trufflehog
    rm "${archive}"

    # trufflehog on PATH is a wrapper around the real binary: --no-update stops
    # it from downloading a replacement for itself, which would run code the
    # pinned checksum above never covered.
    mv "${BIN_DIR}/trufflehog" "${BIN_DIR}/.trufflehog-wrapped"
    printf '#!/bin/sh\nexec %s/.trufflehog-wrapped --no-update "$@"\n' \
        "${BIN_DIR}" > "${BIN_DIR}/trufflehog"
    chmod +x "${BIN_DIR}/trufflehog"
    trufflehog --version
}

install_ripsecrets() {
    local archive="/tmp/ripsecrets.tar.gz"
    local release="ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu"

    if [[ "${TARGET_ARCH}" != "amd64" ]]; then
        echo "[*] Skipping ripsecrets: upstream publishes no linux ${TARGET_ARCH}"
        echo "    release artifact. ripsecrets_scan_task detects the missing binary"
        echo "    at runtime and reports 'not scanned' for every file."
        return
    fi

    download_and_verify \
        "https://github.com/sirwart/ripsecrets/releases/download/v${RIPSECRETS_VERSION}/${release}.tar.gz" \
        "${archive}" \
        "${RIPSECRETS_AMD64_SHA256}"

    tar -xzf "${archive}" -C /tmp
    mv "/tmp/${release}/ripsecrets" "${BIN_DIR}/ripsecrets"
    chmod +x "${BIN_DIR}/ripsecrets"
    rm -rf "${archive}" "/tmp/${release}"
    echo "[*] ripsecrets installed for ${TARGET_ARCH}"
}

install_seaweedfs() {
    local archive="/tmp/seaweedfs.tar.gz"
    local arch_slug
    local expected_sha256

    case "${TARGET_ARCH}" in
        amd64)
            arch_slug="linux_amd64"
            expected_sha256="${SEAWEEDFS_AMD64_SHA256}"
        ;;
        arm64)
            arch_slug="linux_arm64"
            expected_sha256="${SEAWEEDFS_ARM64_SHA256}"
        ;;
        *)
            unsupported_architecture
        ;;
    esac

    download_and_verify \
        "https://github.com/seaweedfs/seaweedfs/releases/download/${SEAWEEDFS_VERSION}/${arch_slug}.tar.gz" \
        "${archive}" \
        "${expected_sha256}"

    tar -xzf "${archive}" -C "${BIN_DIR}" weed
    chmod +x "${BIN_DIR}/weed"
    rm "${archive}"
}

#
# Argument parsing
#
while [[ $# -gt 0 ]]; do
    case "${1}" in
        --target-arch)
            shift
            TARGET_ARCH="${1?Missing ARCH}"
            shift
        ;;
        --trufflehog-version)
            shift
            TRUFFLEHOG_VERSION="${1?Missing VERSION}"
            shift
        ;;
        --trufflehog-amd64-sha256)
            shift
            TRUFFLEHOG_AMD64_SHA256="${1?Missing SHA256}"
            shift
        ;;
        --trufflehog-arm64-sha256)
            shift
            TRUFFLEHOG_ARM64_SHA256="${1?Missing SHA256}"
            shift
        ;;
        --ripsecrets-version)
            shift
            RIPSECRETS_VERSION="${1?Missing VERSION}"
            shift
        ;;
        --ripsecrets-amd64-sha256)
            shift
            RIPSECRETS_AMD64_SHA256="${1?Missing SHA256}"
            shift
        ;;
        --seaweedfs-version)
            shift
            SEAWEEDFS_VERSION="${1?Missing VERSION}"
            shift
        ;;
        --seaweedfs-amd64-sha256)
            shift
            SEAWEEDFS_AMD64_SHA256="${1?Missing SHA256}"
            shift
        ;;
        --seaweedfs-arm64-sha256)
            shift
            SEAWEEDFS_ARM64_SHA256="${1?Missing SHA256}"
            shift
        ;;
        -h|--help)
            usage
            exit 0
        ;;
        *)
            echo >&2 "[!] Error: unknown argument: ${1}"
            usage >&2
            exit 1
        ;;
    esac
done

if [[ -z "${TARGET_ARCH}" \
    || -z "${TRUFFLEHOG_VERSION}" \
    || -z "${TRUFFLEHOG_AMD64_SHA256}" \
    || -z "${TRUFFLEHOG_ARM64_SHA256}" \
    || -z "${RIPSECRETS_VERSION}" \
    || -z "${RIPSECRETS_AMD64_SHA256}" \
    || -z "${SEAWEEDFS_VERSION}" \
    || -z "${SEAWEEDFS_AMD64_SHA256}" \
    || -z "${SEAWEEDFS_ARM64_SHA256}" ]]; then
    echo >&2 "[!] Error: every --*-version, --*-sha256 and --target-arch is required"
    usage >&2
    exit 1
fi

#
# Main
#
install_trufflehog
install_ripsecrets
install_seaweedfs
