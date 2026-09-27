# Image version
ARG ROUNDCUBE_IMAGE_VERSION="1.6.19-apache"
ARG ROUNDCUBE_IMAGE_DIGEST="sha256:f1256d1ce06ca5c52660f67f8511f3971def5d3b80aab3e3809df970489b1c46"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/roundcube/roundcubemail:${ROUNDCUBE_IMAGE_VERSION}@${ROUNDCUBE_IMAGE_DIGEST}


ENV ROUNDCUBEMAIL_SKIN=elastic
COPY config.inc.php /var/roundcube/config/config.inc.php

COPY plugins/alwayslogon/ /var/www/html/plugins/alwayslogon
ENV \
    ROUNDCUBEMAIL_COMPOSER_PLUGINS=johndoh/contextmenu,germancoding/tls_icon \
    ROUNDCUBEMAIL_PLUGINS=archive,zipdownload,alwayslogon,contextmenu,tls_icon

# Run entrypoint here for: roundcube installation,
# skin downloading, plugin installation, ...
# This is because we want to make this template work
# in full offline mode.
RUN set -exu \
    && /docker-entrypoint.sh bin/gc.sh

ENTRYPOINT ["apache2-foreground"]
