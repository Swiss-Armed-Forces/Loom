ARG ELASTICSEARCH_IMAGE_VERSION="9.0.2"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/elasticsearch:${ELASTICSEARCH_IMAGE_VERSION}

RUN set -exu && \
  bin/elasticsearch-plugin install \
  analysis-icu \
  analysis-smartcn \
  analysis-ukrainian \
  analysis-stempel

WORKDIR "/usr/share/elasticsearch"
COPY elasticsearch.yml ./config/elasticsearch.yml

EXPOSE 9200
EXPOSE 9300
