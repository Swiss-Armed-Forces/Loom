# Image version
ARG RABBIT_IMAGE_VERSION="3.13.7-management-alpine"

ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/rabbitmq:${RABBIT_IMAGE_VERSION}

# Set a timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY --chown=rabbitmq:rabbitmq rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY --chown=rabbitmq:rabbitmq advanced.config /etc/rabbitmq/advanced.config
COPY --chown=rabbitmq:rabbitmq enabled_plugins /etc/rabbitmq/enabled_plugins
