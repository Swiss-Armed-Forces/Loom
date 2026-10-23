# shellcheck shell=bash
#
# The body of `loom-chat`, the assistant pane: it waits for Ollama, reports
# what it is waiting on, and then runs opencode against a configuration
# seeded from the store on every start. nixos/console.nix reads this file
# into the writeShellApplication of the same name, behind a prologue of
# `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to. At three hundred and sixty lines this was the largest string in
# the tree that nothing checked.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

model="${LOOM_CHAT_MODEL:?nixos/console.nix must set this}"
endpoint="${LOOM_OLLAMA_ENDPOINT:?nixos/console.nix must set this}"
# Ollama's root route, which answers "Ollama is running" and nothing else.
# What the wait below gates on -- see `ready`.
probe="${LOOM_OLLAMA_PROBE:?nixos/console.nix must set this}"
# Ollama's native routes, which the OpenAI-compatible /v1 does not mirror:
# /api/ps and /api/show are where the context size is readable at all.
#
# Built from `ollamaBaseUrl` like the two above, not hardcoded to the
# ingress: on a --require-client-cert box mtls.nix sets that option to
# `http://127.0.0.1:18080` precisely because Traefik there demands a client
# certificate this pane cannot present, and the loopback proxy forwards
# `locations."/"` so /api/ps and /api/show work through it unchanged. Hard-
# coded, both curls failed on every mTLS box, `context_length` returned 1,
# the jq patch never ran, and the model kept `limit.context = 0` -- which
# is the state the comment further down says turns compaction off and gets
# long sessions silently truncated by Ollama. The option's own description
# says a box behind its own mutual TLS "has to move both at once"; there
# are three readers, not two.
api="${LOOM_OLLAMA_API:?nixos/console.nix must set this}"
namespace="${LOOM_NAMESPACE:?nixos/console.nix must set this}"

# Both are runtime flags (packages/core/src/flag/flag.ts), and neither is
# set by the binary's wrapper: nixpkgs bakes models.dev's catalogue into the
# closure and sets OPENCODE_DISABLE_MODELS_FETCH while *building*, which
# does nothing for the process the operator runs.
#
# Not a hang fix -- measured, opencode falls back to the baked-in catalogue
# in about two seconds when the network is simply absent. It is a policy:
# this box makes no outbound connection it was not asked to make, and
# "fails fast" depends on how the failure arrives. A refused route answers
# immediately; a silently dropped packet does not, and the appliance's own
# dnsmasq plus whatever the site does upstream is exactly the shape where
# that difference shows up.
export OPENCODE_DISABLE_MODELS_FETCH=1
export OPENCODE_DISABLE_AUTOUPDATE=1

# What the assistant is allowed to learn about itself from, which on this
# box has to be only what the image shipped.
#
# opencode discovers skills from `.claude/skills` and `.agents/skills`, in
# $HOME and in every directory from its working directory up to the
# worktree root. Both are writable here -- $HOME is the operator's, and the
# working directory is the seeded checkout -- so without this the set of
# skills depends on what happens to be lying around rather than on what was
# built. `OPENCODE_DISABLE_EXTERNAL_SKILLS` is the one that covers it:
# `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` drops only `.claude` and leaves
# `.agents` scanned, which reads like the right flag and is not.
export OPENCODE_DISABLE_EXTERNAL_SKILLS=1

# The same walk, for instruction files: AGENTS.md, then CLAUDE.md. There is
# no AGENTS.md in the checkout, so the fallback hits the repository's own
# CLAUDE.md -- 500-odd lines about git worktrees, GitLab merge requests and
# poetry lockfiles, prepended to every question an operator asks a box that
# has no git remote and no devenv. `instructions` in the config above is
# what this pane is told instead.
export OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1

# Sessions, logs and caches land on tmpfs, not on the encrypted root. This
# appliance is built for ephemeral, task-specific deployments, and the
# transcript of what an operator asked about an evidence set is not
# something to leave on the disk by accident. /run/loom is created by the
# tmpfiles rule below and is 0700 loom.
state="${LOOM_OPENCODE_STATE:?nixos/console.nix must set this}"
mkdir -p "${state}"
export XDG_DATA_HOME="${state}/data"
export XDG_STATE_HOME="${state}/state"
export XDG_CACHE_HOME="${state}/cache"

