#!/usr/bin/env bash
#
# Puts a certificate covering every name this deployment serves in the
# `self-signed-cert` secret, unless one is already there.
#
# Runs as a pre-install/pre-upgrade hook Job, mounted from the ConfigMap in
# charts/templates/pre-install/scripts-configMap.yaml. Everything the chart has
# to say to it arrives as arguments, so this file stays a plain script that
# linting and review can read.
set -euo pipefail

#
# Vars
#
# Passed by the Job from values.yaml, and checked below rather than defaulted:
# a missing one means the template and this script have drifted apart, and a
# certificate made from an empty domain is worse than a hook that fails loudly.
NAMESPACE=""
LOOM_DOMAIN=""
# Every name the certificate has to carry, one --hostname each, from
# .Values.hostnames -- see the comment there for why a wildcard cannot do this
# job.
LOOM_HOSTNAMES=()

CERT_SECRET_NAME="self-signed-cert"
# The marker that says this Job made the certificate. Only a certificate
# carrying it is ever replaced below.
CERT_ORG="Wildcard Self-Signed"

CRT_FILE="$(mktemp)"
KEY_FILE="$(mktemp)"

#
# Usage
#
usage(){
    echo "usage: ${0} --namespace NAMESPACE --domain DOMAIN --hostname NAME ..."
    echo "  --namespace NAMESPACE   namespace the certificate secret is created in"
    echo "  --domain DOMAIN         domain every host sits under"
    echo "  --hostname NAME         host to name in the certificate; repeat per host"
    echo "  -h|--help               show this help"
}

#
# Functions
#

# The subjectAltName argument: every declared host by name, plus the wildcard
# and the bare domain. The wildcard is kept for the browsers that still honour
# it in a warning dialog; nothing programmatic accepts it for a single-label
# parent, which is what the per-host entries are for.
san_argument() {
    local san name
    san="DNS:*.${LOOM_DOMAIN},DNS:${LOOM_DOMAIN}"
    for name in "${LOOM_HOSTNAMES[@]}"; do
        san="${san},DNS:${name}.${LOOM_DOMAIN}"
    done
    printf '%s' "${san}"
}

# Whether the certificate already in the cluster is to be kept.
#
# A `true` here also covers "somebody else's certificate": an operator-supplied
# one (up.sh --certificate writes this same secret) has no reason to carry our
# Organization, and replacing it would throw away a real certificate for a real
# domain. So the marker is checked first, and anything without it is left alone.
#
# Only that case is a reason to keep a certificate this Job cannot inspect.
# Failing to read or parse one whose secret is right there is an error, and it
# fails the Job rather than reporting "fine, do nothing" -- the alternative is a
# transient API error or an RBAC denial leaving a certificate that names nothing
# in place for the life of the cluster.
keep_existing_cert() {
    local encoded pem subject san name
    # Read and decoded in two steps: this runs inside an `if`, where `set -e`
    # is disabled, so a kubectl that failed would otherwise be indistinguishable
    # from a secret with an empty tls.crt.
    if ! encoded="$(kubectl get secret "${CERT_SECRET_NAME}" -n "${NAMESPACE}" \
        -o jsonpath='{.data.tls\.crt}')"; then
        echo >&2 "[!] Error: could not read secret '${CERT_SECRET_NAME}'"
        exit 1
    fi
    pem="$(base64 -d <<< "${encoded}")"
    if [[ -z "${pem}" ]]; then
        echo >&2 "[!] Error: secret '${CERT_SECRET_NAME}' carries no tls.crt"
        exit 1
    fi
    if ! subject="$(openssl x509 -noout -subject <<< "${pem}")"; then
        echo >&2 "[!] Error: could not parse the certificate in '${CERT_SECRET_NAME}'"
        exit 1
    fi

    # Anchored on the field rather than a substring: the mTLS CA's
    # Organization contains this one, and a substring match would let this Job
    # claim a certificate it did not issue.
    if ! grep --extended-regexp --quiet "O *= *${CERT_ORG}(,|\$)" <<< "${subject}"; then
        echo "[-] '${CERT_SECRET_NAME}' was not issued by this Job, keeping it"
        return 0
    fi

    # An expired certificate verifies nowhere, and nothing else renews this one
    # -- without this a cluster older than the -days below keeps it forever.
    if ! openssl x509 -noout -checkend $((30 * 24 * 3600)) <<< "${pem}" > /dev/null; then
        echo "[-] '${CERT_SECRET_NAME}' expires within 30 days"
        return 1
    fi

    san="$(openssl x509 -noout -ext subjectAltName <<< "${pem}" 2>/dev/null || true)"
    for name in "${LOOM_HOSTNAMES[@]}"; do
        if ! grep -F "DNS:${name}.${LOOM_DOMAIN}" <<< "${san}" > /dev/null; then
            echo "[-] '${CERT_SECRET_NAME}' does not cover ${name}.${LOOM_DOMAIN}"
            return 1
        fi
    done
    return 0
}

