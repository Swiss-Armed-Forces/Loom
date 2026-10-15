#!/bin/sh
# Pulls the models named in LLM_MODELS, a space-separated list, into this
# stage's ollama store.
#
# The pull's own output goes to a file rather than to the build log. `ollama
# pull` redraws a progress bar about ten times a second, which for a
# multi-gigabyte model fills GitLab's 4 MiB job log; past that limit the runner
# collects no further output and the server eventually fails the job as silent
# (`no_updates_running`). A heartbeat line a minute keeps the trace updating
# without the bar, and the captured output is printed when a pull fails.

set -eu

readonly PULL_LOG="/tmp/ollama-pull.log"
readonly SERVER_TIMEOUT_SECONDS=30
readonly HEARTBEAT_INTERVAL_SECONDS=60

# `ollama ps` answers only once the server is up, which keeps the readiness
# probe to the binary this stage already has rather than an installed curl.
start_server() {
  ollama serve >/dev/null 2>&1 &
  remaining="${SERVER_TIMEOUT_SECONDS}"
  while ! ollama ps >/dev/null 2>&1; do
    if [ "${remaining}" -le 0 ]; then
      echo "ERROR: ollama server failed to start" >&2
      exit 1
    fi
    remaining=$((remaining - 1))
    sleep 1
  done
}

heartbeat() {
  while true; do
    sleep "${HEARTBEAT_INTERVAL_SECONDS}"
    echo "  ... still pulling ${1}"
  done
}

pull_model() {
  echo "pulling ${1}"
  heartbeat "${1}" &
  heartbeat_pid="${!}"

  if ollama pull "${1}" >"${PULL_LOG}" 2>&1; then
    kill "${heartbeat_pid}" 2>/dev/null || true
    echo "pulled ${1}"
    return 0
  fi

  kill "${heartbeat_pid}" 2>/dev/null || true
  echo "ERROR: failed to pull ${1}" >&2
  tail -c 4096 "${PULL_LOG}" >&2
  exit 1
}

LLM_MODELS="${LLM_MODELS:?LLM_MODELS must name at least one model}"

start_server
for model in ${LLM_MODELS}; do
  pull_model "${model}"
done
pkill ollama || true
