#!/usr/bin/env bash
set -euo pipefail

# Check for dos2unix issues
files_containing_dos2unix_issues="$(git ls-files -z -- . ':!:integrationtest/assets/' ':!Documentation/c4-2-container.svg' | xargs -0 -n1 dos2unix --info=c --)"
if [[ -n "${files_containing_dos2unix_issues}" ]]; then
	>&2 echo "Files with dos2unix issues found:"
	echo "${files_containing_dos2unix_issues}"
	exit 1
fi