create_self_signed_cert() {
    if kubectl get secret "${CERT_SECRET_NAME}" -n "${NAMESPACE}" &> /dev/null; then
        # Regenerated rather than kept when it cannot verify. A certificate
        # this Job made that names none of the hosts is not a certificate
        # anything can use, and keeping it means every programmatic client over
        # `https://*.loom` stays broken for the life of the cluster, with the
        # services behind those names serving perfectly.
        # shellcheck disable=SC2310
        if keep_existing_cert; then
            echo "[-] Certificate '${CERT_SECRET_NAME}' already exists in namespace"
            return
        fi
        echo "[*] Replacing '${CERT_SECRET_NAME}' with one that names every host"
    fi

    local common_name san
    common_name="*.${LOOM_DOMAIN}"
    # Built before openssl runs rather than inside its argument list, so a
    # failure here fails the Job instead of producing a certificate with an
    # empty subjectAltName.
    san="$(san_argument)"

    # Generate self-signed cert and key.
    #
    # -addext is not decoration, and a wildcard in it is not enough. RFC 6125
    # deprecated matching the hostname against CN, and every modern TLS client
    # now ignores CN outright when a subjectAltName is present -- so the SAN has
    # to be right.
    #
    # Measured, against `openssl s_server` with each variant:
    #
    #   no SAN at all       curl: (60) SSL: certificate subject name '*.loom'
    #                       does not match target hostname 'ollama.loom'
    #   SAN DNS:*.loom      curl: (60) SSL: no alternative certificate subject
    #                       name matches target hostname 'ollama.loom'
    #   SAN DNS:ollama.loom verified
    #
    # A wildcard pattern needs at least two dots: OpenSSL will not expand one
    # that sits directly under a single-label parent, so `*.loom` is compared
    # literally and matches nothing. Node and Bun inherit that rule, so a client
    # that trusts this certificate outright still sits forever on a connection
    # to ollama.loom it cannot verify.
    #
    # Hence every host by name. The wildcard and the bare domain stay on the
    # list: they cost nothing and a browser dialog still shows them.
    #
    # The two extensions after the SAN are what makes this a serving leaf rather
    # than a CA: `openssl req -x509` with no -extensions picks up the stock
    # `v3_ca` section, which sets `basicConstraints: critical, CA:TRUE` and no
    # extendedKeyUsage at all. A manually trusted leaf without `serverAuth` is
    # rejected outright by the macOS and iOS trust stores, so the names alone
    # would not finish the job there.
    #
    # There is deliberately no `keyUsage`, and that is not an oversight. Nothing
    # issues this certificate, so every client that trusts it trusts it as its
    # own anchor -- `loom-chat` in nixos/console.nix hands it to Bun in
    # NODE_EXTRA_CA_CERTS, and install_cluster_ca in
    # nixos/usb-ingest/loom_usb_ingest/transfer.py writes it into mc's CA
    # directory. A verifier asked to use a certificate as an anchor checks
    # whether it is allowed to have signed anything, and a critical `keyUsage`
    # without `keyCertSign` says it is not.
    #
    # Measured, one fake TLS server per variant, the certificate the only thing
    # that changed:
    #
    #   CA:FALSE, keyUsage w/o keyCertSign  Bun: unable to verify the first
    #                                       certificate. curl, node and Go: ok
    #   CA:TRUE, same keyUsage              Bun: same failure -- so this is the
    #                                       keyUsage, not basicConstraints
    #   CA:FALSE, no keyUsage               all four verify
    #
    # OpenSSL (so curl, and node) and Go accept a self-signed certificate found
    # in their trust store whatever its keyUsage says; Bun's BoringSSL does not.
    # That split is worth knowing when reading a bug report: on a box serving
    # such a certificate the appliance's `curl` readiness probe passes and only
    # opencode's own request fails.
    #
    # Adding `keyCertSign` beside CA:FALSE would also work, and would be a
    # contradiction some verifier is entitled to reject later -- so it would
    # have to come with CA:TRUE, which is a serving certificate that may sign
    # others. Emitting no keyUsage avoids the question entirely, and is
    # available here only because openssl will leave the extension out.
    # cert-manager will not: charts/templates/common/certificate.yaml therefore
    # takes the other branch -- `cert sign` *and* `isCA: true` -- and says so.
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:4096 \
        -keyout "${KEY_FILE}" \
        -out "${CRT_FILE}" \
        -subj "/CN=${common_name}/O=${CERT_ORG}" \
        -addext "subjectAltName=${san}" \
        -addext "basicConstraints=critical,CA:FALSE" \
        -addext "extendedKeyUsage=serverAuth"

    # Written in one step rather than delete-then-create: this secret is the
    # defaultCertificate of Traefik's TLSStore, and a delete that is not
    # followed by a create -- a rejected create, an evicted pod -- leaves every
    # host served by Traefik's built-in default certificate instead.
    kubectl create secret tls "${CERT_SECRET_NAME}" \
        --cert="${CRT_FILE}" \
        --key="${KEY_FILE}" \
        --namespace="${NAMESPACE}" \
        --dry-run=client -o yaml \
        | kubectl apply -f -
}

#
# Atexit
#
atexit() {
    rm -f \
        "${CRT_FILE}" \
        "${KEY_FILE}"
}
trap atexit EXIT

#
# Argument parsing
#
while [[ $# -gt 0 ]]; do
    case "${1}" in
        --namespace)
            shift
            NAMESPACE="${1?Missing NAMESPACE}"
            shift
        ;;
        --domain)
            shift
            LOOM_DOMAIN="${1?Missing DOMAIN}"
            shift
        ;;
        --hostname)
            shift
            # Checked here rather than counted later: `${1?...}` fires on
            # unset, not on empty, and san_argument joins on commas, so an
            # empty entry yields `DNS:.loom` and an entry containing a comma
            # splices an arbitrary extra name into the certificate. openssl
            # accepts both, and the coverage check then greps for the junk name
            # and is satisfied by it.
            if [[ ! "${1?Missing NAME}" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
                echo >&2 "[!] Error: invalid hostname: '${1}'"
                exit 1
            fi
            LOOM_HOSTNAMES+=("${1}")
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

if [[ -z "${NAMESPACE}" || -z "${LOOM_DOMAIN}" || ${#LOOM_HOSTNAMES[@]} -eq 0 ]]; then
    echo >&2 "[!] Error: --namespace, --domain and at least one --hostname are required"
    usage >&2
    exit 1
fi

#
# Main
#
create_self_signed_cert
