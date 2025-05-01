# Image version
ARG FLUENTD_IMAGE_VERSION="v1.17.0-1.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/fluent/fluentd:${FLUENTD_IMAGE_VERSION}

USER root

# Package versions
ARG BUILD_BASE_VERSION="0.5-r3"
ARG RUBY_DEV_VERSION="3.2.8-r0"
ARG FLUENT_PLUGIN_ELASTICSEARCH_VERSION="5.4.3"

RUN set -exu \
    && apk add --no-cache --virtual .build-deps \
    build-base=${BUILD_BASE_VERSION} \
    ruby-dev=${RUBY_DEV_VERSION} \
    # customize following instruction as you wish
    && gem install fluent-plugin-elasticsearch:${FLUENT_PLUGIN_ELASTICSEARCH_VERSION} \
    && gem sources --clear-all \
    && apk del .build-deps \
    && rm -rf /home/fluent/.gem/ruby/2.5.0/cache/*.gem

COPY fluent.conf /fluentd/etc/
COPY index-templates /fluentd/etc/index-templates
COPY entrypoint.sh /bin/

USER fluent
