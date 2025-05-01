# Image version
ARG GRAFANA_IMAGE_VERSION="10.4.3"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/grafana/grafana:${GRAFANA_IMAGE_VERSION}

COPY grafana.ini /etc/grafana/grafana.ini
COPY provisioning/ /etc/grafana/provisioning
COPY dashboards/ /var/lib/grafana/dashboards