# Image version
ARG GRAFANA_IMAGE_VERSION="13.1.6"
ARG GRAFANA_IMAGE_DIGEST="sha256:d8276d620291d3aaae3e31dde6d63e6807afee49825f04e8aa7392bbe024216f"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/grafana/grafana:${GRAFANA_IMAGE_VERSION}@${GRAFANA_IMAGE_DIGEST}

# The bundled elasticsearch plugin directory is read-only (image layer), so
# Grafana's background installer cannot update it and the plugin fails to load.
# Copying to the writable plugins directory avoids the crash.
RUN set -exu \
  && cp -r /usr/share/grafana/data/plugins-bundled/elasticsearch /var/lib/grafana/plugins/elasticsearch

COPY grafana.ini /etc/grafana/grafana.ini
COPY provisioning/ /etc/grafana/provisioning
COPY dashboards/ /var/lib/grafana/dashboards