# opencode writes inside its own config directory while it starts -- a
# `.gitignore`, and `opencode.json` itself -- so that directory is a
# writable copy on the tmpfs above rather than the store path that holds
# the pinned configuration. Pointed at a read-only one, every startup
# request that reaches `Config.get` -- `config.providers`, `provider.list`,
# `app.agents`, `config.get` -- fails with EROFS and the pane exits before
# it draws a prompt.
#
# Re-seeded on each start rather than created once: the store copy is what
# pins the model and the provider, so restarting the pane is also the way
# back to a known configuration.
#
# Both variables, because they answer different questions.
# `OPENCODE_CONFIG` names the server config outright, which is what pins
# the model and the provider; `OPENCODE_CONFIG_DIR` puts that same
# directory on the search path, which is the only way `tui.json` beside it
# is ever read. Setting just the first leaves the pane on opencode's own
# theme.
config="${state}/config"
rm --recursive --force "${config}"
mkdir -p "${config}"
# `/.` rather than `/*`, and recursive, because the glob form has three
# ways to go wrong and all of them are silent: it cannot carry a
# subdirectory, it skips dotfiles, and on an empty source it passes a
# literal `*` that fails the copy under `set -e`. Nothing in
# opencodeConfigDir needs any of that today -- the point is that the next
# file added there must not have to notice.
cp --recursive --no-preserve=mode "${LOOM_OPENCODE_CONFIG_DIR:?nixos/console.nix must set this}/." "${config}/"
export OPENCODE_CONFIG="${config}/opencode.json"
export OPENCODE_CONFIG_DIR="${config}"

printf '  Loom assistant on %s.\n' "${model}"

# The ingress serves a cert-manager certificate from a selfSigned issuer,
# so the chain ends at a root nothing has heard of and Bun refuses it with
# "unable to verify the first certificate". Trust it explicitly rather than
# switching verification off: NODE_TLS_REJECT_UNAUTHORIZED=0 would disable
# it for every connection the process makes, not just this one.
#
# Read through the API rather than off the wire: pulling the chain from the
# server and then trusting it would verify nothing at all.
#
# Two secrets, because which one Traefik presents depends on how the chart
# was deployed, and a bundle costs nothing:
#
# Trusting the certificate is only half of it: it also has to name the
# host. The chart's Job puts every `*.loom` host in the subjectAltName one
# by one, because a wildcard cannot do it -- `*.loom` has one dot, and
# OpenSSL (so also Bun, and curl in `ready` below) will not expand a
# wildcard under a single-label parent. A release whose chart predates
# `hostnames` in charts/values.yaml serves a certificate that cannot
# verify no matter what is in this bundle, and `ready` says so.
#
#   self-signed-cert  The `CN=*.loom` certificate that
#                     charts/templates/pre-install/generate-self-signed-certificate.yaml
#                     makes with `openssl req -x509` on every install, and
#                     that traefik/tls-store.yaml sets as the DEFAULT
#                     certificate. This is what actually answers on a stock
#                     box, because charts/values.yaml has
#                     `certificate.enabled: false`.
#   <release>-certificate  cert-manager's, named by the Ingress, and
#                     present only when that value is turned on.
#
# Both are tried for `ca.crt` first and `tls.crt` second: a `kubectl create
# secret tls` secret -- which is how the pre-install Job stores its cert --
# has no `ca.crt` at all. Trusting the leaf is right here rather than a
# fudge: nothing issued that certificate, it signs itself, and it is the
# only anchor there is to trust.
#
# What that costs the chart is one line it must not have. A verifier
# handed a certificate to use as an anchor asks whether it was allowed to
# sign anything, so a critical `keyUsage` without `keyCertSign` bars it
# from the job. Bun's BoringSSL enforces that and fails the first request
# with "unable to verify the first certificate"; OpenSSL (so curl in
# `ready` below) and Go accept the certificate anyway, which is why such a
# box looks healthy right up to the point where this pane answers. So the
# Job emits no keyUsage and the cert-manager Certificate names `cert sign`
# -- see the comments in charts/files/pre-install/ and
# charts/templates/common/certificate.yaml. Releases that get this wrong
# (1.4.0-rc4 is the one) need their `self-signed-cert` secret replaced by
# hand.
ca="${state}/ollama-ca.crt"
append_cert() {
  local secret key pem
  secret="$1"
  [[ -n "${secret}" ]] || return 0
  for key in 'ca\.crt' 'tls\.crt'; do
    pem="$(kubectl --request-timeout=5s --namespace "${namespace}" \
      get secret "${secret}" --output "jsonpath={.data.${key}}" 2>/dev/null \
      | base64 --decode 2>/dev/null)" || continue
    case "${pem}" in
      *"BEGIN CERTIFICATE"*)
        printf '%s\n' "${pem}" >> "${ca}.tmp"
        return 0
        ;;
      *) ;;
    esac
  done
  return 0
}

