# Image version
ARG PROMETHEUS_IMAGE_VERSION="v2.55.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/prom/prometheus:${PROMETHEUS_IMAGE_VERSION}

COPY prometheus.yml /etc/prometheus/prometheus.yml

CMD ["--web.enable-admin-api", "--config.file=/etc/prometheus/prometheus.yml"]