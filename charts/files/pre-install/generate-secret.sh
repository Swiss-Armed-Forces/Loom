#!/usr/bin/env bash
#
# Creates one generated secret, named by the environment. One Job per entry in
# .Values.preInstall.generateSecret runs this same script.
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
# secret generated from an empty size or character set is not a secret.
NAMESPACE=""
SECRET_ENVIRONMENT=""
SECRET_NAME=""
SECRET_SIZE=""
SECRET_CHARS=""
SECRET_FIXED=""

#
# Usage
#
usage(){
    echo "usage: ${0} --namespace NAMESPACE --environment ENV --name NAME --size SIZE --chars CHARS --fixed SECRET"
    echo "  --namespace NAMESPACE   namespace the secret is created in"
    echo "  --environment ENV       deployment environment; 'development' uses the fixed secret"
    echo "  --name NAME             name of the secret to create"
    echo "  --size SIZE             length of the generated secret"
    echo "  --chars CHARS           tr(1) character set the secret is drawn from"
    echo "  --fixed SECRET          secret to use in the development environment"
    echo "  -h|--help               show this help"
}

#
# Functions
#
get_secret_key() {
    kubectl get secret "${SECRET_NAME}" \
        --namespace="${NAMESPACE}" \
        -o jsonpath="{.data.secretkey}" \
        2> /dev/null \
        | base64 -d
}

delete_secret_key() {
    kubectl delete secret "${SECRET_NAME}" \
        --namespace="${NAMESPACE}" \
        &> /dev/null \
        || true
}

is_using_fixed_secret() {
    # An empty --fixed is allowed outside `development`, and an absent secret
    # reads back as empty too -- so the comparison is only meaningful for a
    # fixed value there is something to match.
    [[ -n "${SECRET_FIXED}" ]] || return 1
    # shellcheck disable=SC2310
    [[ "$(get_secret_key || true)" == "${SECRET_FIXED}" ]]
}

use_fixed_secret() {
    [[ "${SECRET_ENVIRONMENT}" = "development" ]]
}

create_secret() {
    local secret_key
    local use_fixed_key

    # shellcheck disable=SC2310
    if is_using_fixed_secret; then
        echo "[*] Deleting fixed secret: '${SECRET_NAME}'"
        delete_secret_key
    fi

    # shellcheck disable=SC2310
    if ! use_fixed_secret; then
        use_fixed_key="false"
        secret_key="$(< /dev/urandom tr -dc "${SECRET_CHARS}" | head -c "${SECRET_SIZE}" || true)"
    else
        use_fixed_key="true"
        secret_key="${SECRET_FIXED}"
        delete_secret_key
    fi

    # shellcheck disable=SC2310
    if get_secret_key &> /dev/null; then
        echo "[*] Secret '${SECRET_NAME}' already exists"
        return
    fi

    echo "[*] Create secret: '${SECRET_NAME}' (size: ${SECRET_SIZE}, fixed: ${use_fixed_key})"
    kubectl create secret generic "${SECRET_NAME}" \
        --namespace="${NAMESPACE}" \
        --from-literal=secretkey="${secret_key}"
}

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
        --environment)
            shift
            SECRET_ENVIRONMENT="${1?Missing ENV}"
            shift
        ;;
        --name)
            shift
            SECRET_NAME="${1?Missing NAME}"
            shift
        ;;
        --size)
            shift
            SECRET_SIZE="${1?Missing SIZE}"
            shift
        ;;
        --chars)
            shift
            SECRET_CHARS="${1?Missing CHARS}"
            shift
        ;;
        --fixed)
            shift
            SECRET_FIXED="${1?Missing SECRET}"
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

if [[ -z "${NAMESPACE}" \
    || -z "${SECRET_ENVIRONMENT}" \
    || -z "${SECRET_NAME}" \
    || -z "${SECRET_SIZE}" \
    || -z "${SECRET_CHARS}" ]]; then
    echo >&2 "[!] Error: --namespace, --environment, --name, --size and --chars are required"
    usage >&2
    exit 1
fi

# --fixed only outside its own environment is a missing value nothing reads: an
# entry in .Values.preInstall.generateSecret with no development secret is a
# legitimate entry, and it is only in `development` that an empty one would
# silently install an empty secret.
# shellcheck disable=SC2310
if use_fixed_secret && [[ -z "${SECRET_FIXED}" ]]; then
    echo >&2 "[!] Error: --fixed is required in the 'development' environment"
    usage >&2
    exit 1
fi

#
# Main
#
create_secret