fetch_ca() {
  : > "${ca}.tmp"
  append_cert self-signed-cert
  append_cert "$(kubectl --request-timeout=5s --namespace "${namespace}" \
    get ingress --selector app.kubernetes.io/component=ollama \
    --output jsonpath='{.items[0].spec.tls[0].secretName}' 2>/dev/null || true)"
  # An empty bundle would make every request fail with a less obvious error
  # than the one this exists to fix, so only publish something that has at
  # least one certificate in it.
  grep --fixed-strings "BEGIN CERTIFICATE" "${ca}.tmp" >/dev/null || return 1
  mv "${ca}.tmp" "${ca}"
}

# Same shape, and the same reason, as loom-k9s's wait: this pane can start
# long before the cluster answers. `ollama.loom` is pinned in /etc/hosts
# from the first boot (box.nix), so a premature start does not fail fast
# with NXDOMAIN -- it hangs against a Traefik that is not listening yet, and
# a pane that prints nothing reads as frozen.
#
# What this waits for is that Ollama answers over a connection that
# verifies, and nothing more. Whether the pinned model is in its inventory
# used to be part of the same condition, on the grounds that opencode exits
# when its first request fails -- but a model that never arrives is then a
# pane that waits forever and says only that it is waiting, which is a
# worse failure than the one it was avoiding. A missing model is now a
# warning below and opencode's own error afterwards: the pane is
# `remain-on-exit` and supervised by loom-pane, so that error stays on
# screen, comes back on a backoff and offers "× restart pane".
#
# Said once per change rather than once per attempt, so a pane that waits
# an hour for a bring-up does not scroll one line every five seconds.
wait_reason=""
note() {
  if [[ "$1" != "${wait_reason}" ]]; then
    wait_reason="$1"
    printf '  %s\n' "$1"
  fi
}

# The halves are checked separately and named separately. Folded into one
# predicate they produce the same silence for "the cluster has not issued
# its certificate yet", "nothing is listening on 443 yet" and "the name
# resolves to something that is not Ollama", which are fixed by different
# things.
#
# curl's own message is carried into the wait line rather than dropped.
# This is the whole reason that was worth changing: --silent without
# --show-error, plus a discarded body, meant one line stood for a cert that
# does not verify, a route that 404s and a model that is not there, and an
# operator looking at the pane could not tell which. `2>&1 >"$body"`
# duplicates stderr onto the substitution's pipe *before* stdout goes to
# the file, so the status is curl's and the message is curl's.
#
# The body is matched too, and not only for tidiness: the appliance answers
# wildcard *.loom from its own dnsmasq (network.nix), so a misrouted name
# lands on some other Loom service that is only too happy to return 200 on
# `/`. --fail catches Traefik's 404 for a host it does not route; it cannot
# catch that.
ready() {
  local err body
  if ! fetch_ca; then
    note "Waiting for the cluster's TLS certificate."
    return 1
  fi
  body="${state}/ollama-probe"
  if ! err="$(curl --silent --show-error --fail --max-time 5 \
    --cacert "${ca}" "${probe}" 2>&1 >"${body}")"; then
    # Folded onto one line: curl's cert diagnostics run to several, and
    # this is a status line in a pane, not a report.
    note "Waiting for Ollama at ${probe}: ${err//$'\n'/ }"
    return 1
  fi
  if ! grep --fixed-strings "Ollama is running" "${body}" >/dev/null; then
    note "Waiting for Ollama at ${probe}: something else answered."
    return 1
  fi
  return 0
}

until ready; do
  sleep 5
done

