#!/usr/bin/env bash
# shellcheck disable=SC2034
set -eou pipefail

# Minimum resources required to deploy Loom.
# See README.md "Minimum Deployment Resources".
LOOM_MIN_CPU="8"
LOOM_MIN_MEMORY="25Gi"
LOOM_MIN_GPU="3"

TRAEFIK_HELM_VERSION="39.0.9"
TRAEFIK_IMAGE_VERSION="v3.6.15"

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
    "flower"
    "rspamd"
    "rspamd-worker"
    "rabbit-amqp"
    "tika"
    "translate"
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
