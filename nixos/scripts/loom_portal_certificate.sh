# shellcheck shell=bash
#
# The body of `loom-portal-certificate`, which gives the portal's own TLS
# listener a real certificate once the cluster has one, replacing the
# placeholder written at boot. nixos/portal.nix reads this file into the
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

readonly TLS_CERT="${LOOM_TLS_CERT:?nixos/portal.nix must set this}"
readonly TLS_KEY="${LOOM_TLS_KEY:?nixos/portal.nix must set this}"
readonly TLS_PLACEHOLDER_MARKER="${LOOM_TLS_PLACEHOLDER_MARKER:?nixos/portal.nix must set this}"
readonly ANCHOR_FILE="${LOOM_ANCHOR_FILE:?nixos/portal.nix must set this}"
readonly FINGERPRINT_FILE="${LOOM_FINGERPRINT_FILE:?nixos/portal.nix must set this}"
readonly NGINX_GROUP="${LOOM_NGINX_GROUP:?nixos/portal.nix must set this}"
readonly NAMESPACE="${LOOM_NAMESPACE:?nixos/portal.nix must set this}"
readonly SERVING_SECRET="${LOOM_SERVING_SECRET:?nixos/portal.nix must set this}"
# "1" when the portal serves TLS of its own, "0" otherwise.
readonly ENABLE_TLS="${LOOM_ENABLE_TLS:?nixos/portal.nix must set this}"

namespace="${NAMESPACE}"
secret="${SERVING_SECRET}"
want_tls="${ENABLE_TLS}"

# Said once per change rather than once per attempt, the way mtls.nix's
# issuer does it: a box waiting an hour for a bring-up should not fill the
# journal with one line every ten seconds.
said=""
note() {
  if [[ "$1" != "${said}" ]]; then
    said="$1"
    echo "$1"
  fi
}

read_secret_key() {
  local value
  value="$(kubectl --request-timeout=5s --namespace "${namespace}" \
    get secret "$1" --output "jsonpath={.data.$2}" 2>/dev/null)" || return 1
  [[ -n "${value}" ]] || return 1
  base64 --decode <<< "${value}"
}

# Whatever the frontend's Ingress names, for a deployment that brought its
# own certificate. Same fallback as cicd/generate_client_certificate.sh's
# fetch_serving_anchor.
ingress_secret() {
  kubectl --request-timeout=5s --namespace "${namespace}" \
    get ingress --selector app.kubernetes.io/component=frontend \
    --output "jsonpath={.items[0].spec.tls[0].secretName}" 2>/dev/null || true
}

# Waiting forever is safe here, unlike in the issuer next door: nothing is
# ordered behind this unit, the page works without it and says so, and a
# visitor is not standing in front of it.
until kubectl --request-timeout=5s --namespace "${namespace}" \
  get secret "${secret}" >/dev/null 2>&1; do
  alternative="$(ingress_secret)"
  if [[ -n "${alternative}" ]] && [[ "${alternative}" != "${secret}" ]]; then
    note "Using '${alternative}' from the frontend Ingress instead of '${secret}'."
    secret="${alternative}"
    continue
  fi
  note "Waiting for '${secret}'; Loom has not got that far yet."
  sleep 10
done

work="$(mktemp --directory)"
# shellcheck disable=SC2064
trap "rm --recursive --force '${work}'" EXIT

# The anchor and the serving pair are not necessarily the same certificate.
#
# On the default path the chart makes `self-signed-cert` with `kubectl
# create secret tls`, so it carries no `ca.crt` and the anchor is the leaf
# itself -- nothing issued it, and a client that trusts this deployment
# trusts that certificate as its own root. On the cert-manager path
# (`certificate.enabled`) the secret carries both, and the anchor is the
# issuer. Taking `tls.crt` in that case would hand the visitor a leaf to
# trust on the one deployment where the leaf rotates underneath them.
found=""
for key in 'ca\.crt' 'tls\.crt'; do
  if read_secret_key "${secret}" "${key}" > "${work}/anchor.pem" \
    && grep --quiet "BEGIN CERTIFICATE" "${work}/anchor.pem"; then
    found="${key}"
    break
  fi
done
if [[ -z "${found}" ]]; then
  echo "Secret '${secret}' carries no certificate this page could publish." >&2
  exit 1
fi

openssl x509 -noout -fingerprint -sha256 -in "${work}/anchor.pem" \
  | cut --delimiter== --fields=2 > "${work}/anchor.sha256"

changed=0

# Compared before it is written, and that is not tidiness. The reload below
# is `reload-or-restart`, which on a box where nginx is down becomes a
# restart -- and a restart drops the in-flight connections on
# loom-mtls-ollama, which carry the assistant pane's token stream at a
# 3600-second read timeout. Doing that every hour for no reason would be a
# chat pane that goes blank on the hour.
publish() {
  if cmp --silent "$1" "$2" 2>/dev/null; then
    return 0
  fi
  install --mode="$3" "$1" "$2"
  changed=1
}

publish "${work}/anchor.pem" "${ANCHOR_FILE}" 644
publish "${work}/anchor.sha256" "${FINGERPRINT_FILE}" 644

if [[ "${want_tls}" = 1 ]]; then
  if ! read_secret_key "${secret}" 'tls\.crt' > "${work}/cert.pem" \
    || ! read_secret_key "${secret}" 'tls\.key' > "${work}/key.pem"; then
    echo "Secret '${secret}' carries no serving pair; leaving the TLS listener as it is." >&2
    exit 0
  fi
  publish "${work}/cert.pem" "${TLS_CERT}" 644
  if ! cmp --silent "${work}/key.pem" "${TLS_KEY}" 2>/dev/null; then
    install --mode=640 --group="${NGINX_GROUP}" \
      "${work}/key.pem" "${TLS_KEY}"
    changed=1
  fi
  # The listener is now the cluster's own certificate -- the one the page
  # has been telling the visitor to trust -- so the page may offer a
  # private key over it. Until this point `_is_secure` was true of a
  # connection carrying the one-day placeholder, which is authenticated by
  # nothing and is in force for the hours a first boot takes.
  rm --force "${TLS_PLACEHOLDER_MARKER}"
fi

if [[ "${changed}" = 1 ]]; then
  echo "Published the serving certificate from '${secret}' (anchor key: ${found})."
  systemctl reload-or-restart nginx.service
fi
