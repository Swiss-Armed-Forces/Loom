#!/usr/bin/env bash
#
# Issues a client identity for Loom's mutual TLS, and exports the trust anchor
# that belongs beside it.
#
# Two different certificate authorities are in play and they are easy to mix up:
#
#   self-signed-mtls-cert  A CA keypair, made by the pre-install Job in
#                          charts/files/pre-install/generate-self-signed-mtls-certificate.sh.
#                          charts/templates/common/tls-option.yaml points
#                          Traefik's clientAuth at it, so this is what every
#                          client certificate has to be signed by. It verifies
#                          clients and signs nothing a client has to trust.
#   self-signed-cert       The certificate Traefik *serves*, made by the sibling
#                          Job. Nothing issues it, so a client that trusts the
#                          deployment trusts this certificate itself, as its own
#                          anchor.
#
# Which is why the two are exported separately rather than bundled. A PKCS#12
# file is a bag of certificates with no notion of trust: a CA dropped into one
# is stored and handed back, and no browser, keystore or trust store grants it
# anything on the strength of having been in the bag. The bundle this writes
# therefore carries the client identity and nothing else, and the anchor is a
# plain PEM with an install step of its own -- see the mutual TLS section in
# Documentation/installation.md.
#
# Runs from a checkout (the `generate-client-certificate` devenv script) and
# from the appliance (nixos/mtls.nix's loom-client-certificate.service), which
# is why vars.sh below is optional and --namespace exists.
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#
# Shared variables
#

# Read from vars.sh when there is a checkout around this script, and given with
# --namespace when there is not. vars.sh needs yq and charts/values.yaml, and
# the appliance runs this out of /nix/store with neither -- so a missing one is
# not an error here. An unset NAMESPACE after argument parsing is.
NAMESPACE=""

VARS_FILE="${SCRIPT_DIR}/../vars.sh"
if [[ -r "${VARS_FILE}" ]]; then
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${VARS_FILE}"
fi

#
# Defines
#

# The CA that signs what this issues. Absent means mutual TLS was never
# deployed -- see certificate.requireClientCert in charts/values.yaml.
MTLS_CA_SECRET_NAME="self-signed-mtls-cert"

# The serving certificate, which is also the trust anchor. Searched the way
# nixos/console.nix's fetch_ca searches: this secret first, then whatever the
# Ingress names, because which of the two answers depends on how the chart was
# deployed.
SERVING_CERT_SECRET_NAME="self-signed-cert"

DEFAULT_VALIDITY_DAYS="60"

# The window the pre-install Job replaces the mTLS CA in. A client certificate
# that outlives that moment verifies against nothing afterwards, and nothing
# says so at the time -- the handshake simply starts failing. Kept in step with
# the -checkend in generate-self-signed-mtls-certificate.sh.
CA_REPLACEMENT_WINDOW_DAYS="30"

# Matching the CA and the serving certificate, both of which the chart makes at
# 4096.
KEY_BITS="4096"

#
# Runtime vars
#

CLIENT_NAME=""
OUT_DIR="."
VALIDITY_DAYS="${DEFAULT_VALIDITY_DAYS}"
FORCE=false
LEGACY_PBE=false

WORK_DIR=""

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  --name NAME         name for the identity; becomes the certificate's"
    echo "                      CN and the basename of the files written"
    echo "                      default: client-<timestamp>"
    echo "  --out-dir DIR       directory to write into, created if absent"
    echo "                      default: ${OUT_DIR}"
    echo "  --days N            how long the client certificate is valid"
    echo "                      default: ${DEFAULT_VALIDITY_DAYS}"
    echo "  --namespace NS      namespace the Loom secrets live in"
    echo "                      default: read from vars.sh, else required"
    echo "  --force             overwrite files that are already there"
    echo "  --legacy-pbe        encrypt the PKCS#12 with 3DES instead of AES-256,"
    echo "                      for importers that reject OpenSSL 3's default"
    echo "  -h|--help           show this help"
}

#
# Functions
#

