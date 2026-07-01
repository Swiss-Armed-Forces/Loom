#!/usr/bin/env sh
# Helper functions for GitLab CI job scripts.
# This file is sourced by CI job scripts running under sh — all syntax
# must be POSIX sh compatible (no bash-specific constructs).
#
# see:
#  - https://docs.gitlab.com/ci/jobs/job_logs/#custom-collapsible-sections

# Start a gitlab job log section
# $1 : name of the section
# $2 (optional) : description of the section
# If the description is not provided, the name will be used as the description
section_start() {
  section_title="${1}" && shift
  section_description="${1:-${section_title}}"
  date_now=$(date +%s)
  printf "section_start:%s:%s[collapsed=true]\r\033[0K%s\n" "${date_now}" "${section_title}" "${section_description}"
}

# End a gitlab job log section
# $1 : name of the section
section_end() {
  section_title="${1}" && shift
  date_now=$(date +%s)
  printf "section_end:%s:%s\r\033[0K\n" "${date_now}" "${section_title}"
}

# Retry a command up to N times with a delay between attempts.
# Usage: with_retry [--max N] [--delay SECONDS] -- COMMAND [ARGS...]
with_retry() {
  max=3
  delay=30
  while [ "${1#--}" != "$1" ]; do
    case "$1" in
      --max)   max="$2";   shift 2 ;;
      --delay) delay="$2"; shift 2 ;;
      --)      shift; break ;;
      *)       break ;;
    esac
  done
  attempt=1
  until "$@"; do
    if [ "${attempt}" -ge "${max}" ]; then
      echo "[with_retry] Command failed after ${max} attempts: $*" >&2
      return 1
    fi
    echo "[with_retry] Attempt ${attempt}/${max} failed, retrying in ${delay}s..." >&2
    sleep "${delay}"
    attempt=$((attempt + 1))
  done
}
