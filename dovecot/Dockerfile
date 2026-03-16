# Image version
ARG DOVECOT_IMAGE_VERSION="2.3.21.1"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/dovecot/dovecot:${DOVECOT_IMAGE_VERSION}

COPY auth.conf dovecot.conf /etc/dovecot/conf.d/