# One key out of one secret, as PEM on stdout.
#
# Read and decoded in two steps, the same way keep_existing_mtls_cert does in
# the pre-install script: this is called from `if`, where `set -e` is off, so a
# kubectl that failed would otherwise be indistinguishable from a secret with an
# empty value in it.
#
# KEY arrives with its dots escaped for jsonpath -- `ca\.crt`, not `ca.crt`.
read_secret_key() {
    local secret key encoded pem
    secret="${1}"
    key="${2}"

    if ! encoded="$(kubectl get secret "${secret}" \
        --namespace "${NAMESPACE}" \
        --output "jsonpath={.data.${key}}" 2>/dev/null)"; then
        return 1
    fi
    if [[ -z "${encoded}" ]]; then
        return 1
    fi

    if ! pem="$(base64 --decode <<< "${encoded}")"; then
        return 1
    fi
    case "${pem}" in
        *"BEGIN "*) ;;
        *) return 1 ;;
    esac

    printf '%s\n' "${pem}"
}

# The secret the chart's Ingresses name for TLS. On the cert-manager path
# (certificate.enabled) that is `<release>-certificate` rather than the secret
# the openssl Job writes, so the anchor is looked up instead of assumed.
ingress_tls_secret() {
    kubectl get ingress \
        --namespace "${NAMESPACE}" \
        --selector app.kubernetes.io/component=frontend \
        --output "jsonpath={.items[0].spec.tls[0].secretName}" 2>/dev/null || true
}

# The serving certificate, as PEM on stdout.
#
# `ca.crt` first and `tls.crt` second, for both candidates: a `kubectl create
# secret tls` secret -- which is how the openssl Job stores its certificate --
# has no `ca.crt` at all, while cert-manager's has both. Trusting the leaf is
# right rather than a fudge where it is all there is: nothing issued that
# certificate, it signs itself, and it is the only anchor on offer.
fetch_serving_anchor() {
    local -a secrets=("${SERVING_CERT_SECRET_NAME}")
    local from_ingress secret key pem

    from_ingress="$(ingress_tls_secret)"
    if [[ -n "${from_ingress}" && "${from_ingress}" != "${SERVING_CERT_SECRET_NAME}" ]]; then
        secrets+=("${from_ingress}")
    fi

    for secret in "${secrets[@]}"; do
        for key in 'ca\.crt' 'tls\.crt'; do
            # shellcheck disable=SC2310
            if pem="$(read_secret_key "${secret}" "${key}")"; then
                printf '%s\n' "${pem}"
                return 0
            fi
        done
    done
    return 1
}

# How many days are left on a certificate. Printed rather than compared, so the
# caller can say the number out loud.
days_left() {
    local cert not_after end_epoch now_epoch
    cert="${1}"

    if ! not_after="$(openssl x509 -noout -enddate -in "${cert}")"; then
        return 1
    fi
    not_after="${not_after#notAfter=}"

    if ! end_epoch="$(date --date "${not_after}" +%s)"; then
        return 1
    fi
    now_epoch="$(date +%s)"

    printf '%s\n' "$(( (end_epoch - now_epoch) / 86400 ))"
}

# Refuse to issue a certificate that outlives the CA behind it.
#
# Two things end it, and the later one is not the date on the CA. The
# pre-install Job replaces that CA once it is inside CA_REPLACEMENT_WINDOW_DAYS
# of expiring, and the replacement verifies none of the certificates the old one
# signed. So the usable life of anything issued here ends a month before the CA
# does, and a client certificate is only honest if it ends first.
assert_ca_outlives_client() {
    local ca_cert usable remaining
    ca_cert="${1}"
    usable=$(( (VALIDITY_DAYS + CA_REPLACEMENT_WINDOW_DAYS) * 86400 ))

    if openssl x509 -noout -checkend "${usable}" -in "${ca_cert}" > /dev/null; then
        return 0
    fi

    # shellcheck disable=SC2310
    remaining="$(days_left "${ca_cert}" || echo "?")"
    echo >&2 "[!] Error: the CA in '${MTLS_CA_SECRET_NAME}' has ${remaining} days left."
    echo >&2 "    A client certificate valid for ${VALIDITY_DAYS} days would outlive it."
    echo >&2 "    The pre-install Job replaces that CA within ${CA_REPLACEMENT_WINDOW_DAYS}"
    echo >&2 "    days of expiry, and the replacement verifies nothing the old one"
    echo >&2 "    signed -- so certificates issued now would stop working silently."
    echo >&2 "    Either pass a shorter --days, or redeploy the chart to roll the CA"
    echo >&2 "    and reissue every client afterwards."
    exit 1
}

