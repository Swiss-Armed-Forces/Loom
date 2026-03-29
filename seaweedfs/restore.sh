#!/bin/sh
set -eu

# Restore script: starts SQLite filer on-demand, restores to Redis, then stops
# Usage: ./restore.sh [filerDir]
#
# This script restores filer metadata from the SQLite backup to Redis.
# It starts a temporary SQLite filer, runs the restore, then cleans up.
#
# Arguments:
#   filerDir - Directory to restore (default: /)
#
# Required environment variables:
#   SQLITE_FILER_PORT      - Port for the temporary SQLite filer HTTP
#   SQLITE_FILER_GRPC_PORT - Port for the temporary SQLite filer gRPC
#   MASTER_HOST            - SeaweedFS master hostname
#   MASTER_PORT            - SeaweedFS master port
#
# Optional environment variables:
#   REDIS_CONFIG  - Path to Redis filer config (default: /etc/seaweedfs/redis_filer.toml)

FILER_DIR="${1:-/}"
SQLITE_FILER_DB="${SQLITE_FILER_DB:-/data/filer_backup.db}"
REDIS_CONFIG="${REDIS_CONFIG:-/etc/seaweedfs/redis_filer.toml}"

# Validate required environment variables
SQLITE_FILER_PORT="${SQLITE_FILER_PORT?Missing SQLITE_FILER_PORT}"
SQLITE_FILER_GRPC_PORT="${SQLITE_FILER_GRPC_PORT?Missing SQLITE_FILER_GRPC_PORT}"
MASTER_HOST="${MASTER_HOST?Missing MASTER_HOST}"
MASTER_PORT="${MASTER_PORT?Missing MASTER_PORT}"

MASTER="${MASTER_HOST}:${MASTER_PORT}"
FILER_PID=""

# Cleanup filer on exit (Ctrl+C or script end)
cleanup() {
  echo ""
  echo "Stopping SQLite filer..."
  if [ -n "${FILER_PID}" ]; then
    kill "${FILER_PID}" 2>/dev/null || true
  fi
  echo "Done."
}
trap cleanup EXIT

# Wait for master to be available
echo "Waiting for SeaweedFS master..."
until nc -z "${MASTER_HOST}" "${MASTER_PORT}" 2>/dev/null; do
  sleep 1
done
echo "Master is ready."

echo "Running WAL checkpoint on ${SQLITE_FILER_DB}..."
sqlite3 "${SQLITE_FILER_DB}" "PRAGMA wal_checkpoint(FULL);"
echo "Checkpoint complete."

echo "Starting SQLite filer..."
weed filer \
  -master="${MASTER}" \
  -ip=127.0.0.1 \
  -ip.bind=127.0.0.1 \
  -port="${SQLITE_FILER_PORT}" \
  -port.grpc="${SQLITE_FILER_GRPC_PORT}" &
FILER_PID=$!

# Wait for filer to be ready (check both HTTP and gRPC ports)
echo "Waiting for SQLite filer to be ready..."
until nc -z 127.0.0.1 "${SQLITE_FILER_PORT}" 2>/dev/null && \
      nc -z 127.0.0.1 "${SQLITE_FILER_GRPC_PORT}" 2>/dev/null; do
  sleep 1
done
echo "SQLite filer is ready."

echo ""
echo "Starting restore from SQLite to Redis..."
echo "  Source: SQLite filer at 127.0.0.1:${SQLITE_FILER_PORT}"
echo "  Target: Redis (config: ${REDIS_CONFIG})"
echo "  Directory: ${FILER_DIR}"
echo ""
echo "NOTE: Press Ctrl+C when you see 'listening for updates' to stop."
echo ""

# Run restore - blocks until user hits Ctrl+C
weed filer.meta.backup \
  -filer="127.0.0.1:${SQLITE_FILER_PORT}" \
  -filerDir="${FILER_DIR}" \
  -config="${REDIS_CONFIG}" \
  -restart
