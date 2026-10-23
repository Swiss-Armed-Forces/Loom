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
# And the question `certificate.requireClientCert` rests on: that every route
# this chart renders with it set is one the requirement actually reaches.
#
# It is carried by a `router.tls.options` annotation pasted into each of the
# chart's Ingress templates, one copy per service, and by nothing else --
# `spec.tls` does not imply it, and traefik's `websecure` entrypoint sets
# `http.tls=true` for everything on it, so a router can be a perfectly good TLS
# router and still demand no certificate. An Ingress copied from a sibling
# without those three lines is therefore the regression to catch, and it needs
# no unusual route to happen. An IngressRouteTCP is the other shape: on a
# plain entrypoint, or on `websecure` with no `tls`, it terminates nothing the
# option could attach to.
#
# Scope, which is the word "this chart" above: routes rendered by the *traefik*
# chart are outside it, and the dashboard it enables on `websecure` is one of
# them. See the threat-model section of Documentation/appliance.md.
#
# Runs `helm template`, which is client-side -- no cluster, no network.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${CONTEXT_DIR}/charts"
RELEASE="loom"
# Read off the chart in main, so --chart is honoured.
DOMAIN=""
MANIFEST=""
MTLS_MANIFEST=""

# The yq programs, in quoted heredocs rather than inline single quotes:
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

# The same question for TCP routes, asked of both halves. `websecure` is the
# only entrypoint traefik terminates TLS on (traefik/values.yaml), so a route
# on any of the others -- amqp, redis, redis-cache, imap, prometheus -- is a
# plain listener the requirement cannot reach. And a route that *is* on
# `websecure` with `tls` unset terminates none either, which is one value away
# in charts/templates/dovecot/ingressRoute.yaml and would pass a check that
# only looked at the entrypoint.
UNSECURED_TCP_ROUTE_PROGRAM="$(cat <<'JQ'
select(.kind == "IngressRouteTCP")
| . as $route
| ([$route.spec.entryPoints[]?] | index("websecure")) as $secure
| if $secure == null then
      $route.spec.entryPoints[]?
      | "\($route.metadata.name): on entrypoint \(.), which terminates no TLS"
  elif ($route.spec.tls | not) then
      "\($route.metadata.name): on websecure with no spec.tls"
  else
      empty
  end
JQ
)"

# Whether the requirement is attached at all, which is the regression that
# needs no unusual route to happen.
#
# The TLSOption is referenced by a `router.tls.options` annotation pasted into
# every one of the chart's Ingress templates, one copy each. A new service
# whose Ingress was copied from a sibling without that block renders on
# `websecure`, with TLS, demanding nothing -- and every check above passes it.
# The redirect Ingress is the one legitimate exception: it is on `web`, where
# there is no TLS to attach an option to.
#
# An Ingress with *no* entrypoints annotation counts as being on websecure, and
# that is not a technicality: traefik attaches such a router to every default
# entrypoint, and traefik/values.yaml marks none of its seven as non-default.
# Reading a missing annotation as "not websecure" would have skipped exactly
# the template that forgot to say where it belongs.
UNGUARDED_INGRESS_PROGRAM="$(cat <<'JQ'
select(.kind == "Ingress")
| . as $ingress
| ($ingress.metadata.annotations["traefik.ingress.kubernetes.io/router.entrypoints"]) as $entrypoints
| select($entrypoints == null or ($entrypoints | test("(^|,)[[:space:]]*websecure[[:space:]]*(,|$)")))
| select($ingress.metadata.annotations["traefik.ingress.kubernetes.io/router.tls.options"] == null)
| "\($ingress.metadata.name)\(if $entrypoints == null then " (no entrypoints annotation)" else "" end)"
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

# What `certificate.requireClientCert` is actually worth, asked of the manifest
# that sets it. Both answers are "nothing escapes", and both are true today
# only because of what the chart leaves switched off -- which is the kind of
# true that stops being true in a merge request nobody connected to mutual TLS.
check_client_cert_coverage(){
    local unguarded tcp status=0

    unguarded="$(yq --raw-output "${UNGUARDED_INGRESS_PROGRAM}" <<< "${MTLS_MANIFEST}")"
    if [[ -n "${unguarded}" ]]; then
        echo >&2 "[!] Error: an Ingress routes on websecure without the TLSOption that"
        echo >&2 "    carries the client-certificate requirement, so traefik serves it"
        echo >&2 "    with the default options and demands nothing:"
        printf '%s\n' "${unguarded}" | sed 's/^/      /' >&2
        status=1
    fi

    tcp="$(yq --raw-output "${UNSECURED_TCP_ROUTE_PROGRAM}" <<< "${MTLS_MANIFEST}")"
    if [[ -n "${tcp}" ]]; then
        echo >&2 "[!] Error: an IngressRouteTCP sits on an entrypoint that does not"
        echo >&2 "    terminate TLS, so certificate.requireClientCert does not cover it:"
        printf '%s\n' "${tcp}" | sed 's/^/      /' >&2
        status=1
    fi

    [[ "${status}" -eq 0 ]] || return 1
    echo "[*] every route the chart renders is covered by requireClientCert"
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

    # A second rendering, because the question the third check asks is only
    # meaningful with the requirement on, and the default values leave it off.
    MTLS_MANIFEST="$(helm template "${RELEASE}" "${CHART_DIR}" \
        --set certificate.requireClientCert=true)"

    # Plain calls rather than `||`-collected: `set -e` takes the first failure,
    # and any one of them on its own is a stop.
    check_declared_hosts
    check_tls_hosts
    check_client_cert_coverage
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
