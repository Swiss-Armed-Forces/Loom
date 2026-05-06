# Image version
ARG ELASTICSEARCH_IMAGE_VERSION="9.2.0"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/elasticsearch:${ELASTICSEARCH_IMAGE_VERSION}

RUN set -exu \
  && bin/elasticsearch-plugin install \
  analysis-icu \
  analysis-smartcn \
  analysis-ukrainian \
  analysis-stempel

# Remove default configurations so that we can overwrite them
# with configmaps
RUN set -exu \
  && rm -rf "/usr/share/elasticsearch/config/elasticsearch.yml"

EXPOSE 9200
EXPOSE 9300