# Said once, and not waited on. An air-gapped box only has the models
# ollama/Dockerfile.models baked in, and the one thing that cannot be fixed from
# this pane is a model that is not on the box -- so name it here, where the
# operator is already looking, rather than let opencode's first failure be
# the only clue. /api/ps is what the chart probes, and it answers 200 on an
# empty model store, so a Ready ollama pod proves nothing about this.
#
# `grep` without -q, deliberately -- this one is a pipeline, unlike the
# probe above: the script runs under `set -o pipefail`, and -q makes grep
# exit on the first match, which hands the producer on its left an EPIPE
# and fails the pipeline *because* the match was found. The same trap is
# documented at length in tests/appliance.nix.
if ! curl --silent --fail --max-time 5 --cacert "${ca}" "${endpoint}/models" \
  | grep --fixed-strings "${model}" >/dev/null; then
  printf '  Warning: Ollama does not list %s.\n' "${model}"
  printf '  Starting anyway; the first question will fail until it does.\n'
  printf '  What is on the box: ollama list, in the ollama pod.\n'
fi

# How big the context is, asked rather than written down.
#
# Not cosmetics. A model whose `limit.context` is 0 -- which is what a
# provider invented by this file resolves to, there being no catalogue
# entry for it -- turns opencode's automatic compaction OFF: the check
# begins `if (model.limit.context === 0) return false`. So the pane has
# been running without it, and a long session does not get summarised, it
# gets silently truncated by Ollama at the far end. The readout is the
# visible half of the same fact: "N tokens" with no percentage in the
# session bar, and the sidebar block that used to say `0% used`.
#
# It cannot be a constant. Ollama sizes the context from the VRAM it
# measures -- ollama/ollama_wrapper.py mirrors the ladder, 256k above 47
# GiB, 32k above 23 GiB, 4096 below -- capped by what the model was trained
# on, and one image serves platforms with different GPUs. A number written
# down here would be wrong on a box that fell to a lower tier, and wrong in
# the direction that matters: it would claim headroom that is not there,
# hold off compaction past the real window, and the operator would find out
# by having the conversation truncated anyway.
#
# /api/ps first, because that is the window the running model actually has.
# It is empty until something has been asked, so /api/show is the fallback:
# the trained length, which is what Ollama serves whenever the tier is not
# the binding constraint. The key there is architecture-prefixed
# (`qwen3.context_length`), hence the suffix match rather than a name.
#
# Nothing is written when neither answers, which leaves the pane exactly as
# it was. A missing limit is a bare token count: honest, if worse.
context_length() {
  local body value
  if body="$(curl --silent --fail --max-time 5 --cacert "${ca}" \
    "${api}/ps" 2>/dev/null)"; then
    if value="$(jq --exit-status \
      '[.models[]?.context_length // 0] | max // 0 | select(. > 0)' \
      <<<"${body}" 2>/dev/null)"; then
      printf '%s\n' "${value}"
      return 0
    fi
  fi
  if body="$(curl --silent --fail --max-time 5 --cacert "${ca}" \
    --json "$(jq --null-input --arg model "${model}" '{model: $model}')" \
    "${api}/show" 2>/dev/null)"; then
    if value="$(jq --exit-status \
      '[(.model_info // {}) | to_entries[]
        | select(.key | endswith(".context_length")) | .value]
        | first | select(type == "number" and . > 0)' \
      <<<"${body}" 2>/dev/null)"; then
      printf '%s\n' "${value}"
      return 0
    fi
  fi
  return 1
}

if context="$(context_length)"; then
  # `output` is required beside `context` by opencode's schema and is not
  # a thing Ollama reports -- a local model has no output cap of its own,
  # `num_predict` runs until the window is full. It still has to be chosen
  # rather than left large, because it is what compaction reserves:
  # the trigger is `context - min(20000, output)`, so output == context
  # would compact on the first message. A cap of 8192, and never more than
  # a quarter of the window so the 4096-token tier keeps room to answer in.
  output="$((context / 4))"
  if [[ "${output}" -gt 8192 ]]; then
    output=8192
  fi
  # Patched into the tmpfs copy, which is re-seeded from the store on every
  # start -- so this is re-asked each time rather than remembered, and a box
  # whose Ollama came back on a different tier is not left describing the
  # old one.
  tmp="${config}/opencode.json.tmp"
  jq --arg model "${model}" --argjson context "${context}" \
    --argjson output "${output}" \
    '.provider.ollama.models[$model].limit =
        { context: $context, output: $output }' \
    "${OPENCODE_CONFIG}" >"${tmp}"
  mv "${tmp}" "${OPENCODE_CONFIG}"
  printf '  Context window: %s tokens.\n' "${context}"
fi

# Bun honours this the same way Node does -- measured against a self-signed
# server: the fetch fails with "self signed certificate" without it and
# succeeds with it.
export NODE_EXTRA_CA_CERTS="${ca}"

exec opencode
