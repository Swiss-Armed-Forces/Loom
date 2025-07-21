# Image version
ARG MONGO_IMAGE_VERSION="7-jammy"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/mongo:${MONGO_IMAGE_VERSION}

# Set a timezone
ENV TZ=UTC
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

EXPOSE 27017
