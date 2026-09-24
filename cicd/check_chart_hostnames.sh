#!/usr/bin/env bash
#
# Asserts that `hostnames.ingress` in charts/values.yaml is exactly the set of
# hosts the chart routes by name.
#
# The routes are the authority: `spec.rules[].host` on an Ingress, and
# HostSNI(`<name>.<domain>`) on a Traefik IngressRouteTCP, are what Traefik
# actually matches, and they are written per template. The list in values.yaml
# is a restatement, and it exists only because a Helm template cannot read what
# its siblings rendered -- the pre-install Job that generates the TLS
# certificate has to name every host in a subjectAltName, and it has no way to
# enumerate them. This script is what keeps the restatement honest.
#
# `hostnames.extra` is deliberately not checked against anything: those hosts
# have no route that names them. They match HostSNI(`*`) and are told apart by
# entrypoint, or they come from another chart, so nothing here implies the name.
#
# Also asserts, per Ingress, that `spec.tls[].hosts` is a subset of that
# Ingress's `spec.rules[].host`: Traefik keys off `secretName`, so a TLS block
# naming a host the rules do not serve breaks nothing at request time and is
# invisible until somebody reads the certificate it implies.
#
# Runs `helm template`, which is client-side -- no cluster, no network.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${CONTEXT_DIR}/charts"
RELEASE="loom"
# Read off the chart in main, so --chart is honoured.
DOMAIN=""
MANIFEST=""

# The two yq programs, in quoted heredocs rather than inline single quotes:
# both carry backticks and jq variables, which a shell reads as syntax of its
# own.

# Every host the chart names in a route, selected by object kind rather than
# grepped out of the stream: the rendered output carries the pre-install
# scripts' ConfigMap and a settings ConfigMap besides the objects of interest,
# and any line in either that happened to look like a host key would become a
# phantom entry with no way to tell it apart from a real one.
ROUTED_HOSTS_PROGRAM="$(cat <<'JQ'
if .kind == "Ingress" then
    .spec.rules[]?.host
elif .kind == "IngressRouteTCP" then
    (.spec.routes[]?.match | scan("HostSNI\\(`([^`]+)`\\)")[0]),
    (.spec.tls.domains[]?.main)
else
    empty
end
JQ
)"

# Per Ingress, the tls[].hosts entries its own rules do not serve.
STRAY_TLS_HOSTS_PROGRAM="$(cat <<'JQ'
select(.kind == "Ingress")
| . as $ingress
| [$ingress.spec.rules[]?.host] as $rules
| $ingress.spec.tls[]?.hosts[]? as $host
| select(($rules | index($host)) == null)
| "\($ingress.metadata.name): \($host)"
JQ
)"

usage(){
    cat <<EOF
Usage: $(basename "${0}") [OPTIONS]

Compares charts/values.yaml's hostnames.ingress with the hosts the chart's
Ingress and IngressRouteTCP rules render.

OPTIONS:
  --chart DIR   chart to check (default: ${CHART_DIR})
  -h|--help     show this help
EOF
}

# Those hosts as short labels. The wildcard host of the http-to-https redirect
# Ingress, and HostSNI(`*`), are patterns rather than names: there is no `*`
# entry in values.yaml to match them, so they are dropped.
rendered_hosts(){
    local fqdns host
    fqdns="$(yq --raw-output "${ROUTED_HOSTS_PROGRAM}" <<< "${MANIFEST}")"

    # Suffix-stripped in bash rather than with sed: DOMAIN is interpolated from
    # values.yaml, and in a regex its dots are metacharacters and a slash in it
    # would break the s/// delimiter.
    while read -r host; do
        [[ -n "${host}" ]] || continue
        [[ "${host}" != \** ]] || continue
        printf '%s\n' "${host%".${DOMAIN}"}"
    done <<< "${fqdns}" | sort --unique
}

declared_hosts(){
    # Read straight out of values.yaml rather than through a rendered template:
    # what is being checked is the declaration itself, and a template that
    # reformatted it would hide a mistake in it.
    local hosts
    # Read, then sorted, in two steps rather than a pipeline, so `set -e` still
    # sees yq fail.
    hosts="$(yq --raw-output '.hostnames.ingress[]' "${CHART_DIR}/values.yaml")"
    sort --unique <<< "${hosts}"
}

check_tls_hosts(){
    local stray
    stray="$(yq --raw-output "${STRAY_TLS_HOSTS_PROGRAM}" <<< "${MANIFEST}")"
    [[ -n "${stray}" ]] || return 0

    echo >&2 "[!] Error: an Ingress names a host in spec.tls[].hosts that its own"
    echo >&2 "    spec.rules[].host does not serve:"
    printf '%s\n' "${stray}" | sed 's/^/      /' >&2
    return 1
}

check_declared_hosts(){
    local rendered declared count
    rendered="$(rendered_hosts)"
    declared="$(declared_hosts)"

    # An empty rendered set compares equal to an empty declared one, and `wc -l`
    # on an empty string still says 1 -- so without this the check passes and
    # reports a count in exactly the case it should be shouting.
    if [[ -z "${rendered}" ]]; then
        echo >&2 "[!] Error: the chart rendered no Ingress hosts. Either ${CHART_DIR}"
        echo >&2 "    declares none, or they are all gated off by its default values."
        return 1
    fi

    if [[ "${rendered}" == "${declared}" ]]; then
        count="$(grep --count . <<< "${rendered}")"
        echo "[*] hostnames.ingress matches the chart's ${count} routed hosts"
        return 0
    fi

    echo >&2 "[!] Error: hostnames.ingress in charts/values.yaml does not match the"
    echo >&2 "    hosts the chart's Ingress and IngressRouteTCP rules render."
    echo >&2 ""
    echo >&2 "    Missing from values.yaml (a route serves it, the certificate"
    echo >&2 "    would not cover it):"
    comm -23 <(printf '%s\n' "${rendered}") <(printf '%s\n' "${declared}") \
        | sed 's/^/      /' >&2
    echo >&2 ""
    echo >&2 "    In values.yaml with no route naming it (move it to hostnames.extra"
    echo >&2 "    if it is served by entrypoint instead):"
    comm -13 <(printf '%s\n' "${rendered}") <(printf '%s\n' "${declared}") \
        | sed 's/^/      /' >&2
    return 1
}

main(){
    DOMAIN="$(yq --raw-output '.domain' "${CHART_DIR}/values.yaml")"
    # An absent key leaves yq successful and printing "null", which would strip
    # a `.null` suffix off nothing and fail with a full host-list diff instead
    # of saying what actually went wrong.
    if [[ -z "${DOMAIN}" || "${DOMAIN}" == "null" ]]; then
        echo >&2 "[!] Error: could not read 'domain' from ${CHART_DIR}/values.yaml"
        return 1
    fi

    MANIFEST="$(helm template "${RELEASE}" "${CHART_DIR}")"

    # Plain calls rather than `||`-collected: `set -e` takes the first failure,
    # and either one on its own is a stop.
    check_declared_hosts
    check_tls_hosts
}

while (( $# )); do
    case "${1}" in
        --chart)
            shift
            CHART_DIR="${1?Missing DIR}"
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

main
