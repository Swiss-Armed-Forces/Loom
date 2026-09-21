#!/usr/bin/env bash
#
# Asserts that `hostnames.ingress` in charts/values.yaml is exactly the set of
# hosts the chart's Ingress rules render.
#
# The Ingress rules are the authority: `spec.rules[].host` is what Traefik
# actually routes, and it is written per template. The list in values.yaml is a
# restatement, and it exists only because a Helm template cannot read what its
# siblings rendered -- the pre-install Job that generates the TLS certificate
# has to name every host in a subjectAltName, and it has no way to enumerate
# them. This script is what keeps the restatement honest.
#
# `hostnames.extra` is deliberately not checked against anything: those hosts
# have no Ingress rule to compare with. Their routes match HostSNI(`*`) and are
# told apart by entrypoint, so nothing in the chart implies the name.
#
# Runs `helm template`, which is client-side -- no cluster, no network.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${CONTEXT_DIR}/charts"
RELEASE="loom"
# Read off the chart in main, so --chart is honoured.
DOMAIN=""

usage(){
    cat <<EOF
Usage: $(basename "${0}") [OPTIONS]

Compares charts/values.yaml's hostnames.ingress with the hosts the chart's
Ingress rules render.

OPTIONS:
  --chart DIR   chart to check (default: ${CHART_DIR})
  -h|--help     show this help
EOF
}

# The wildcard host of the http-to-https redirect Ingress. A pattern rather than
# a name, and there is no `*` entry in values.yaml to match it, so it is dropped
# from both sides of the comparison.
rendered_hosts(){
    helm template "${RELEASE}" "${CHART_DIR}" \
        | grep --extended-regexp '^[[:space:]]*- host:' \
        | sed 's/.*host:[[:space:]]*//; s/"//g' \
        | grep --invert-match '^\*\.' \
        | sed "s/\.${DOMAIN}\$//" \
        | sort --unique
}

declared_hosts(){
    # Read straight out of values.yaml rather than through a rendered template:
    # what is being checked is the declaration itself, and a template that
    # reformatted it would hide a mistake in it.
    python3 -c '
import sys, yaml
values = yaml.safe_load(open(sys.argv[1]))
for name in sorted(set(values["hostnames"]["ingress"])):
    print(name)
' "${CHART_DIR}/values.yaml"
}

main(){
    DOMAIN="$(python3 -c '
import sys, yaml
print(yaml.safe_load(open(sys.argv[1]))["domain"])
' "${CHART_DIR}/values.yaml")"

    local rendered declared
    rendered="$(rendered_hosts)"
    declared="$(declared_hosts)"

    if [[ "${rendered}" == "${declared}" ]]; then
        local count
        count="$(wc -l <<< "${rendered}")"
        echo "[*] hostnames.ingress matches the chart's ${count} Ingress hosts"
        return 0
    fi

    echo >&2 "[!] Error: hostnames.ingress in charts/values.yaml does not match the"
    echo >&2 "    hosts the chart's Ingress rules render."
    echo >&2 ""
    echo >&2 "    Missing from values.yaml (an Ingress serves it, the certificate"
    echo >&2 "    would not cover it):"
    comm -23 <(printf '%s\n' "${rendered}") <(printf '%s\n' "${declared}") \
        | sed 's/^/      /' >&2
    echo >&2 ""
    echo >&2 "    In values.yaml with no Ingress rule (move it to hostnames.extra"
    echo >&2 "    if it is served by entrypoint instead):"
    comm -13 <(printf '%s\n' "${rendered}") <(printf '%s\n' "${declared}") \
        | sed 's/^/      /' >&2
    return 1
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
            usage
            exit 1
        ;;
    esac
done

main
