ARG LIBRETRANSLATE_IMAGE_VERSION="v1.7.2"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/libretranslate/libretranslate:${LIBRETRANSLATE_IMAGE_VERSION}-cuda

COPY patches/ /tmp/patches/
RUN set -exu && \
    for patch in /tmp/patches/*.patch; do \
    if [ -f "${patch}" ]; then \
    patch -p1 < "${patch}"; \
    fi \
    done && \
    rm -rf /tmp/patches

RUN set -exu \
    && scripts/install_models.py

# Install GUNICORN
ARG GUNICORN_VERSION=23.0.0
RUN set -exu \
    && pip install --no-cache-dir -I "gunicorn[gevent]==${GUNICORN_VERSION}"

EXPOSE 5000

ENTRYPOINT ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--max-requests", "50", "--max-requests-jitter", "10", "--access-logfile", "-", "--timeout", "180" ]
