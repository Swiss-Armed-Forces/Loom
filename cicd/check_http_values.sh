#!/usr/bin/env bash
#
# Asserts that charts/values-http.yaml moves *every* HTTP Ingress onto Traefik's
# `web` entrypoint, and that it turns the global http-to-https redirect off.
#
# The rendered manifest is the authority rather than the values file: what
# matters is the annotation each Ingress ends up carrying, and values-http.yaml
# has to restate a component path per Ingress to produce it. A component added
# to values.yaml with an ingress of its own renders a router that still listens
# on `websecure` alone, and nothing else in the repository would notice --
# `--enable-http` would simply not reach it, and the symptom is a service that
# 404s over http for no visible reason.
#
# Checking the annotation rather than comparing key sets is what keeps this
# honest through the chart's own shapes: `rabbit.ingress.http` sits a level
# deeper than the rest, and `dovecot.ingress.imaps` shares the same values
# anchor while rendering an IngressRouteTCP whose entrypoint its template pins.
# A textual comparison has to special-case both; this sees neither.
#
# The redirect half is not a formality. templates/global-http-redirect/ingress.yaml
# matches `*.<domain>` on `web` and answers before any of the widened routers,
# so leaving it on makes the whole values file invisible at request time.
#
# Runs `helm template`, which is client-side -- no cluster, no network.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${CONTEXT_DIR}/charts"
HTTP_VALUES=""
RELEASE="loom"
MANIFEST=""

# In a quoted heredoc rather than inline single quotes: the program carries jq
# variables and a regex, which a shell reads as syntax of its own.
#
# The annotation is split on `,` because that is how the chart writes it
# ("web, websecure"), and each token trimmed, so a router listening on
# `websecure` alone is told apart from one that merely lists `web` second.
NO_WEB_ENTRYPOINT_PROGRAM="$(cat <<'JQ'
select(.kind == "Ingress")
| . as $ingress
| ($ingress.metadata.annotations["traefik.ingress.kubernetes.io/router.entrypoints"] // "") as $entrypoints
| ($entrypoints | split(",") | map(sub("^ +"; "") | sub(" +$"; ""))) as $listed
| select(($listed | index("web")) == null)
| "\($ingress.metadata.name): \(if $entrypoints == "" then "<no entrypoints annotation>" else $entrypoints end)"
JQ
)"

INGRESS_NAMES_PROGRAM='select(.kind == "Ingress") | .metadata.name'

usage(){
    cat <<EOF
Usage: $(basename "${0}") [OPTIONS]

Renders the chart with charts/values-http.yaml and asserts every Ingress
listens on Traefik's 'web' entrypoint, and that the global http-to-https
redirect is off.

OPTIONS:
  --chart DIR    chart to check (default: ${CHART_DIR})
  --values FILE  http values file (default: <chart>/values-http.yaml)
  -h|--help      show this help
EOF
}

check_every_ingress_on_web(){
    local stray rendered count
    rendered="$(yq --raw-output "${INGRESS_NAMES_PROGRAM}" <<< "${MANIFEST}")"

    # An empty rendered set would make the stray check below pass by having
    # nothing to look at -- which is exactly the case worth shouting about.
    if [[ -z "${rendered}" ]]; then
        echo >&2 "[!] Error: the chart rendered no Ingress at all. Either ${CHART_DIR}"
        echo >&2 "    declares none, or they are gated off by its default values."
        return 1
    fi

    stray="$(yq --raw-output "${NO_WEB_ENTRYPOINT_PROGRAM}" <<< "${MANIFEST}")"
    if [[ -z "${stray}" ]]; then
        count="$(grep --count . <<< "${rendered}")"
        echo "[*] values-http.yaml puts all ${count} Ingresses on the web entrypoint"
        return 0
    fi

    echo >&2 "[!] Error: ${HTTP_VALUES} leaves an Ingress off the 'web' entrypoint,"
    echo >&2 "    so --enable-http would not reach it:"
    printf '%s\n' "${stray}" | sed 's/^/      /' >&2
    echo >&2 ""
    echo >&2 "    Add the component's path to ${HTTP_VALUES}, mirroring how it is"
    echo >&2 "    nested in values.yaml. Note rabbit's is rabbit.ingress.http."
    return 1
}

check_global_redirect_off(){
    local redirect
    # Matched on the rendered name rather than on the values key: what breaks
    # the feature is the object existing, whatever turned it on.
    redirect="$(yq --raw-output \
        'select((.metadata.name? // "") | endswith("global-http-redirect")) | "\(.kind)/\(.metadata.name)"' \
        <<< "${MANIFEST}")"
    [[ -n "${redirect}" ]] || return 0

    echo >&2 "[!] Error: the global http-to-https redirect still renders with"
    echo >&2 "    ${HTTP_VALUES} applied. It matches '*.<domain>' on the web"
    echo >&2 "    entrypoint and answers ahead of every widened router, so the"
    echo >&2 "    whole values file has no visible effect. Set"
    echo >&2 "    globalHttpRedirect.enabled to false there."
    printf '%s\n' "${redirect}" | sed 's/^/      /' >&2
    return 1
}

main(){
    [[ -n "${HTTP_VALUES}" ]] || HTTP_VALUES="${CHART_DIR}/values-http.yaml"

    if [[ ! -f "${HTTP_VALUES}" ]]; then
        echo >&2 "[!] Error: values file not found: ${HTTP_VALUES}"
        return 1
    fi

    MANIFEST="$(helm template "${RELEASE}" "${CHART_DIR}" --values "${HTTP_VALUES}")"

    # Plain calls rather than `||`-collected: `set -e` takes the first failure,
    # and either one on its own is a stop.
    check_every_ingress_on_web
    check_global_redirect_off
}

while (( $# )); do
    case "${1}" in
        --chart)
            shift
            CHART_DIR="${1?Missing DIR}"
            shift
        ;;
        --values)
            shift
            HTTP_VALUES="${1?Missing FILE}"
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
