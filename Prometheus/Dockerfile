# Image version
ARG PROMETHEUS_IMAGE_VERSION="v2.55.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/prom/prometheus:${PROMETHEUS_IMAGE_VERSION}

CMD ["--web.enable-admin-api", "--auto-gomemlimit", "--auto-gomaxprocs", "--config.file=/etc/prometheus/prometheus.yml"]