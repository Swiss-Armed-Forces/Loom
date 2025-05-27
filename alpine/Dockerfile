# Image version
ARG ALPINE_IMAGE_VERSION="3.21.3"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/alpine:${ALPINE_IMAGE_VERSION}

#
# Bash
#
ARG BASH_VERSION="5.2.37-r0"
RUN set -exu \
    && apk add --no-cache \
    bash=${BASH_VERSION}
SHELL ["/bin/bash", "--login", "-c"]

#
# kubectl
#
ARG KUBECTL_VERSION="1.31.5-r3"
RUN set -exu \
    && apk add --no-cache \
    kubectl=${KUBECTL_VERSION}

#
# openssl
#
ARG OPENSSL_VERSION="3.3.3-r0"
RUN set -exu \
    && apk add --no-cache \
    openssl=${OPENSSL_VERSION}
