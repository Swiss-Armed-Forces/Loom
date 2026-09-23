#!/usr/bin/env bash
#
# Puts a self-signed CA keypair in the `self-signed-mtls-cert` secret, for the
# client certificates mutual TLS is verified against, unless one is already
# there.
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
# a missing one means the template and this script have drifted apart, and a CA
# issued for an empty domain is worse than a hook that fails loudly.
NAMESPACE=""
LOOM_DOMAIN=""

MTLS_CERT_SECRET_NAME="self-signed-mtls-cert"
# The Organization this Job stamps on the CA it issues. A constant for the same
# reason CERT_ORG is one in the sibling script, and worth noting that it
# contains that value as a prefix: the sibling's ownership test anchors on the
# whole field so that a "Wildcard Self-Signed MTLS" CA is never claimed as its
# serving certificate.
MTLS_CERT_ORG="Wildcard Self-Signed MTLS"

CRT_FILE="$(mktemp)"
KEY_FILE="$(mktemp)"

#
# Usage
#
usage(){
    echo "usage: ${0} --namespace NAMESPACE --domain DOMAIN"
    echo "  --namespace NAMESPACE   namespace the CA secret is created in"
    echo "  --domain DOMAIN         domain the CA is issued for"
    echo "  -h|--help               show this help"
}

#
# Functions
#
# Whether the CA already in the cluster is to be kept. Structured like
# keep_existing_cert() in the sibling script: a CA without this Job's marker is
# somebody else's and is never touched, one that cannot be read at all is an
# error rather than a reason to do nothing, and an expired one is replaced --
# nothing else renews it, so without this a cluster older than the -days below
# verifies no client certificate ever again.
keep_existing_mtls_cert() {
    local encoded pem subject
    # Read and decoded in two steps: this runs inside an `if`, where `set -e`
    # is disabled, so a kubectl that failed would otherwise be indistinguishable
    # from a secret with an empty ca.crt.
    if ! encoded="$(kubectl get secret "${MTLS_CERT_SECRET_NAME}" -n "${NAMESPACE}" \
        -o jsonpath='{.data.ca\.crt}')"; then
        echo >&2 "[!] Error: could not read secret '${MTLS_CERT_SECRET_NAME}'"
        exit 1
    fi
    pem="$(base64 -d <<< "${encoded}")"
    if [[ -z "${pem}" ]]; then
        echo >&2 "[!] Error: secret '${MTLS_CERT_SECRET_NAME}' carries no ca.crt"
        exit 1
    fi
    if ! subject="$(openssl x509 -noout -subject <<< "${pem}")"; then
        echo >&2 "[!] Error: could not parse the CA in '${MTLS_CERT_SECRET_NAME}'"
        exit 1
    fi

    if ! grep --extended-regexp --quiet "O *= *${MTLS_CERT_ORG}(,|\$)" <<< "${subject}"; then
        echo "[-] '${MTLS_CERT_SECRET_NAME}' was not issued by this Job, keeping it"
        return 0
    fi

    if ! openssl x509 -noout -checkend $((30 * 24 * 3600)) <<< "${pem}" > /dev/null; then
        echo "[-] '${MTLS_CERT_SECRET_NAME}' expires within 30 days"
        return 1
    fi
    return 0
}

create_self_signed_mtls_cert() {
    if kubectl get secret "${MTLS_CERT_SECRET_NAME}" -n "${NAMESPACE}" &> /dev/null; then
        # shellcheck disable=SC2310
        if keep_existing_mtls_cert; then
            echo "[-] Certificate '${MTLS_CERT_SECRET_NAME}' already exists in namespace"
            return
        fi
        echo "[*] Replacing '${MTLS_CERT_SECRET_NAME}'"
    fi

    local common_name
    common_name="*.${LOOM_DOMAIN}"

    # Generate self-signed cert and key
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:4096 \
        -keyout "${KEY_FILE}" \
        -out "${CRT_FILE}" \
        -subj "/CN=${common_name}/O=${MTLS_CERT_ORG}"

    # Written in one step rather than delete-then-create, so a failure between
    # the two never leaves mutual TLS with no CA to verify against.
    kubectl create secret generic "${MTLS_CERT_SECRET_NAME}" \
        --from-file=ca.crt="${CRT_FILE}" \
        --from-file=ca.key="${KEY_FILE}" \
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

if [[ -z "${NAMESPACE}" || -z "${LOOM_DOMAIN}" ]]; then
    echo >&2 "[!] Error: --namespace and --domain are required"
    usage >&2
    exit 1
fi

#
# Main
#
create_self_signed_mtls_cert
