# Image version
ARG ELASTICSEARCH_IMAGE_VERSION="9.3.8"
ARG ELASTICSEARCH_IMAGE_DIGEST="sha256:ec3f5c02c5a2f40078550757943979f5db5ff61222206ed2b5cf27c9db3908c2"

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
