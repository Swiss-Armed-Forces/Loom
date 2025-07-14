ARG PYTHON_BUILDER_IMAGE_VERSION="3.11.13-bookworm"
ARG PYTHON_IMAGE_VERSION="3.11.13-bookworm"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/python:${PYTHON_BUILDER_IMAGE_VERSION} AS builder-base

RUN pip install --no-cache-dir poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1


COPY common/pyproject.toml common/poetry.lock common/README.md /code/common/
COPY worker/pyproject.toml worker/poetry.lock worker/README.md /code/worker/
WORKDIR /code/worker

FROM builder-base AS builder-dev
# Install dependencies only (not the project itself or directory deps):
# --no-root: we don't need to install our source, we'll copy that to the image later
# --no-directory: we reference common as directory dependency - don't make poetry check for that
# poetry is run twice to support Docker layer caching - this way we don't always have to
# re-install all internet dependencies when something in the source code changes
RUN poetry install --no-root --no-directory --no-cache
COPY common/ /code/common
COPY worker/ /code/worker
RUN poetry install --no-cache

FROM builder-base AS builder-prod
# Install dependencies only (not the project itself or directory deps):
# --no-root: we don't need to install our source, we'll copy that to the image later
# --no-directory: we reference common as directory dependency - don't make poetry check for that
# poetry is run twice to support Docker layer caching - this way we don't always have to
# re-install all internet dependencies when something in the source code changest
RUN poetry install --no-root --no-directory --no-cache --without dev,test
COPY common/ /code/common
COPY worker/ /code/worker
RUN poetry install --no-cache --without dev,test


FROM ${DOCKER_REGISTRY}/python:${PYTHON_IMAGE_VERSION} AS runtime-base

# Package versions
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
CMD ["python" ,"main.py", "shell"]

FROM runtime-base AS production
COPY --from=builder-prod ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
CMD ["python" , "main.py", "shell"]