fetch_ca() {
    echo "[*] Reading the mutual TLS CA from '${MTLS_CA_SECRET_NAME}'"

    # shellcheck disable=SC2310
    if ! read_secret_key "${MTLS_CA_SECRET_NAME}" 'ca\.crt' > "${CA_CERT_FILE}"; then
        echo >&2 "[!] Error: no CA certificate in secret '${MTLS_CA_SECRET_NAME}' in"
        echo >&2 "    namespace '${NAMESPACE}'. That secret is made by the chart's"
        echo >&2 "    pre-install hook; a deployment that has never had"
        echo >&2 "    certificate.requireClientCert set has no client certificates to"
        echo >&2 "    issue and nothing that would check one."
        exit 1
    fi

    # shellcheck disable=SC2310
    if ! read_secret_key "${MTLS_CA_SECRET_NAME}" 'ca\.key' > "${CA_KEY_FILE}"; then
        echo >&2 "[!] Error: no CA private key in secret '${MTLS_CA_SECRET_NAME}'."
        echo >&2 "    Issuing a client certificate needs it."
        exit 1
    fi

    assert_ca_outlives_client "${CA_CERT_FILE}"
}

generate_client_key_and_csr() {
    echo "[*] Generating a ${KEY_BITS}-bit key and a request for CN=${CLIENT_NAME}"

    openssl genrsa -out "${CLIENT_KEY_FILE}" "${KEY_BITS}" 2> /dev/null

    openssl req -new \
        -key "${CLIENT_KEY_FILE}" \
        -subj "/CN=${CLIENT_NAME}" \
        -out "${CLIENT_CSR_FILE}"
}

sign_client_cert() {
    echo "[*] Signing it for ${VALIDITY_DAYS} days"

    # Written out rather than left to openssl, which gives an end entity
    # certificate no extensions at all.
    #
    # This is the one certificate in the deployment that carries a critical
    # keyUsage, and the two sibling scripts say at length why they carry none:
    # theirs are used as their own trust anchors, and a verifier asked to anchor
    # on a certificate checks whether it was allowed to sign anything. Nothing
    # anchors on this one. It is an end entity presented to a server that
    # already holds the CA, so saying what it is for costs nothing.
    #
    # Go accepts a client certificate with no extendedKeyUsage at all, which is
    # why mutual TLS appeared to work without this.
    cat > "${EXT_FILE}" <<'EOF'
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid, issuer
EOF

    # -CAcreateserial writes <ca>.srl beside the CA file, which is why the CA
    # lives in the work directory the trap removes rather than in a bare mktemp.
    openssl x509 -req \
        -in "${CLIENT_CSR_FILE}" \
        -CA "${CA_CERT_FILE}" \
        -CAkey "${CA_KEY_FILE}" \
        -CAcreateserial \
        -extfile "${EXT_FILE}" \
        -days "${VALIDITY_DAYS}" \
        -sha256 \
        -out "${CLIENT_CERT_FILE}" 2> /dev/null
}

write_identity() {
    echo "[*] Writing the identity"

    install -m 600 "${CLIENT_CERT_FILE}" "${OUT_CERT}"
    install -m 600 "${CLIENT_KEY_FILE}" "${OUT_KEY}"

    # No --certfile. The bundle is the leaf and its key and nothing else: a CA
    # in here would be stored, handed back by `-cacerts`, and trusted by
    # nobody -- see the header.
    local -a args=(
        -export
        -inkey "${CLIENT_KEY_FILE}"
        -in "${CLIENT_CERT_FILE}"
        -name "${CLIENT_NAME}"
        -passout pass:
        -out "${OUT_P12}"
    )

    # OpenSSL 3 encrypts a PKCS#12 with AES-256-CBC and PBKDF2, which importers
    # older than that refuse outright rather than prompt about.
    if [[ "${LEGACY_PBE}" == true ]]; then
        args+=(
            -certpbe PBE-SHA1-3DES
            -keypbe PBE-SHA1-3DES
            -macalg sha1
        )
    fi

    openssl pkcs12 "${args[@]}"
    chmod 600 "${OUT_P12}"
}

write_anchor() {
    echo "[*] Exporting the trust anchor"

    # shellcheck disable=SC2310
    if ! fetch_serving_anchor > "${OUT_ANCHOR}"; then
        echo >&2 "[!] Error: could not find the serving certificate. Looked in secret"
        echo >&2 "    '${SERVING_CERT_SECRET_NAME}' and in whatever the frontend"
        echo >&2 "    Ingress names, for 'ca.crt' and then 'tls.crt'."
        exit 1
    fi
    chmod 644 "${OUT_ANCHOR}"
}

