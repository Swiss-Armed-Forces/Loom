#!/usr/bin/env bash
#
# Asserts that Loom is never served in cleartext, and that the one layer which
# does serve cleartext still covers the whole chart.
#
# Three things are checked, against `helm template` output rather than against
# the values files: what matters is the annotation each Ingress ends up
# carrying, and a values file has to restate a component path per Ingress to
# produce it.
#
#   1. A deployment -- the chart's own defaults -- renders no Ingress on
#      Traefik's `web` entrypoint, and does render the global http-to-https
#      redirect. Together those are what make port 80 answer with a redirect
#      and nothing else, for every host.
#   2. The Traefik dashboard route, which lives in the sibling traefik chart's
#      values and so is invisible to the render above, lists no `web`
#      entrypoint either.
#   3. charts/values-development-http.yaml moves *every* Ingress onto `web` and
#      turns the redirect off. A component added to values.yaml with an ingress
#      of its own renders a router that stays on `websecure` alone, and nothing
#      else in the repository would notice -- the symptom is a service that 404s
#      over http in the development profile for no visible reason.
#
# Checking the annotation rather than comparing key sets is what keeps this
# honest through the chart's own shapes: `rabbit.ingress.http` sits a level
# deeper than the rest, and `dovecot.ingress.imaps` shares the same values
# anchor while rendering an IngressRouteTCP whose entrypoint its template pins.
# A textual comparison has to special-case both; this sees neither.
#
# The redirect halves are not a formality in either direction.
# templates/global-http-redirect/ingress.yaml matches `*.<domain>` on `web` and
# answers ahead of every other router, so it is both the whole of what a
# deployment serves on port 80 and what would make the development layer
# invisible at request time.
#
# The development layer is rendered twice: once over the chart's defaults, and
# once with charts/values-development.yaml beneath it, because up.sh applies it
# for the dev and integration-test profiles together. A component that
# values-development.yaml enables and values.yaml leaves off would otherwise get
# an Ingress in dev that this check never renders -- and that deployment is
# load-bearing for the integration tests, which reach Loom over
# http://rabbit.loom and http://elasticsearch.loom.
#
# Runs `helm template`, which is client-side -- no cluster, no network.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${CONTEXT_DIR}/charts"
TRAEFIK_VALUES=""
HTTP_VALUES=""
DEV_VALUES=""
RELEASE="loom"
MANIFEST=""
# Which render the messages below are talking about.
LAYER="a deployment"

