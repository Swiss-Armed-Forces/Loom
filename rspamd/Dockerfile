# Image version
ARG ALPINE_IMAGE_VERSION="3.20"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/alpine:${ALPINE_IMAGE_VERSION}

# Package versions
ARG RSPAMD_VERSION="3.8.4-r0"

RUN set -exu && apk add --no-cache rspamd=${RSPAMD_VERSION}

RUN set -exu \
    && echo "bind_socket = \"0.0.0.0:11333\";" >> /etc/rspamd/local.d/worker-normal.inc \
    && echo "bind_socket = \"0.0.0.0:11334\";" >> /etc/rspamd/local.d/worker-controller.inc \
    && echo "secure_ip = \"0.0.0.0/0\";" >> /etc/rspamd/local.d/worker-controller.inc \
    && echo "hostname_enabled = false;" >> /etc/rspamd/local.d/hfilter.conf

RUN set -exu && chown -R rspamd:rspamd /etc/rspamd/local.d

USER rspamd
EXPOSE 11333 11334
ENTRYPOINT ["rspamd", "--no-fork"]
