# Image version
ARG PYTHON_BUILDER_IMAGE_VERSION="3.14.7-bookworm"
ARG PYTHON_BUILDER_IMAGE_DIGEST="sha256:bfb689a7986adc6d5f16722e06c78e755efe4062e56276715fef450cbad09436"
ARG PYTHON_IMAGE_VERSION="3.14.7-bookworm"
ARG PYTHON_IMAGE_DIGEST="sha256:bfb689a7986adc6d5f16722e06c78e755efe4062e56276715fef450cbad09436"

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
    && TRUFFLEHOG_ARCH="" \
    && if [ "${TARGETARCH}" = "amd64" ]; then TRUFFLEHOG_ARCH="linux_amd64"; fi \
    && if [ "${TARGETARCH}" = "arm64" ]; then TRUFFLEHOG_ARCH="linux_arm64"; fi \
    && if [ -z "${TRUFFLEHOG_ARCH}" ]; then echo "Unsupported architecture: ${TARGETARCH}" && exit 1; fi \
    && curl -sSfL "https://github.com/trufflesecurity/trufflehog/releases/download/${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION#v}_${TRUFFLEHOG_ARCH}.tar.gz" \
        -o /tmp/trufflehog.tar.gz \
    && tar -xzf /tmp/trufflehog.tar.gz -C /usr/local/bin trufflehog \
    && mv /usr/local/bin/trufflehog /usr/local/bin/.trufflehog-wrapped \
    && printf '#!/bin/sh\nexec /usr/local/bin/.trufflehog-wrapped --no-update "$@"\n' > /usr/local/bin/trufflehog \
    && chmod +x /usr/local/bin/trufflehog \
    && rm /tmp/trufflehog.tar.gz \
    && trufflehog --version \
    && RIPSECRETS_INSTALLED="" \
    && if [ "${TARGETARCH}" = "amd64" ]; then \
        curl -LO "https://github.com/sirwart/ripsecrets/releases/download/v${RIPSECRETS_VERSION}/ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
        && tar -xzf "ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
        && mv "ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu/ripsecrets" /usr/local/bin/ripsecrets \
        && rm "ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu.tar.gz" \
        && rm -rf "ripsecrets-${RIPSECRETS_VERSION}-x86_64-unknown-linux-gnu" \
        && echo "ripsecrets installed for amd64" \
        && RIPSECRETS_INSTALLED="yes"; \
    fi \
    && if [ -z "${RIPSECRETS_INSTALLED}" ]; then \
        echo "WARNING: ripsecrets is not installed on ${TARGETARCH}: upstream publishes" \
        "no linux ${TARGETARCH} release artifact. ripsecrets_scan_task detects the" \
        "missing binary at runtime and reports 'not scanned' for every file."; \
    fi \
    && SW_ARCH="" \
    && if [ "${TARGETARCH}" = "amd64" ]; then SW_ARCH="linux_amd64"; fi \
    && if [ "${TARGETARCH}" = "arm64" ]; then SW_ARCH="linux_arm64"; fi \
    && if [ -z "${SW_ARCH}" ]; then echo "Unsupported architecture: ${TARGETARCH}" && exit 1; fi \
    && curl -LO "https://github.com/seaweedfs/seaweedfs/releases/download/${SEAWEEDFS_VERSION}/${SW_ARCH}.tar.gz" \
    && tar -xzf "${SW_ARCH}.tar.gz" \
    && mv weed /usr/local/bin/weed \
    && chmod +x /usr/local/bin/weed \
    && rm "${SW_ARCH}.tar.gz" \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*


# Set timezone and permit Celery uid 0 to hide deserialisation warnings
ENV TZ=UTC C_FORCE_ROOT=true
RUN set -exu \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

WORKDIR /usr/share/misc/magic
COPY ./worker/magic/email.magic /usr/share/misc/magic/email.magic
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
