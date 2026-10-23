# shellcheck shell=bash
#
# The body of `loom-mtls-placeholder`, which writes a throwaway client
# certificate so nginx starts straight away rather than waiting out a cluster
# bring-up with the captive portal behind it. nixos/mtls.nix reads this file
# into the writeShellApplication of the same name, behind a prologue of
# `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly STATE_DIR="${LOOM_STATE_DIR:?nixos/mtls.nix must set this}"
readonly CLIENT_CERT="${LOOM_CLIENT_CERT:?nixos/mtls.nix must set this}"
readonly CLIENT_KEY="${LOOM_CLIENT_KEY:?nixos/mtls.nix must set this}"
readonly SERVER_ANCHOR="${LOOM_SERVER_ANCHOR:?nixos/mtls.nix must set this}"
readonly NGINX_GROUP="${LOOM_NGINX_GROUP:?nixos/mtls.nix must set this}"

state="${STATE_DIR}"
mkdir -p "${state}"
# Restated here as well as in tmpfiles, because this unit is ordered
# before nginx and a directory nginx cannot traverse is the failure it
# exists to prevent.
chgrp "${NGINX_GROUP}" "${state}"
chmod 750 "${state}"

# Only when there is nothing there. A placeholder written over a real
# identity would take the box off its own cluster until the next renewal.
if [[ -s "${CLIENT_CERT}" ]] && [[ -s "${CLIENT_KEY}" ]]; then
  exit 0
fi

umask 077
openssl req -x509 -nodes -days 1 \
  -newkey rsa:2048 \
  -subj "/CN=loom-mtls-placeholder" \
  -keyout "${CLIENT_KEY}" \
  -out "${CLIENT_CERT}" 2>/dev/null

# Group-readable, for the reason `nginxGroup` is declared at all: the
# configuration test reads both halves as the service user.
chgrp "${NGINX_GROUP}" \
  "${CLIENT_KEY}" "${CLIENT_CERT}"
chmod 640 "${CLIENT_KEY}"
chmod 644 "${CLIENT_CERT}"

# `proxy_ssl_trusted_certificate` needs a file too, and the placeholder
# identity is as good a stand-in as any: nothing verifies against it while
# the upstream is being refused anyway.
if [[ ! -s "${SERVER_ANCHOR}" ]]; then
  cp "${CLIENT_CERT}" "${SERVER_ANCHOR}"
  chmod 644 "${SERVER_ANCHOR}"
fi
