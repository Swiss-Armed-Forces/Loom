# Image version
ARG PYTHON_BUILDER_IMAGE_VERSION="3.14.8-bookworm"
ARG PYTHON_BUILDER_IMAGE_DIGEST="sha256:b3c121f5b6b446c964c6ea924d9a099e259b29d7b56df82729e33572a31eadcc"
ARG PYTHON_IMAGE_VERSION="3.14.8-bookworm"
ARG PYTHON_IMAGE_DIGEST="sha256:b3c121f5b6b446c964c6ea924d9a099e259b29d7b56df82729e33572a31eadcc"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/python:${PYTHON_BUILDER_IMAGE_VERSION}@${PYTHON_BUILDER_IMAGE_DIGEST} AS builder-base

ARG POETRY_VERSION="2.3.1"
RUN set -exu \
    && pip install --no-cache-dir poetry==${POETRY_VERSION}

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
RUN set -exu \
    && poetry install --no-root --no-directory --no-cache
COPY common/ /code/common
COPY worker/ /code/worker
RUN set -exu \
    && poetry install --no-cache

FROM builder-base AS builder-prod
# Install dependencies only (not the project itself or directory deps):
# --no-root: we don't need to install our source, we'll copy that to the image later
# --no-directory: we reference common as directory dependency - don't make poetry check for that
# poetry is run twice to support Docker layer caching - this way we don't always have to
# re-install all internet dependencies when something in the source code changest
RUN set -exu \
    && poetry install --no-root --no-directory --no-cache --without dev,test
COPY common/ /code/common
COPY worker/ /code/worker
RUN set -exu \
    && poetry install --no-cache --without dev,test


FROM ${DOCKER_REGISTRY}/python:${PYTHON_IMAGE_VERSION}@${PYTHON_IMAGE_DIGEST} AS runtime-base

# Package versions
ARG IMAGEMAGICK_VERSION="8:6.9.*"
ARG GHOSTSCRIPT_VERSION="10.0.*"
ARG LIBLEPTONICA_DEV_VERSION="1.82.*"
ARG PST_UTILS_VERSION="0.6.*"
ARG TSHARK_VERSION="4.0.*"
ARG RIPSECRETS_VERSION="0.1.11"
ARG CURL_VERSION="7.88.*"
ARG TRUFFLEHOG_VERSION="v3.90.6"
ARG BINUTILS_VERSION="2.40-*"
ARG SEAWEEDFS_VERSION="4.17"

# Checksums for verifying downloaded binaries
# These are verified at build time to prevent supply chain attacks
ARG TRUFFLEHOG_AMD64_SHA256="edbca2465f76a7a4aa2f87ed02559975e366b7e9142a5dee035f65fd51a970ae"
ARG TRUFFLEHOG_ARM64_SHA256="badf4d2ad147a91c99adcde5c40e69fc3808496d72aa9b1f8265824862488277"
# ripsecrets: only amd64 available (upstream publishes no linux/arm64 binary)
ARG RIPSECRETS_AMD64_SHA256="9daf017dfdea242a58f672450a2526f0406211afe9e872c740adc49b42feccf5"  # nosec ripsecrets
ARG SEAWEEDFS_AMD64_SHA256="b7f68af1d4d90c14130c5d0d719a14d78194ac7deb9983f485fffe6a3c5d56ce"
ARG SEAWEEDFS_ARM64_SHA256="186a1ec831bed8cd37349425ae176eda9ff1b628463a0a3fbb846c5fa61fbff7"

SHELL [ "/bin/bash", "-o", "pipefail", "-c" ]

# Target architecture of this build ("amd64", "arm64"). BuildKit populates the
# predefined build arg; declaring it here makes it visible to the RUN below and
# keeps it correct under cross-compilation, unlike `dpkg --print-architecture`.
ARG TARGETARCH

# install deps
RUN set -exu \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    imagemagick=${IMAGEMAGICK_VERSION} \
    ghostscript=${GHOSTSCRIPT_VERSION} \
    libleptonica-dev=${LIBLEPTONICA_DEV_VERSION} \
    pst-utils=${PST_UTILS_VERSION} \
    tshark=${TSHARK_VERSION} \
    curl=${CURL_VERSION} \
    binutils=${BINUTILS_VERSION} \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

# install binaries downloaded from GitHub releases. Versions and checksums stay
# here so the pinned values sit next to the package versions above; the script
# does the downloading, verifying and unpacking.
COPY worker/docker/install-third-party-binaries.sh /tmp/install-third-party-binaries.sh
RUN set -exu \
    && /tmp/install-third-party-binaries.sh \
        --target-arch "${TARGETARCH}" \
        --trufflehog-version "${TRUFFLEHOG_VERSION}" \
        --trufflehog-amd64-sha256 "${TRUFFLEHOG_AMD64_SHA256}" \
        --trufflehog-arm64-sha256 "${TRUFFLEHOG_ARM64_SHA256}" \
        --ripsecrets-version "${RIPSECRETS_VERSION}" \
        --ripsecrets-amd64-sha256 "${RIPSECRETS_AMD64_SHA256}" \
        --seaweedfs-version "${SEAWEEDFS_VERSION}" \
        --seaweedfs-amd64-sha256 "${SEAWEEDFS_AMD64_SHA256}" \
        --seaweedfs-arm64-sha256 "${SEAWEEDFS_ARM64_SHA256}" \
    && rm /tmp/install-third-party-binaries.sh


# Set timezone and permit Celery uid 0 to hide deserialisation warnings
ENV TZ=UTC C_FORCE_ROOT=true
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

WORKDIR /usr/share/misc/magic
COPY ./worker/docker/email.magic /usr/share/misc/magic/email.magic
RUN set -exu \
    && file -C -m /usr/share/misc/magic/email.magic

ENV BUILDER_VIRTUAL_ENV=/code/worker/.venv \
    VIRTUAL_ENV=/code/.venv \
    PATH="/code/.venv/bin:$PATH" \
    MAGIC="/usr/share/misc/magic.mgc:/usr/share/misc/magic/email.magic.mgc"

COPY common/ /code/common
COPY worker/ /code/worker
WORKDIR /code/worker

FROM runtime-base AS dev
COPY --from=builder-dev ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
CMD ["python" ,"main.py", "shell"]

FROM runtime-base AS production
COPY --from=builder-prod ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
CMD ["python" , "main.py", "shell"]
