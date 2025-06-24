#!/usr/bin/env bash
set -eou pipefail

readarray -t containers < <(docker ps -a -q || true)

if [[ "${#containers[@]}" -eq 0 ]]; then
    # no containers running
    exit 0
fi

docker stop "${containers[@]}"