# Image version
ARG RABBIT_IMAGE_VERSION="4.1.8-management-alpine"
ARG RABBIT_IMAGE_DIGEST="sha256:9cee09b738ad0a9ff1b5bca1883313b745ddfe9b24528d398ca489c34b0feb55"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/rabbitmq:${RABBIT_IMAGE_VERSION}@${RABBIT_IMAGE_DIGEST}

# Set a timezone
ENV TZ=UTC
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
