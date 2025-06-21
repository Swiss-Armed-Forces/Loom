# Image version
ARG FLUENTD_IMAGE_VERSION="v1.17.0-1.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/fluent/fluentd:${FLUENTD_IMAGE_VERSION}

USER root

# Package versions
ARG BUILD_BASE_VERSION="0.5-r3"
ARG RUBY_DEV_VERSION="3.2.8-r0"
ARG FLUENT_PLUGIN_ELASTICSEARCH_VERSION="6.0.0"
# Fix for Fluentd Elasticsearch compatibility issue:
# The fluent-plugin-elasticsearch .gemspec doesn't pin the elasticsearch Ruby gem version,
# which can cause version 9.x to be installed automatically. This creates compatibility
# issues with Elasticsearch 8.x clusters that only accept Content-Type versions 7 or 8.
# Solution: Explicitly install a compatible elasticsearch gem version before the plugin.
# Working versions: elasticsearch (8.18.0), fluent-plugin-elasticsearch (5.4.3)
#
# see:
#  - https://github.com/uken/fluent-plugin-elasticsearch/issues/1061#issuecomment-2912230835
ARG ELASTICSEARCH_GEM_VERSION="8.18.0"

RUN set -exu \
    && apk add --no-cache --virtual .build-deps \
    build-base=${BUILD_BASE_VERSION} \
    ruby-dev=${RUBY_DEV_VERSION} \
    # Installing elasticsearch here is a workaround for a known issue.
    # See comment on ELASTICSEARCH_GEM_VERSION. This also has to be installed
    # before come fluent-plugin-elasticsearch
    && fluent-gem install elasticsearch:${ELASTICSEARCH_GEM_VERSION} \
    && fluent-gem install fluent-plugin-elasticsearch:${FLUENT_PLUGIN_ELASTICSEARCH_VERSION} \
    && gem sources --clear-all \
    && apk del .build-deps \
    && rm -rf /home/fluent/.gem/ruby/2.5.0/cache/*.gem

COPY fluent.conf /fluentd/etc/
COPY index-templates /fluentd/etc/index-templates
COPY entrypoint.sh /bin/

USER fluent
