ARG PYTHON_BUILDER_IMAGE_VERSION="3.11.13-bookworm"
ARG PYTHON_IMAGE_VERSION="3.11.13-slim-bookworm"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/python:${PYTHON_BUILDER_IMAGE_VERSION} AS builder-base

RUN pip install --no-cache-dir poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1


COPY common/pyproject.toml common/poetry.lock common/README.md /code/common/
COPY crawler/pyproject.toml crawler/poetry.lock crawler/README.md /code/crawler/
WORKDIR /code/crawler

FROM builder-base AS builder-dev
# Install dependencies only (not the project itself or directory deps):
# --no-root: we don't need to install our source, we'll copy that to the image later
# --no-directory: we reference common as directory dependency - don't make poetry check for that
# poetry is run twice to support Docker layer caching - this way we don't always have to
# re-install all internet dependencies when something in the source code changes
RUN poetry install --no-root --no-directory --no-cache
COPY common/ /code/common
COPY crawler/ /code/crawler
RUN poetry install --no-cache

FROM builder-base AS builder-prod
# Install dependencies only (not the project itself or directory deps):
# --no-root: we don't need to install our source, we'll copy that to the image later
# --no-directory: we reference common as directory dependency - don't make poetry check for that
# poetry is run twice to support Docker layer caching - this way we don't always have to
# re-install all internet dependencies when something in the source code changest
RUN poetry install --no-root --no-directory --no-cache --without dev,test
COPY common/ /code/common
COPY crawler/ /code/crawler
RUN poetry install --no-cache --without dev,test


# The runtime image, used to just run the code provided its virtual environment
FROM ${DOCKER_REGISTRY}/python:${PYTHON_IMAGE_VERSION} AS runtime-base

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV BUILDER_VIRTUAL_ENV=/code/crawler/.venv \
    VIRTUAL_ENV=/code/.venv \
    PATH="/code/.venv/bin:$PATH"
COPY common/ /code/common
COPY crawler/ /code/crawler
WORKDIR /code/crawler

FROM runtime-base AS dev
COPY --from=builder-dev ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}

EXPOSE 6601
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "127.0.0.1:6601", \
    "-m", "watchdog.watchmedo", "auto-restart", "--verbose", "--recursive", "--signal", "SIGTERM", "--patterns", "*.py", "--directory", "/code/common", "--directory", "/code/crawler",  "--debounce-interval", "3",\
    "--", \
    "python", "-Xfrozen_modules=off", "-m", "crawler.main" \
    ]

FROM runtime-base AS production
COPY --from=builder-prod ${BUILDER_VIRTUAL_ENV} ${VIRTUAL_ENV}
CMD ["python", "-m", "crawler.main"]
