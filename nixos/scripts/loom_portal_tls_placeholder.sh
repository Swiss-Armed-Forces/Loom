# shellcheck shell=bash
#
# The body of `loom-portal-tls-placeholder`, which writes a throwaway
# certificate for the portal's TLS listener so nginx binds at boot instead of
# waiting for the cluster. nixos/portal.nix reads this file into the
# writeShellApplication of the same name, behind a prologue of `LOOM_*`
# assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly TLS_DIR="${LOOM_TLS_DIR:?nixos/portal.nix must set this}"
readonly TLS_CERT="${LOOM_TLS_CERT:?nixos/portal.nix must set this}"
readonly TLS_KEY="${LOOM_TLS_KEY:?nixos/portal.nix must set this}"
readonly TLS_PLACEHOLDER_MARKER="${LOOM_TLS_PLACEHOLDER_MARKER:?nixos/portal.nix must set this}"
readonly NGINX_GROUP="${LOOM_NGINX_GROUP:?nixos/portal.nix must set this}"
readonly PORTAL_USER="${LOOM_PORTAL_USER:?nixos/portal.nix must set this}"
readonly PORTAL_HOST="${LOOM_PORTAL_HOST:?nixos/portal.nix must set this}"

mkdir --parents "${TLS_DIR}"
chgrp "${NGINX_GROUP}" "${TLS_DIR}"
chmod 750 "${TLS_DIR}"

# Only when there is nothing usable there. Writing a placeholder over the
# real certificate would put the warning back for a day, on the one page
# that exists to take it away -- but `-s` alone also kept an *expired*
# pair: `tlsDir` is on the encrypted root and survives reboots, this
# certificate is `-days 1`, and `loom-portal-certificate` loops until the
# cluster answers without ever consulting expiry. On a box whose cluster
# never comes up, every boot after the first short-circuited past replacing
# it and nginx served an expired certificate indefinitely. `-checkend 0` is
# the one-line version of what `loom-mtls-identity` does daily.
if [[ -s "${TLS_CERT}" ]] && [[ -s "${TLS_KEY}" ]] \
  && openssl x509 -noout -checkend 0 -in "${TLS_CERT}" \
    >/dev/null 2>&1; then
  exit 0
fi

umask 077
openssl req -x509 -nodes -days 1 \
  -newkey rsa:2048 \
  -subj "/CN=${PORTAL_HOST}" \
  -keyout "${TLS_KEY}" \
  -out "${TLS_CERT}" 2>/dev/null

chgrp "${NGINX_GROUP}" "${TLS_KEY}" "${TLS_CERT}"
chmod 640 "${TLS_KEY}"
chmod 644 "${TLS_CERT}"

# The marker the page reads. While it exists, 443 is answered by a
# certificate nothing can verify -- `-days 1`, rsa:2048, self-signed
# `CN=portal.loom` -- and the page must not offer a PKCS#12 over it: the
# bundle carries an unencrypted private key, and "the connection was
# encrypted" is not the property that matters when the key exchange is
# authenticated by nothing. `loom-portal-certificate` removes it once the
# cluster's own pair is in place, which on a first boot is hours away.
: > "${TLS_PLACEHOLDER_MARKER}"
chgrp "${PORTAL_USER}" "${TLS_PLACEHOLDER_MARKER}"
chmod 644 "${TLS_PLACEHOLDER_MARKER}"
