# Image version
ARG ALPINE_IMAGE_VERSION="3.23.5"
ARG ALPINE_IMAGE_DIGEST="sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/alpine:${ALPINE_IMAGE_VERSION}@${ALPINE_IMAGE_DIGEST}

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
