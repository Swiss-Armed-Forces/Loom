#!/bin/sh

#source vars if file exists
DEFAULT=/etc/default/fluentd
FLUENTD_CONF=${FLUENTD_CONF?Missing FLUENTD_CONF}

if [ -r "${DEFAULT}" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    . "${DEFAULT}"
    set +o allexport
fi

# If the user has supplied only arguments append them to `fluentd` command
if [ "${1#-}" != "$1" ]; then
    set -- fluentd "$@"
fi

# If user does not supply config file or plugins, use the default
if [ "$1" = "fluentd" ]; then
    if ! echo "$@" | grep -e ' \-c' -e ' \-\-config' ; then
       set -- "$@" --config "/fluentd/etc/${FLUENTD_CONF}"
    fi

    if ! echo "$@" | grep -e ' \-p' -e ' \-\-plugin' ; then
       set -- "$@" --plugin /fluentd/plugins
    fi
fi

exec "$@"
