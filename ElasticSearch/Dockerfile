# Image version
ARG ELASTICSEARCH_IMAGE_VERSION="9.3.6"
ARG ELASTICSEARCH_IMAGE_DIGEST="sha256:da2c1769534f9b90ac5faa5584152a05d2972c5ffa9137fcff42b6b9d024ff84"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/elasticsearch:${ELASTICSEARCH_IMAGE_VERSION}@${ELASTICSEARCH_IMAGE_DIGEST}

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
