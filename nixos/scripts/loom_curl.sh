# shellcheck shell=bash
#
# The body of `loom-curl`, a curl that already holds the box's own client
# identity and trusts the cluster's certificate, so a program on the
# appliance can reach a `--require-client-cert` Loom without a proxy port.
# nixos/mtls.nix reads this file into the writeShellApplication of the same
# name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly CONSOLE_DIR="${LOOM_CONSOLE_DIR:?nixos/mtls.nix must set this}"
readonly CONSOLE_CERT="${LOOM_CONSOLE_CERT:?nixos/mtls.nix must set this}"
readonly CONSOLE_KEY="${LOOM_CONSOLE_KEY:?nixos/mtls.nix must set this}"
readonly CONSOLE_ANCHOR="${LOOM_CONSOLE_ANCHOR:?nixos/mtls.nix must set this}"
readonly NAMESPACE="${LOOM_NAMESPACE:?nixos/mtls.nix must set this}"
readonly SERVING_CERT_SECRET="${LOOM_SERVING_CERT_SECRET:?nixos/mtls.nix must set this}"

cert="${CONSOLE_CERT}"
key="${CONSOLE_KEY}"
anchor="${CONSOLE_ANCHOR}"
namespace="${NAMESPACE}"
secret="${SERVING_CERT_SECRET}"

# Arguments are passed through untouched, deliberately.
#
# This used to rewrite a leading `http://` to `https://`, so that one
# documented spelling would work on an image serving plaintext and on one
# that does not. It is not needed -- `websecure` exists on every image, so
# `https://` is already the spelling that always works -- and it broke
# three things that look exactly like the URL it meant to fix: the
# loopback proxies (`http://127.0.0.1:18080/`, which appliance.md gives as
# the way to test them, and which speak plain http), `http://portal.loom/`
# (whose TLS listener exists only on the mutual TLS image), and the value
# of any flag that happens to be a URL, `--proxy` among them. A wrapper
# that edits arguments has to know which argument is the URL, and this one
# cannot.
flags=()

# The anchor. On a mutual TLS box the issuer already wrote one next to the
# console's identity; anywhere else it is read out of the cluster.
#
# Read every time rather than cached. The chart's pre-install Job replaces
# the serving certificate as it nears expiry, and a cached copy would
# outlive it and fail verification with an error that says nothing about
# why -- on a box whose whole purpose is to be diagnosed from this pane.
# One kubectl call on a command somebody typed is not worth that.
if [[ -r "${anchor}" ]]; then
  flags+=( --cacert "${anchor}" )
else
  work="$(mktemp --directory)"
  # shellcheck disable=SC2064
  trap "rm --recursive --force '${work}'" EXIT
  pem="${work}/server-ca.pem"

  # `ca.crt` first and `tls.crt` second, which is the order and the reason
  # cicd/generate_client_certificate.sh uses: a secret made by `kubectl
  # create secret tls` has no `ca.crt` at all, and a self-signed leaf is
  # its own anchor.
  #
  # --request-timeout so a cluster that is down costs five seconds rather
  # than kubectl's default wait, the same bound ready.nix and the identity
  # unit use.
  for field in 'ca\.crt' 'tls\.crt'; do
    encoded="$(kubectl --request-timeout=5s --namespace "${namespace}" \
      get secret "${secret}" --output "jsonpath={.data.${field}}" 2>/dev/null || true)"
    [[ -n "${encoded}" ]] || continue

    printf '%s' "${encoded}" | base64 --decode > "${pem}" 2>/dev/null || true

    # Checked for a PEM header rather than merely for being non-empty,
    # the way generate_client_certificate.sh and console.nix both check
    # their own copies of this: anything else handed to `--cacert`
    # produces the opaque verification failure this whole branch exists
    # to avoid.
    if grep --quiet -- "-----BEGIN CERTIFICATE-----" "${pem}" 2>/dev/null; then
      flags+=( --cacert "${pem}" )
      break
    fi
  done

  if [[ ! -s "${pem}" ]]; then
    echo "loom-curl: could not read ${secret} from the cluster;" \
      "TLS verification will fail until Loom is up." >&2
  fi
fi

# The identity, where this box has one. Absent on every image but a
# --require-client-cert one, where nothing asks for it.
#
# The directory is the tell, not the files: tmpfiles creates it at boot
# and only on an image that requires certificates, while the files appear
# whenever loom-mtls-identity first reaches the cluster -- hours into a
# first bring-up. Between the two, every request is refused during the
# handshake, and curl's own message for that says nothing about why.
if [[ -r "${cert}" ]] && [[ -r "${key}" ]]; then
  flags+=( --cert "${cert}" --key "${key}" )
elif [[ -d "${CONSOLE_DIR}" ]]; then
  echo "loom-curl: this box requires a client certificate and has not been" \
    "issued one yet; see 'systemctl status loom-mtls-identity'." >&2
fi

# Ours first: curl takes the last occurrence of either flag, so an
# operator passing their own --cert or --cacert still overrides these.
#
# Not `exec`: the anchor above may be in a temporary directory this script
# still has to remove, and an exec'd process never runs the EXIT trap.
# `set -e` propagates curl's exit status.
curl "${flags[@]}" "$@"
