ARG LIBRETRANSLATE_IMAGE_VERSION="v1.6.4"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/libretranslate/libretranslate:${LIBRETRANSLATE_IMAGE_VERSION}-cuda

COPY patches/ /tmp/patches/
RUN set -exu && \
    for patch in /tmp/patches/*.patch; do [ -f "$patch" ] && patch -p1 < "${patch}"; done && \
    rm -rf /tmp/patches

RUN set -exu \
    && scripts/install_models.py

# Install GUNICORN
ARG GUNICORN_VERSION=22.0.0
RUN set -exu \
    && pip install --no-cache-dir -I "gunicorn[gevent]==${GUNICORN_VERSION}"

EXPOSE 5000

# We overwrite here ARGOS_DEVICE_TYPE which is set in the
# base image to `cuda`. This will allow running this image
# on machines without cuda installed
#
# Can be removed if the following is implemented and a new version of the image is released
# - https://github.com/LibreTranslate/LibreTranslate/issues/713
#
# Reference:
# - https://github.com/argosopentech/argos-translate/blob/master/README.md#gpu-acceleration
# - https://github.com/LibreTranslate/LibreTranslate/blob/6796e95acd2969cd1c727673a0eca7f7856e8092/docker/cuda.Dockerfile#L3C5-L3C22
ENV ARGOS_DEVICE_TYPE=auto

ENTRYPOINT ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--max-requests-jitter", "1024", "--access-logfile", "-", "--timeout", "180" ]