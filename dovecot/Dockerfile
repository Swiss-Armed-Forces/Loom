# Image version
ARG DOVECOT_IMAGE_VERSION="2.4.5"
ARG DOVECOT_IMAGE_DIGEST="sha256:c807be4fb5a97d9c3a90770569d3a6c4cbdcb36742ad41f90409cbd929166553"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/dovecot/dovecot:${DOVECOT_IMAGE_VERSION}@${DOVECOT_IMAGE_DIGEST}

COPY auth.conf dovecot.conf fts.conf storage.conf /etc/dovecot/conf.d/
