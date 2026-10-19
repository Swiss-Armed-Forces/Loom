#!/bin/sh
#
# Copies the preloaded Ollama model store into the runtime's model storage.
#
# Runs as the `copy-ollama-models` initContainer, mounted from the ConfigMap in
# charts/templates/ollama/_configMap.yaml. Everything the chart has to say to it
# arrives as arguments, so this file stays a plain script that linting and review
# can read. The models image is Alpine and carries no bash, so this is POSIX sh
# against busybox.
set -eu

#
# Vars
#
# Passed by the initContainer from the Deployment template, and checked below
# rather than defaulted: a missing one means the template and this script have
# drifted apart, and a copy into the wrong place is worse than a container that
# fails loudly.
SOURCE=""
DESTINATION=""

# Scratch file each pass below writes its `find` results into, and reads back by
# redirection rather than through a pipe: a `while` on the right of a pipe runs
# in a subshell, which swallows the exit status this script relies on. The two
# passes run one after the other, so one file serves both.
FILE_LIST="$(mktemp)"

# Suffix the in-progress copy carries. Never collides with a real entry: a blob
# is named for its own digest and a manifest for its tag.
PARTIAL_SUFFIX=".partial"

#
# Usage
#
usage(){
    echo "usage: ${0} --source DIR --destination DIR"
    echo "  --source DIR        model store to copy from"
    echo "  --destination DIR   model store to copy into"
    echo "  -h|--help           show this help"
}

#
# Functions
#
# Copies one file into place, or leaves it alone when it is already there whole.
#
# Sizes decide that, not modification times. A destination left half-written
# carries the time it was written, which is newer than the source it came from,
# so an mtime comparison skips precisely the file that has to be copied again.
#
# The copy lands on a temporary name beside its destination and is renamed
# afterwards. Both are on one filesystem, so the rename is atomic: a run that
# dies partway -- the memory limit has to hold the dirty page cache of a
# multi-gigabyte blob -- leaves nothing short under the name Ollama opens, and
# the next run copies it again.
copy_file() {
    source_file="${1}"
    destination_file="${2}"
    partial_file="${destination_file}${PARTIAL_SUFFIX}"

    source_size="$(stat -c %s "${source_file}")"
    destination_size=""
    if [ -f "${destination_file}" ]; then
        destination_size="$(stat -c %s "${destination_file}")"
    fi

    if [ "${source_size}" = "${destination_size}" ]; then
        echo "[-] up to date: ${destination_file}"
        return 0
    fi

    echo "[*] copying ${source_size} bytes: ${source_file}"
    rm -f "${partial_file}"
    cp "${source_file}" "${partial_file}"
    mv "${partial_file}" "${destination_file}"
}

# Drops what an interrupted run left behind. The rename keeps those files out of
# Ollama's way, but nothing else ever removes them, and the volume is sized for
# the models rather than for their remains.
discard_partial_files() {
    find "${DESTINATION}" -type f -name "*${PARTIAL_SUFFIX}" > "${FILE_LIST}"

    while IFS= read -r partial_file; do
        echo "[*] discarding interrupted copy: ${partial_file}"
        rm -f "${partial_file}"
    done < "${FILE_LIST}"
}

copy_tree() {
    find "${SOURCE}" -type f > "${FILE_LIST}"

    while IFS= read -r source_file; do
        relative_path="${source_file#"${SOURCE}"/}"
        destination_file="${DESTINATION}/${relative_path}"
        destination_dir="$(dirname "${destination_file}")"

        mkdir -p "${destination_dir}"
        copy_file "${source_file}" "${destination_file}"
    done < "${FILE_LIST}"
}

#
# Atexit
#
atexit() {
    rm -f "${FILE_LIST}"
}
trap atexit EXIT

#
# Argument parsing
#
while [ $# -gt 0 ]; do
    case "${1}" in
        --source)
            shift
            SOURCE="${1?Missing SOURCE}"
            shift
        ;;
        --destination)
            shift
            DESTINATION="${1?Missing DESTINATION}"
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

if [ -z "${SOURCE}" ] || [ -z "${DESTINATION}" ]; then
    echo >&2 "[!] Error: --source and --destination are required"
    usage >&2
    exit 1
fi

if [ ! -d "${SOURCE}" ]; then
    echo >&2 "[!] Error: --source '${SOURCE}' is not a directory"
    exit 1
fi

if [ ! -d "${DESTINATION}" ]; then
    echo >&2 "[!] Error: --destination '${DESTINATION}' is not a directory"
    exit 1
fi

# Trailing slashes are stripped so that the path each source file keeps below
# SOURCE is the path it takes below DESTINATION.
SOURCE="${SOURCE%/}"
DESTINATION="${DESTINATION%/}"

#
# Main
#
discard_partial_files
copy_tree
