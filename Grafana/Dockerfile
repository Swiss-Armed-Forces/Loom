# Image version
ARG GRAFANA_IMAGE_VERSION="13.1.7"
ARG GRAFANA_IMAGE_DIGEST="sha256:248cda1de5bc3e69c3fb23c5efe1292aa18399d8ece499aa88cab6fd16f78d4b"

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
