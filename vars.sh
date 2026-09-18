#!/usr/bin/env bash
# shellcheck disable=SC2034
set -eou pipefail

# Minimum resources required to deploy Loom.
# See README.md "Minimum Deployment Resources".
LOOM_MIN_CPU="8"
LOOM_MIN_MEMORY="25Gi"
LOOM_MIN_GPU="1"

TRAEFIK_HELM_VERSION="39.0.9"
TRAEFIK_IMAGE_VERSION="v3.6.15"

KEDA_HELM_VERSION="2.20.1"
KEDA_IMAGE_VERSION="2.20.1"

NAMESPACE="loom"

# The chat model the appliance console pins itself to (nixos/console.nix's
# loom-chat, via cicd/build_appliance_image.sh). Not a free choice: an
# air-gapped box only ever has the models baked into the ollama image, and the
# production target of ollama/Dockerfile pulls exactly this one plus the
# embedding model. Pointing the console at anything else gives a pane that
# cannot answer.
#
# Naming a model the workers do not use would also be wrong even if it were
# present -- ollama would load a second model and evict the one mid-index. So
# this tracks `_llmDefaults.model` in charts/values.yaml, and the appliance test
# asserts the value that reaches the image.
LOOM_CHAT_MODEL="huihui_ai/qwen3.5-abliterated:9b"

LOOM_HOSTS=(
    "rabbit"
    "frontend"
    "api"
    "traefik"
    "elasticvue"
    "elasticsearch"
    "redisinsight"
    "redis"
    "redis-cache"
    "rspamd"
    "rspamd-worker"
    "rabbit-amqp"
    "tika"
    "prometheus"
    "grafana"
    "open-webui"
    "ollama"
    "dovecot"
    "roundcube"
    "seaweedfs"
    "s3"
    "gotenberg"
)
LOOM_DOMAIN="loom"

LOOM_HOSTS_FQDN=()
for h in "${LOOM_HOSTS[@]}"; do
    LOOM_HOSTS_FQDN+=("${h}.${LOOM_DOMAIN}")
done
