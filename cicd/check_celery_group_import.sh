#!/usr/bin/env bash
# Checks that python code file does not import group directly from celery.canvas
# This check is required for our patch of Celery issue #8182
# Can be removed together with patch as soon as issue is fixed upstream

exit_code=0

for file in "$@"; do
    violations=$(
        grep \
            --line-number \
            'from celery.canvas import' "${file}" \
        | grep \
            'group\|*' \
        || true
    )
    if [[ -n "${violations}" ]]; then
        >&2 echo "ERROR: Found direct group import from celery.canvas in ${file}. Import instead directly from celery !"
        >&2 echo "${violations}"
        exit_code=1
    fi
done

exit "${exit_code}"
