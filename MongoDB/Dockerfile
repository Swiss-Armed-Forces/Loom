# Image version
ARG MONGO_IMAGE_VERSION="7-jammy"

ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/mongo:${MONGO_IMAGE_VERSION}

# Set a timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 27017
