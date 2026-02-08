#!/usr/bin/env bash
# shellcheck disable=SC2034
set -eou pipefail

TRAEFIK_HELM_VERSION="36.0.0"
TRAEFIK_IMAGE_VERSION="v3.4.1"

LOOM_HOSTS=(
    "rabbit"
    "frontend"
    "api"
    "traefik"
    "mongo-web"
    "elasticvue"
    "elasticsearch"
    "redisinsight"
    "redis"
    "flower"
    "rspamd"
    "rspamd-worker"
    "rabbit-amqp"
    "tika"
    "translate"
    "mongodb"
    "prometheus"
    "grafana"
    "open-webui"
    "ollama"
    "ollama-tool"
    "dovecot"
    "roundcube"
    "minio"
    "minio-api"
    "gotenberg"
)
LOOM_DOMAIN="loom"


LOOM_HOSTS_FQDN=()
for h in "${LOOM_HOSTS[@]}"; do
    LOOM_HOSTS_FQDN+=("${h}.${LOOM_DOMAIN}")
done
