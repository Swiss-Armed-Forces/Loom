# Image version
ARG DOVECOT_IMAGE_VERSION="2.4.5"
ARG DOVECOT_IMAGE_DIGEST="sha256:43c14def08a57f25107593cbcf64a0a6fbae84a7b9de7aa038513c9b21e91914"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/dovecot/dovecot:${DOVECOT_IMAGE_VERSION}@${DOVECOT_IMAGE_DIGEST}

COPY auth.conf dovecot.conf fts.conf storage.conf /etc/dovecot/conf.d/
