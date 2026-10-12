# Image version
ARG RABBIT_IMAGE_VERSION="4.1.8-management-alpine"
ARG RABBIT_IMAGE_DIGEST="sha256:b586ea9784425774ac56f3d4919e4f723edb3287ef8a6c4c8f0df8fe569747c3"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/rabbitmq:${RABBIT_IMAGE_VERSION}@${RABBIT_IMAGE_DIGEST}

# Set a timezone
ENV TZ=UTC
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
