# Image version
ARG ROUNDCUBE_IMAGE_VERSION="1.6.9-apache"

ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/roundcube/roundcubemail:${ROUNDCUBE_IMAGE_VERSION}


ENV ROUNDCUBEMAIL_SKIN=elastic
COPY config.inc.php /var/roundcube/config/config.inc.php

COPY plugins/alwayslogon/ /var/www/html/plugins/alwayslogon
ENV ROUNDCUBEMAIL_PLUGINS=archive,zipdownload,subscriptions_option,alwayslogon

# Run entrypoint here for: roundcube installation,
# skin downloading, plugin installation, ...
# This is because we want to make this template work
# in full offline mode.
RUN set -exu \
    && /docker-entrypoint.sh bin/gc.sh

ENTRYPOINT ["apache2-foreground"]