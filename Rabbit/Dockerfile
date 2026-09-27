# Image version
ARG RABBIT_IMAGE_VERSION="4.1.8-management-alpine"
ARG RABBIT_IMAGE_DIGEST="sha256:4631fc431a8fb41e3d7449f9a18faa13ea807793b7a5224080ff505780f8d11b"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/rabbitmq:${RABBIT_IMAGE_VERSION}@${RABBIT_IMAGE_DIGEST}

# Set a timezone
ENV TZ=UTC
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
