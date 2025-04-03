#!/usr/bin/env bash
# shellcheck disable=SC2034
set -eou pipefail

TRAEFIK_HELM_VERSION="33.2.1"
TRAEFIK_IMAGE_VERSION="v3.3.2"

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
    "dovecot"
    "roundcube"
    "minio"
    "minio-api"
)
LOOM_DOMAIN="loom"


LOOM_HOSTS_FQDN=()
for h in "${LOOM_HOSTS[@]}"; do
    LOOM_HOSTS_FQDN+=("${h}.${LOOM_DOMAIN}")
done
