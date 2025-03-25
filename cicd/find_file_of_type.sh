#!/usr/bin/env bash
# shellcheck disable=SC2312,SC2016,SC2310
# Find all files of a given type, use file -b and file -bi to get a type of a file
# from: https://unix.stackexchange.com/questions/483871/how-to-find-files-by-file-type
#
# Usage: search_dir file_type ignores
set -euo pipefail

# Arguments
SEARCH_DIR="${1?Missing SEARCH_DIR}" && shift
FILE_TYPE="${1?Missing FILE_TYPE}" && shift
IGNORES=( "${@}" )

is_git_repo(){
	git rev-parse --git-dir &> /dev/null
}

file_test(){
    local search="${1?Missing search}" && shift
    local file="${1?Missing file}" && shift

    file_name=$(basename -- "${file}")
    file_extension="${file##*.}"
    file_name="${file_name%.*}"
    if [[ "${file_extension}" == "${file_name}" ]]; then
        file_extension="no-extension"
    fi

    file_mime="$(file -bi "${file}" )"
    file_brief="$(file -b "${file}" )"

    file_type=".${file_extension}: ${file_mime} ${file_brief}"

    [[ "${file_type,,}" =~ ${search,,} ]]
    return $?
}
export -f file_test

comm -23 \
	<(
		(
			if is_git_repo ; then
				# Is a git repo
				git ls-files -z -- "${SEARCH_DIR}" \
				| xargs \
					--null \
					--max-args 1 \
						bash -c 'if file_test "${1}" "${2}"; then echo "$2"; fi' \
							bash "${FILE_TYPE}"
			else
				# Not a git repo: fallback to find version
				find "${SEARCH_DIR}" \
					-type f \
					-exec \
						bash -c 'file_test "${1}" "${2}"' \
							bash "${FILE_TYPE}" {} \; \
					-print
			fi
		) \
		| sort \
	) \
	<( \
		printf '%s\n' "${IGNORES[@]}" \
		| sort \
	)
