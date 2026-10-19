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

# Enter the devenv shell, dropping a nix fetcher cache that has outlived the
# store paths it names.
#
# nix records in ~/.cache/nix/fetcher-cache-v*.sqlite the NAR hash of every
# file it copies out of a fetched source tree, and on the next evaluation it
# derives that file's store path from the cached hash instead of looking in the
# store.  Garbage collection does not prune those rows, so once a collection
# removes such a copy - the runner's store is shared between jobs, and the
# appliance tests collect to stay inside their disk budget - every later
# evaluation that needs the same file dies with
#
#   error: path '/nix/store/...' is not valid
#
# and stays dead: a copied source has no deriver and no substituter, so nothing
# can rebuild or fetch it.  Only re-copying it from the tree helps, which is
# what nix does again once the cache no longer claims to have done it.
#
# The retry is deliberately narrow: any other evaluation failure - a broken
# devenv.nix, a missing package - is reported as it is, without a second run.
devenv_shell_ready() {
  devenv_shell_log=$(mktemp)

  if devenv shell -- echo "[*] devenv shell ready" >"${devenv_shell_log}" 2>&1; then
    cat "${devenv_shell_log}"
    rm -f "${devenv_shell_log}"
    return 0
  fi

  cat "${devenv_shell_log}" >&2
  if ! grep -q "is not valid" "${devenv_shell_log}"; then
    rm -f "${devenv_shell_log}"
    return 1
  fi
  rm -f "${devenv_shell_log}"

  echo "[*] The nix fetcher cache names store paths that are gone - dropping it and evaluating again" >&2
  rm -f "${XDG_CACHE_HOME:-${HOME}/.cache}"/nix/fetcher-cache-v*.sqlite*

  devenv shell -- echo "[*] devenv shell ready (after dropping the fetcher cache)"
}
