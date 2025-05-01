ARG ELASTICSEARCH_IMAGE_VERSION="8.13.4"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/elasticsearch:${ELASTICSEARCH_IMAGE_VERSION}

ARG BC_VERSION="1.07.*"

USER root:root
RUN apt-get update && apt-get install -y --no-install-recommends \
  bc=${BC_VERSION} \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Set a timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
USER elasticsearch:root

RUN bin/elasticsearch-plugin install \
  analysis-icu \
  analysis-smartcn \
  analysis-ukrainian \
  analysis-stempel

WORKDIR "/usr/share/elasticsearch"
COPY elasticsearch.yml ./config/elasticsearch.yml

EXPOSE 9200
EXPOSE 9300
