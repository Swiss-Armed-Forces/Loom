#!/usr/bin/env bash
set -euo pipefail

#
# Environment
#
NAMESPACE="${NAMESPACE:-loom}"

#
# Defines
#
SECRET_NAME="self-signed-mtls-cert"
CLIENT_NAME="client-$(date +%s)"
CERT_VALIDITY_DAYS="60"

CA_CERT_FILE="$(mktemp)"
CA_KEY_FILE="$(mktemp)"
CLIENT_KEY_FILE="$(mktemp)"
CLIENT_CSR_FILE="$(mktemp)"
CLIENT_CERT_FILE="$(mktemp)"
PKCS12_FILE="${CLIENT_NAME}.p12"

#
# Functions
#

# --- Step 1: Fetch CA cert and key from Kubernetes ---
fetch_ca_from_k8s() {
    echo "[*] Fetching CA cert and key from Kubernetes secret '${SECRET_NAME}' in namespace '${NAMESPACE}'..."

    kubectl get secret "${SECRET_NAME}" \
        --namespace="${NAMESPACE}" \
        --output="jsonpath={.data['ca\.crt']}" \
        | base64 --decode > "${CA_CERT_FILE}"

    kubectl get secret "${SECRET_NAME}" \
        --namespace="${NAMESPACE}" \
        --output="jsonpath={.data['ca\.key']}" \
        | base64 --decode > "${CA_KEY_FILE}"
}

# --- Step 2: Generate client private key and CSR ---
generate_client_key_and_csr() {
    echo "[*] Generating client key and CSR..."

    openssl genrsa \
        --out "${CLIENT_KEY_FILE}" \
        2048

    openssl req \
        --new \
        --key "${CLIENT_KEY_FILE}" \
        --subj "/CN=${CLIENT_NAME}" \
        --out "${CLIENT_CSR_FILE}"
}

# --- Step 3: Sign the client certificate with the CA ---
sign_client_cert() {
    echo "[*] Signing client certificate with CA..."

    openssl x509 \
        --req \
        --in "${CLIENT_CSR_FILE}" \
        --CA "${CA_CERT_FILE}" \
        --CAkey "${CA_KEY_FILE}" \
        --CAcreateserial \
        --out "${CLIENT_CERT_FILE}" \
        --days "${CERT_VALIDITY_DAYS}" \
        --sha256
}

# --- Step 4: Generate PKCS#12 bundle for browser import ---
generate_pkcs12_bundle() {
    echo "[*] Generating PKCS#12 bundle..."

    openssl pkcs12 \
        --export \
        --inkey "${CLIENT_KEY_FILE}" \
        --in "${CLIENT_CERT_FILE}" \
        --certfile "${CA_CERT_FILE}" \
        --out "${PKCS12_FILE}" \
        --name "${CLIENT_NAME}" \
        --passout pass:

    echo "[✔] PKCS#12 bundle created:"
    echo "  - File: ${PKCS12_FILE}"
    echo "  - Password: (none)"
}

#
# Atexit
#
atexit() {
    echo "[*] Cleaning up CA files..."
    rm --force \
        "${CA_CERT_FILE}" \
        "${CA_KEY_FILE}" \
        "${CLIENT_CERT_FILE}" \
        "${CLIENT_KEY_FILE}" \
        "${CLIENT_CSR_FILE}"
}
trap atexit EXIT

#
# Main
#
fetch_ca_from_k8s
generate_client_key_and_csr
sign_client_cert
generate_pkcs12_bundle