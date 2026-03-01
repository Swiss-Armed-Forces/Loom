# Image version
ARG PROMETHEUS_IMAGE_VERSION="v3.10.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/prom/prometheus:${PROMETHEUS_IMAGE_VERSION}

CMD ["--web.enable-admin-api", "--enable-feature=auto-gomemlimit", "--enable-feature=auto-gomaxprocs", "--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"]