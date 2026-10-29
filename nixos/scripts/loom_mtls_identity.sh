# shellcheck shell=bash
#
# The body of `loom-mtls-identity`, which issues the box its own two client
# certificates once the cluster's CA exists -- nginx's, and the console's for
# `loom-curl` -- and reissues them before they expire. nixos/mtls.nix reads
# this file into the writeShellApplication of the same name, behind a
# prologue of `LOOM_*` assignments.
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
readonly NGINX_GROUP="${LOOM_NGINX_GROUP:?nixos/mtls.nix must set this}"
readonly CONSOLE_DIR="${LOOM_CONSOLE_DIR:?nixos/mtls.nix must set this}"
readonly CONSOLE_GROUP="${LOOM_CONSOLE_GROUP:?nixos/mtls.nix must set this}"
readonly NAMESPACE="${LOOM_NAMESPACE:?nixos/mtls.nix must set this}"
readonly CA_SECRET="${LOOM_CA_SECRET:?nixos/mtls.nix must set this}"
readonly IDENTITY_NAME="${LOOM_IDENTITY_NAME:?nixos/mtls.nix must set this}"
readonly CONSOLE_IDENTITY_NAME="${LOOM_CONSOLE_IDENTITY_NAME:?nixos/mtls.nix must set this}"
readonly VALIDITY_DAYS="${LOOM_VALIDITY_DAYS:?nixos/mtls.nix must set this}"
readonly RENEW_BEFORE="${LOOM_RENEW_BEFORE:?nixos/mtls.nix must set this}"

state="${STATE_DIR}"
console="${CONSOLE_DIR}"
namespace="${NAMESPACE}"
secret="${CA_SECRET}"
name="${IDENTITY_NAME}"
console_name="${CONSOLE_IDENTITY_NAME}"
days="${VALIDITY_DAYS}"
renew_before="${RENEW_BEFORE}"

# The placeholder is a certificate too, so "is there a file" is not the
# question -- `-checkend` against a one-day placeholder is false on the
# day it was written, which is what gets it replaced.
fresh() {
  openssl x509 -noout -checkend "$((renew_before * 86400))" \
    -in "$1" >/dev/null 2>&1
}

# Both, and that is the whole reason this is a function. Guarding on the
# proxy's certificate alone means a console identity that is missing or
# expired is skipped for as long as nginx's is fresh -- which is every day
# but one in sixty, so the console would be issued once and then silently
# left to expire.
if fresh "${state}/client.crt" && fresh "${console}/console.crt"; then
  echo "Both certificates have more than ${renew_before} days left; nothing to do."
  exit 0
fi

# Said once per change rather than once per attempt, the way console.nix's
# waits do: a box that waits an hour for a bring-up should not fill the
# journal with one line every ten seconds.
said=""
note() {
  if [[ "$1" != "${said}" ]]; then
    said="$1"
    echo "$1"
  fi
}

until kubectl --request-timeout=5s --namespace "${namespace}" \
  get secret "${secret}" >/dev/null 2>&1; do
  note "Waiting for '${secret}'; Loom has not got that far yet."
  sleep 10
done

work="$(mktemp --directory)"
# shellcheck disable=SC2064
trap "rm --recursive --force '${work}'" EXIT

# A directory each. The issuer writes `loom-server-ca.pem` beside every
# identity it makes, so two runs sharing one output directory would have
# the second meet a file the first left there.
mkdir -p "${work}/proxy" "${work}/console"

# The proxy's identity first, and all the way into place before the
# console's is even asked for. Under `set -e` a failure on the second
# issuance aborts the script, so doing them both up front and installing
# afterwards would have a console that cannot be issued discard a proxy
# certificate that was generated perfectly well -- taking the assistant
# pane and USB ingest down to renew something neither uses.
loom-client-certificate \
  --name "${name}" \
  --days "${days}" \
  --namespace "${namespace}" \
  --out-dir "${work}/proxy"

# Moved into place together, and only once all three exist: nginx reloads
# on its own schedule as well as on the one below, and a reload that lands
# between a new certificate and its key gets a pair that does not match.
#
# The key is group-readable and the group is nginx's, because nginx runs
# as its own user and reads this while parsing -- see `nginxGroup`.
install -m 644 "${work}/proxy/${name}.crt" "${state}/client.crt"
install -m 640 -g "${NGINX_GROUP}" \
  "${work}/proxy/${name}.key" "${state}/client.key"
install -m 644 "${work}/proxy/loom-server-ca.pem" "${state}/loom-server-ca.pem"

echo "Issued a client identity for ${name}."

# reload-or-restart rather than reload: on a box where nginx failed to
# start at all, a reload is a no-op and the proxy stays down.
systemctl reload-or-restart nginx.service

# And now the console's, group-readable by the operator instead.
# `loom-curl` is what reads it, as whoever is at the console or in the
# assistant pane.
loom-client-certificate \
  --name "${console_name}" \
  --days "${days}" \
  --namespace "${namespace}" \
  --out-dir "${work}/console"

# The directory is restated here as well as in tmpfiles, the way the
# placeholder unit restates its own: `install` creates a file and not the
# path above it, so a unit that ran before systemd-tmpfiles would fail on
# the first line rather than issue anything.
install -d -m 750 -g "${CONSOLE_GROUP}" "${console}"

install -m 644 "${work}/console/${console_name}.crt" "${console}/console.crt"
install -m 640 -g "${CONSOLE_GROUP}" \
  "${work}/console/${console_name}.key" "${console}/console.key"
install -m 644 "${work}/console/loom-server-ca.pem" "${console}/loom-server-ca.pem"

echo "Issued a client identity for ${console_name}."
