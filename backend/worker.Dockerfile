ARG PYTHON_BUILDER_IMAGE_VERSION="3.11.13-bookworm"
ARG PYTHON_IMAGE_VERSION="3.11.13-bookworm"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/python:${PYTHON_BUILDER_IMAGE_VERSION} AS builder-base

RUN pip install --no-cache-dir poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1


COPY worker/pyproject.toml worker/poetry.lock worker/README.md /code/worker/
COPY common/pyproject.toml common/poetry.lock common/README.md /code/common/
WORKDIR /code/worker

FROM builder-base AS builder-dev
RUN poetry install --no-root --no-directory --no-cache
COPY common/ /code/common
COPY worker/ /code/worker
RUN poetry install --no-cache

FROM builder-base AS builder-prod
RUN poetry install --no-cache --no-root --no-directory --without dev,test
COPY common/ /code/common
COPY worker/ /code/worker
RUN poetry install --no-cache --without dev,test


FROM ${DOCKER_REGISTRY}/python:${PYTHON_IMAGE_VERSION} AS runtime-base

# Package versions
ARG CA_CERTIFICATES_VERSION="20230311"
ARG IMAGEMAGICK_VERSION="8:6.9.*"
ARG GHOSTSCRIPT_VERSION="10.0.*"
ARG LIBLEPTONICA_DEV_VERSION="1.82.*"
ARG PST_UTILS_VERSION="0.6.*"
ARG TSHARK_VERSION="4.0.*"
ARG BINWALK_VERSION="2.3.*"
ARG CABEXTRACT_VERSION="1.9-*"

# install deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates=${CA_CERTIFICATES_VERSION} \
    imagemagick=${IMAGEMAGICK_VERSION} \
    ghostscript=${GHOSTSCRIPT_VERSION} \
    libleptonica-dev=${LIBLEPTONICA_DEV_VERSION} \
    pst-utils=${PST_UTILS_VERSION} \
    tshark=${TSHARK_VERSION} \
    binwalk=${BINWALK_VERSION} \
    cabextract=${CABEXTRACT_VERSION} \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

# Set timezone and permit Celery uid 0 to hide deserialisation warnings
ENV TZ=UTC C_FORCE_ROOT=true
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./worker/imagemagic-policy.xml /etc/ImageMagick-6/policy.xml

ENV BUILDER_VIRTUAL_ENV=/code/worker/.venv \
    VIRTUAL_ENV=/code/.venv \
    PATH="/code/.venv/bin:$PATH"

COPY common/ /code/common
COPY worker/ /code/worker
WORKDIR /code/worker

FROM runtime-base AS dev
COPY --from=builder-dev ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}

# This is required for debugging when using the gevent pool
# ENV GEVENT_SUPPORT=True

EXPOSE 5500
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "127.0.0.1:5500", \
    "-m", "watchdog.watchmedo", "auto-restart", "--verbose", "--recursive", "--signal", "SIGTERM", "--patterns", "*.py", "--directory", "/code/common", "--directory", "/code/worker", "--debounce-interval", "3", \
    "--", \
    "python", "-Xfrozen_modules=off", "-m", "celery", "--app", "worker", "worker", "--loglevel", "DEBUG", "--pool", "threads", "--exclude-queues", "celery.interactive"]

FROM dev AS dev-interactive
EXPOSE 5501
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "127.0.0.1:5501", \
    "-m", "watchdog.watchmedo", "auto-restart", "--verbose", "--recursive", "--signal", "SIGTERM", "--patterns", "*.py", "--directory", "/code/common", "--directory", "/code/worker", "--debounce-interval", "3", \
    "--", \
    "python", "-Xfrozen_modules=off", "-m", "celery", "--app", "worker", "worker", "--loglevel", "DEBUG", "--pool", "threads", "--queues", "celery.interactive"]

FROM dev AS dev-periodic
EXPOSE 5502
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "127.0.0.1:5502", \
    "-m", "watchdog.watchmedo", "auto-restart", "--verbose", "--recursive", "--signal", "SIGTERM", "--patterns", "*.py", "--directory", "/code/common", "--directory", "/code/worker", "--debounce-interval", "3", \
    "--", \
    "python", "-Xfrozen_modules=off", "-m", "celery", "--app", "worker", "worker", "--loglevel", "DEBUG", "--pool", "threads", "--queues", "celery.__periodic"]

FROM dev AS dev-beat
EXPOSE 5503
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "127.0.0.1:5503",\
    "-m", "watchdog.watchmedo", "auto-restart", "--verbose", "--recursive", "--signal", "SIGTERM", "--patterns", "*.py", "--directory", "/code/common", "--directory", "/code/worker", "--debounce-interval", "3", \
    "--", \
    "python", "-Xfrozen_modules=off", "-m", "celery", "--app", "worker", "beat", "--loglevel", "DEBUG"]

FROM runtime-base AS flower
ENV FLOWER_UNAUTHENTICATED_API=1
COPY --from=builder-dev ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
# flower port
EXPOSE 5555
CMD ["python", "-m", "celery", "--app", "worker", "flower", "--broker-api=http://guest:guest@rabbit:15672/api/"]

FROM runtime-base AS production
COPY --from=builder-prod ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
CMD ["python" ,"-m", "celery", "--app", "worker", "worker", "--loglevel", "INFO", "--pool", "threads", "--exclude-queues", "celery.interactive,celery.__periodic"]

FROM production AS production-interactive
CMD ["python", "-m", "celery", "--app", "worker", "worker", "--loglevel", "INFO", "--pool", "threads", "--queues", "celery.interactive"]

FROM production AS production-periodic
CMD ["python", "-m", "celery", "--app", "worker", "worker", "--loglevel", "INFO", "--pool", "threads", "--queues", "celery.__periodic"]

FROM production AS production-beat
CMD ["python", "-m", "celery", "--app", "worker", "beat", "--loglevel", "INFO"]