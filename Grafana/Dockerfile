# Image version
ARG GRAFANA_IMAGE_VERSION="10.4.3"

ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/grafana/grafana:${GRAFANA_IMAGE_VERSION}

COPY grafana.ini /etc/grafana/grafana.ini
COPY provisioning/ /etc/grafana/provisioning
COPY dashboards/ /var/lib/grafana/dashboards