# Image version
ARG PROMETHEUS_IMAGE_VERSION="v3.11.3"
ARG PROMETHEUS_IMAGE_DIGEST="sha256:e4254400b85610324913f0dc4acf92603d9984e7519414c5a12811aa6146acc3"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/prom/prometheus:${PROMETHEUS_IMAGE_VERSION}@${PROMETHEUS_IMAGE_DIGEST}

CMD ["--web.enable-admin-api", "--enable-feature=auto-gomemlimit", "--enable-feature=auto-gomaxprocs", "--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"]
