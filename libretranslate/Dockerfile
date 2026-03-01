ARG LIBRETRANSLATE_IMAGE_VERSION="v1.9.4"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/libretranslate/libretranslate:${LIBRETRANSLATE_IMAGE_VERSION}-cuda

COPY patches/ /tmp/patches/
RUN set -exu \
    && for patch in /tmp/patches/*.patch; do \
    if [ -f "${patch}" ]; then \
    patch -p1 < "${patch}"; \
    fi \
    done && \
    rm -rf /tmp/patches

RUN set -exu \
    && scripts/install_models.py

# Set up /metrics data dir
ENV PROMETHEUS_MULTIPROC_DIR="db/prometheus"
RUN set -exu \
    && mkdir -p "${PROMETHEUS_MULTIPROC_DIR}"

# Install GUNICORN
ARG GUNICORN_VERSION=23.0.0
RUN set -exu \
    && pip install --no-cache-dir -I "gunicorn[gevent]==${GUNICORN_VERSION}"

EXPOSE 5000

ENTRYPOINT ["gunicorn", "-c", "scripts/gunicorn_conf.py"]
CMD ["wsgi:app()"]