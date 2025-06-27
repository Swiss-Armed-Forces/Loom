# Image version
ARG RABBIT_IMAGE_VERSION="4.1.1-management-alpine"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/rabbitmq:${RABBIT_IMAGE_VERSION}

# Set a timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq advanced.config /etc/rabbitmq/advanced.config
COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
