#!/bin/sh
# Reap scratch files left behind by killed Tika parses.
#
# A parse that is killed - task timeout, OOM - never runs its cleanup handlers,
# so its scratch files stay behind in the RAM-backed /tmp. They accumulate until
# /tmp is full, and from then on every parse fails, not just the oversized one
# that started it. Clearing /tmp on container start only heals this at a restart,
# so sweep the leftovers of a long-running container periodically.
set -eu

tmp_dir=/tmp
max_age_seconds=600
interval_seconds=60

usage() {
    cat <<USAGE
Usage: ${0} [--tmp-dir DIR] [--max-age-seconds N] [--interval-seconds N]

Deletes Tika and ImageMagick scratch entries under DIR whose age exceeds
MAX-AGE-SECONDS, repeating every INTERVAL-SECONDS until terminated.

Defaults: --tmp-dir ${tmp_dir} --max-age-seconds ${max_age_seconds} --interval-seconds ${interval_seconds}
USAGE
}

while [ ${#} -gt 0 ]; do
    case "${1}" in
    --tmp-dir)
        tmp_dir="${2}"
        shift 2
        ;;
    --max-age-seconds)
        max_age_seconds="${2}"
        shift 2
        ;;
    --interval-seconds)
        interval_seconds="${2}"
        shift 2
        ;;
    -h | --help)
        usage
        exit 0
        ;;
    *)
        echo "${0}: unknown argument: ${1}" >&2
        usage >&2
        exit 1
        ;;
    esac
done

# find works in whole minutes, so round the threshold up: never reap below it,
# at the cost of keeping orphans at most a minute longer.
max_age_minutes=$(((max_age_seconds + 59) / 60))
if [ "${max_age_minutes}" -lt 1 ]; then
    max_age_minutes=1
fi

# Terminate during the sleep instead of after it: sleep runs in the background
# and wait is interruptible, so the container stops promptly.
trap 'exit 0' INT TERM

echo "tmp-reaper: sweeping ${tmp_dir} every ${interval_seconds}s for entries older than ${max_age_minutes}m"

while true; do
    # apache-tika-server-forked-tmp-* is the running server's own scratch: it is
    # written once at startup and never touched again, so it ages past any
    # threshold while still in use and must stay excluded.
    reaped=$(
        find "${tmp_dir}" -mindepth 1 -maxdepth 1 \
            \( -name 'apache-tika-*' -o -name 'tika-pdfbox-rendering-*' -o -name 'magick-*' \) \
            ! -name 'apache-tika-server-forked-tmp-*' \
            -mmin "+${max_age_minutes}" \
            -print -exec rm -rf {} + 2>/dev/null | wc -l
    )
    if [ "${reaped}" -gt 0 ]; then
        echo "tmp-reaper: removed ${reaped} orphaned scratch entries older than ${max_age_minutes}m"
    fi
    sleep "${interval_seconds}" &
    wait ${!}
done
