# Image version
ARG ALPINE_IMAGE_VERSION="3.23.4"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/alpine:${ALPINE_IMAGE_VERSION}

#
# bash
#
ARG BASH_VERSION="5.3"
RUN set -exu \
    && apk add --no-cache \
    bash~=${BASH_VERSION}
SHELL ["/bin/bash", "--login", "-c"]

#
# kubectl
#
ARG KUBECTL_VERSION="1.34"
RUN set -exu \
    && apk add --no-cache \
    kubectl~=${KUBECTL_VERSION}

#
# openssl
#
ARG OPENSSL_VERSION="3.5"
RUN set -exu \
    && apk add --no-cache \
    openssl~=${OPENSSL_VERSION}

#
# ca-certificates
#
ARG CA_CERTIFICATES_VERSION="20260611"
RUN set -exu \
    && apk add --no-cache \
    ca-certificates~=${CA_CERTIFICATES_VERSION}
