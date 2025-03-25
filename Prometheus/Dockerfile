ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/prom/prometheus:v2.55.0

COPY prometheus.yml /etc/prometheus/prometheus.yml

CMD ["--web.enable-admin-api", "--config.file=/etc/prometheus/prometheus.yml"]