# In a quoted heredoc rather than inline single quotes: the program carries jq
# variables and a regex, which a shell reads as syntax of its own.
#
# The annotation is split on `,` because that is how the chart writes it
# ("web, websecure"), and each token trimmed, so a router listening on
# `websecure` alone is told apart from one that merely lists `web` second.
WEB_ENTRYPOINT_PROGRAM="$(cat <<'JQ'
select(.kind == "Ingress")
| select((.metadata.name // "") | endswith("global-http-redirect") | not)
| . as $ingress
| ($ingress.metadata.annotations["traefik.ingress.kubernetes.io/router.entrypoints"] // "") as $entrypoints
| ($entrypoints | split(",") | map(sub("^ +"; "") | sub(" +$"; ""))) as $listed
| {
    name: $ingress.metadata.name,
    entrypoints: (if $entrypoints == "" then "<no entrypoints annotation>" else $entrypoints end),
    web: (($listed | index("web")) != null)
  }
| select(.web == ($web == "true"))
| "\(.name): \(.entrypoints)"
JQ
)"

# The redirect's own Ingress is excluded from both: it is the one object that
# must be on `web`, and counting it would make "every Ingress is on websecure"
# unsatisfiable and "every Ingress is on web" true for the wrong reason.
INGRESS_NAMES_PROGRAM='
select(.kind == "Ingress")
| select((.metadata.name // "") | endswith("global-http-redirect") | not)
| .metadata.name'

REDIRECT_PROGRAM='select((.metadata.name? // "") | endswith("global-http-redirect")) | "\(.kind)/\(.metadata.name)"'

usage(){
    cat <<EOF
Usage: $(basename "${0}") [OPTIONS]

Asserts that the chart's defaults serve https alone -- no Ingress on Traefik's
'web' entrypoint, and the global http-to-https redirect rendered -- that the
Traefik dashboard route agrees, and that charts/values-development-http.yaml
still moves every Ingress onto 'web' with the redirect off.

OPTIONS:
  --chart DIR    chart to check (default: ${CHART_DIR})
  --values FILE  development http values file
                (default: <chart>/values-development-http.yaml)
  --dev-values FILE
                development values file rendered as a second pass
                (default: <chart>/values-development.yaml)
  --traefik-values FILE
                traefik chart values carrying the dashboard route
                (default: <context>/traefik/values.yaml)
  -h|--help      show this help
EOF
}

# Ingresses in the current render that are on the web entrypoint, or that are
# not, as "<name>: <entrypoints>" lines.
ingresses_on_web(){
    yq --raw-output --arg web "${1}" "${WEB_ENTRYPOINT_PROGRAM}" <<< "${MANIFEST}"
}

rendered_ingress_count(){
    local rendered
    rendered="$(yq --raw-output "${INGRESS_NAMES_PROGRAM}" <<< "${MANIFEST}")"

    # An empty rendered set would make every check below pass by having nothing
    # to look at -- which is exactly the case worth shouting about.
    if [[ -z "${rendered}" ]]; then
        echo >&2 "[!] Error: the chart rendered no Ingress at all. Either ${CHART_DIR}"
        echo >&2 "    declares none, or they are gated off by its default values."
        return 1
    fi

    grep --count . <<< "${rendered}"
}

check_no_ingress_on_web(){
    local stray count
    count="$(rendered_ingress_count)"

    stray="$(ingresses_on_web true)"
    if [[ -z "${stray}" ]]; then
        echo "[*] ${LAYER}: all ${count} Ingresses are on websecure alone"
        return 0
    fi

    echo >&2 "[!] Error: with ${LAYER}, an Ingress answers on the 'web' entrypoint,"
    echo >&2 "    so Loom is served in cleartext:"
    printf '%s\n' "${stray}" | sed 's/^/      /' >&2
    echo >&2 ""
    echo >&2 "    Deployments serve https alone. Plain http belongs in"
    echo >&2 "    ${HTTP_VALUES}, which only the development profile applies."
    return 1
}

check_every_ingress_on_web(){
    local stray count
    count="$(rendered_ingress_count)"

    stray="$(ingresses_on_web false)"
    if [[ -z "${stray}" ]]; then
        echo "[*] ${LAYER}: all ${count} Ingresses are on the web entrypoint"
        return 0
    fi

    echo >&2 "[!] Error: with ${LAYER}, $(basename "${HTTP_VALUES}") leaves an Ingress"
    echo >&2 "    off the 'web' entrypoint, so the development profile cannot reach it:"
    printf '%s\n' "${stray}" | sed 's/^/      /' >&2
    echo >&2 ""
    echo >&2 "    Add the component's path to ${HTTP_VALUES}, mirroring how it is"
    echo >&2 "    nested in values.yaml. Note rabbit's is rabbit.ingress.http."
    return 1
}

check_global_redirect_on(){
    local redirect
    # Matched on the rendered name rather than on the values key: what makes
    # port 80 answer is the object existing, whatever turned it on.
    redirect="$(yq --raw-output "${REDIRECT_PROGRAM}" <<< "${MANIFEST}")"
    if [[ -n "${redirect}" ]]; then
        echo "[*] ${LAYER}: the global http-to-https redirect renders"
        return 0
    fi

    echo >&2 "[!] Error: with ${LAYER}, the global http-to-https redirect does not"
    echo >&2 "    render. Port 80 would answer nothing at all rather than sending"
    echo >&2 "    every visitor to https. Set globalHttpRedirect.enabled to true"
    echo >&2 "    in ${CHART_DIR}/values.yaml."
    return 1
}

check_global_redirect_off(){
    local redirect
    redirect="$(yq --raw-output "${REDIRECT_PROGRAM}" <<< "${MANIFEST}")"
    [[ -n "${redirect}" ]] || return 0

    echo >&2 "[!] Error: the global http-to-https redirect still renders with"
    echo >&2 "    ${HTTP_VALUES} applied. It matches '*.<domain>' on the web"
    echo >&2 "    entrypoint and answers ahead of every widened router, so the"
    echo >&2 "    whole values file has no visible effect. Set"
    echo >&2 "    globalHttpRedirect.enabled to false there."
    printf '%s\n' "${redirect}" | sed 's/^/      /' >&2
    return 1
}

check_traefik_dashboard(){
    # Read out of the values file rather than out of a render: the dashboard is
    # one IngressRoute in a vendored chart, and the entrypoints it is given here
    # are copied through verbatim.
    local entrypoints
    entrypoints="$(yq --raw-output \
        '[.ingressRoute.dashboard.entryPoints // [] | .[]] | join(",")' \
        "${TRAEFIK_VALUES}")"

    if [[ ",${entrypoints}," != *",web,"* ]]; then
        echo "[*] the traefik dashboard is on: ${entrypoints:-<none>}"
        return 0
    fi

    echo >&2 "[!] Error: ${TRAEFIK_VALUES} routes the Traefik dashboard on the 'web'"
    echo >&2 "    entrypoint (${entrypoints}), so it answers in cleartext on port 80"
    echo >&2 "    whatever the Loom chart renders. Leave it on websecure alone."
    return 1
}

render_layer(){
    # Renders one layering. The values files are given in skaffold's own order,
    # so the development http layer is applied last here exactly as up.sh's
    # UP_FLAG_VALUES are.
    LAYER="${1}"
    shift

    MANIFEST="$(helm template "${RELEASE}" "${CHART_DIR}" "${@}")"
}

main(){
    [[ -n "${HTTP_VALUES}" ]] || HTTP_VALUES="${CHART_DIR}/values-development-http.yaml"
    [[ -n "${DEV_VALUES}" ]] || DEV_VALUES="${CHART_DIR}/values-development.yaml"
    [[ -n "${TRAEFIK_VALUES}" ]] || TRAEFIK_VALUES="${CONTEXT_DIR}/traefik/values.yaml"

    local file
    for file in "${HTTP_VALUES}" "${DEV_VALUES}" "${TRAEFIK_VALUES}"; do
        if [[ ! -f "${file}" ]]; then
            echo >&2 "[!] Error: values file not found: ${file}"
            return 1
        fi
    done

    # Plain calls rather than `||`-collected: `set -e` takes the first failure,
    # and any one of them on its own is a stop.
    render_layer "a deployment"
    check_no_ingress_on_web
    check_global_redirect_on
    check_traefik_dashboard

    render_layer "the development profile"  --values "${HTTP_VALUES}"
    check_every_ingress_on_web
    check_global_redirect_off

    render_layer "the development profile over values-development.yaml" \
        --values "${DEV_VALUES}" --values "${HTTP_VALUES}"
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
        --dev-values)
            shift
            DEV_VALUES="${1?Missing FILE}"
            shift
        ;;
        --traefik-values)
            shift
            TRAEFIK_VALUES="${1?Missing FILE}"
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
