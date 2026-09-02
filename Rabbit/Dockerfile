# Image version
ARG RABBIT_IMAGE_VERSION="4.1.8-management-alpine"
ARG RABBIT_IMAGE_DIGEST="sha256:f81b0dc2f3810f01d5968f6e5ed7cd22864a49481f92691cb7fdf532c31d6eec"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/rabbitmq:${RABBIT_IMAGE_VERSION}@${RABBIT_IMAGE_DIGEST}

# Set a timezone
ENV TZ=UTC
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