fingerprint() {
    local line
    line="$(openssl x509 -noout -fingerprint -sha256 -in "${1}")"
    printf '%s\n' "${line#*=}"
}

write_readme() {
    local anchor_name anchor_fingerprint client_fingerprint
    anchor_name="$(basename "${OUT_ANCHOR}")"
    anchor_fingerprint="$(fingerprint "${OUT_ANCHOR}")"
    client_fingerprint="$(fingerprint "${OUT_CERT}")"

    cat > "${OUT_README}" <<EOF
Loom client certificate for "${CLIENT_NAME}"

Loom is serving its hosts with mutual TLS: a client that presents no certificate
is refused during the handshake, before any page is served.

  ${CLIENT_NAME}.p12
      The identity, for browsers and anything else that imports a bundle. It
      holds the certificate and its private key, and NO PASSWORD -- treat the
      file as the credential it is.
  ${CLIENT_NAME}.crt and ${CLIENT_NAME}.key
      The same certificate and its key as PEM. This is the pair for curl, mc,
      nginx and anything else that takes --cert and --key.
  ${anchor_name}
      The certificate Loom serves. Nothing issued it, so it is its own trust
      anchor. Installing it is what stops the browser warning about *.loom.

Importing the .p12 does NOT make Loom's certificate trusted. A PKCS#12 file
carries certificates, not trust, so the anchor has to be installed separately
and deliberately. That is step 2, and it is the one people skip.

1. The identity

  Firefox
    Settings -> Privacy & Security -> Certificates -> View Certificates ->
    Your Certificates -> Import, and pick the .p12. Leave the password
    prompt empty.
  Chrome
    Settings -> Privacy and security -> Security -> Manage certificates ->
    Your certificates -> Import. On Linux this is the same NSS database
    Firefox uses.
  Windows
    certutil -user -importpfx My ${CLIENT_NAME}.p12
  macOS
    security import ${CLIENT_NAME}.p12 -k ~/Library/Keychains/login.keychain-db

2. The trust anchor

  Firefox
    The same dialog, Authorities tab, Import, and tick "Trust this CA to
    identify websites". The tick is the point: importing without it stores
    the certificate and trusts nothing.
  Chrome
    On Linux, the same NSS database, Authorities tab. On Windows and macOS
    Chrome uses the system store, so use the entries below.
  Windows
    certutil -user -addstore Root ${anchor_name}
    Confirm the prompt; it is asking whether to trust a new root.
  macOS
    security add-trusted-cert -r trustRoot \\
      -k ~/Library/Keychains/login.keychain-db ${anchor_name}
  Linux
    Copy it into /usr/local/share/ca-certificates/ and run
    update-ca-certificates, or pass it per call with curl --cacert.

3. Check it

  curl --cacert ${anchor_name} \\
    --cert ${CLIENT_NAME}.crt --key ${CLIENT_NAME}.key \\
    https://frontend.loom/

  The same call without --cert and --key must fail during the handshake. If
  it succeeds, mutual TLS is not actually on.

Fingerprints, SHA-256. Compare the anchor's against the deployment over some
channel that is not this file, or trusting it proves nothing:

  identity  ${client_fingerprint}
  anchor    ${anchor_fingerprint}

This certificate is valid for ${VALIDITY_DAYS} days. Nothing renews it; issue
another with \`generate-client-certificate\` when it expires.
EOF
}

report() {
    local client_fingerprint anchor_fingerprint
    client_fingerprint="$(fingerprint "${OUT_CERT}")"
    anchor_fingerprint="$(fingerprint "${OUT_ANCHOR}")"

    echo
    echo "[✔] Written to ${OUT_DIR}:"
    echo "  - $(basename "${OUT_P12}")  identity for browsers, no password"
    echo "  - $(basename "${OUT_CERT}")  identity as PEM, with"
    echo "  - $(basename "${OUT_KEY}")  its key, for curl and friends"
    echo "  - $(basename "${OUT_ANCHOR}")  trust anchor, installed separately"
    echo "  - $(basename "${OUT_README}")  what each file is and how to install it"
    echo
    echo "  identity fingerprint  ${client_fingerprint}"
    echo "  anchor fingerprint    ${anchor_fingerprint}"
    echo
    echo "  The .p12 establishes no trust in Loom's own certificate. Install"
    echo "  $(basename "${OUT_ANCHOR}") for that -- see $(basename "${OUT_README}")."
}

#
# Atexit
#
atexit() {
    if [[ -n "${WORK_DIR}" ]]; then
        rm --recursive --force "${WORK_DIR}"
    fi
}
trap atexit EXIT

#
# Argument parsing
#
while [[ $# -gt 0 ]]; do
    case "${1}" in
        --name)
            shift
            CLIENT_NAME="${1?Missing NAME}"
            shift
        ;;
        --out-dir)
            shift
            OUT_DIR="${1?Missing DIR}"
            shift
        ;;
        --days)
            shift
            VALIDITY_DAYS="${1?Missing N}"
            shift
        ;;
        --namespace)
            shift
            NAMESPACE="${1?Missing NS}"
            shift
        ;;
        --force)
            FORCE=true
            shift
        ;;
        --legacy-pbe)
            LEGACY_PBE=true
            shift
        ;;
        -h|--help)
            usage
            exit 0
        ;;
        *)
            echo >&2 "[!] Error: unknown argument: ${1}"
            usage >&2
            exit 1
        ;;
    esac
done

if [[ -z "${CLIENT_NAME}" ]]; then
    CLIENT_NAME="client-$(date +%s)"
fi

# Checked rather than trusted: this becomes a CN, four filenames and a PKCS#12
# friendlyName, and a value with a slash in it reaches openssl's -subj as a
# second field of the subject.
if [[ ! "${CLIENT_NAME}" =~ ^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$ ]]; then
    echo >&2 "[!] Error: invalid name: '${CLIENT_NAME}'"
    echo >&2 "    Letters, digits, dot, dash and underscore; must start and end"
    echo >&2 "    with a letter or a digit."
    exit 1
fi

if [[ ! "${VALIDITY_DAYS}" =~ ^[0-9]+$ ]] || (( VALIDITY_DAYS < 1 )); then
    echo >&2 "[!] Error: --days takes a positive number of days, got '${VALIDITY_DAYS}'"
    exit 1
fi

if [[ -z "${NAMESPACE}" ]]; then
    echo >&2 "[!] Error: no namespace. vars.sh was not found next to this script,"
    echo >&2 "    so --namespace is required."
    exit 1
fi

#
# Main
#

OUT_P12="${OUT_DIR}/${CLIENT_NAME}.p12"
OUT_CERT="${OUT_DIR}/${CLIENT_NAME}.crt"
OUT_KEY="${OUT_DIR}/${CLIENT_NAME}.key"
OUT_ANCHOR="${OUT_DIR}/loom-server-ca.pem"
OUT_README="${OUT_DIR}/README.txt"

if [[ "${FORCE}" != true ]]; then
    for existing in "${OUT_P12}" "${OUT_CERT}" "${OUT_KEY}" "${OUT_ANCHOR}" "${OUT_README}"; do
        if [[ -e "${existing}" ]]; then
            echo >&2 "[!] Error: ${existing} already exists. Pass --force to replace it,"
            echo >&2 "    or --name/--out-dir to write somewhere else."
            exit 1
        fi
    done
fi

# Mode set afterwards rather than with `mkdir -m`, which applies only to the
# deepest directory when --parents made several. The chmod is inside the branch,
# so a directory the operator already had keeps the permissions they gave it.
if [[ ! -d "${OUT_DIR}" ]]; then
    mkdir --parents "${OUT_DIR}"
    chmod 700 "${OUT_DIR}"
fi

# One directory rather than a handful of mktemp files, so the trap also takes
# the serial file -CAcreateserial drops beside the CA.
WORK_DIR="$(mktemp --directory)"
CA_CERT_FILE="${WORK_DIR}/ca.crt"
CA_KEY_FILE="${WORK_DIR}/ca.key"
CLIENT_KEY_FILE="${WORK_DIR}/client.key"
CLIENT_CSR_FILE="${WORK_DIR}/client.csr"
CLIENT_CERT_FILE="${WORK_DIR}/client.crt"
EXT_FILE="${WORK_DIR}/client.ext"

fetch_ca
generate_client_key_and_csr
sign_client_cert
write_identity
write_anchor
write_readme
report
