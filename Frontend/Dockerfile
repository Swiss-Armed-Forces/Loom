# Image version
ARG NODE_IMAGE_VERSION="24.15.0-alpine3.23"
ARG NODE_IMAGE_DIGEST="sha256:d1b3b4da11eefd5941e7f0b9cf17783fc99d9c6fc34884a665f40a06dbdfc94f"
ARG NGINX_IMAGE_VERSION="1.30.3-alpine3.23"
ARG NGINX_IMAGE_DIGEST="sha256:0d3b80406a13a767339fbe2f41406d6c7da727ab89cf8fae399e81f780f814d1"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/node:${NODE_IMAGE_VERSION}@${NODE_IMAGE_DIGEST} AS base
WORKDIR /code
# Copy dependencies separately and install them once
ARG PNPM_VERSION="10.32.1"
RUN set -exu \
  && npm install -g "pnpm@$PNPM_VERSION"
COPY \
  package.json \
  pnpm-workspace.yaml \
  pnpm-lock.yaml \
  .npmrc \
  ./
COPY patches patches
RUN set -exu \
  && pnpm install --frozen-lockfile
COPY ./ ./

FROM base AS dev
CMD [ "pnpm", "dev" ]

FROM base AS build
ENV NODE_ENV=production
RUN set -exu \
  && pnpm run build

FROM ${DOCKER_REGISTRY}/nginx:${NGINX_IMAGE_VERSION}@${NGINX_IMAGE_DIGEST} AS production
# Set a timezone
ENV TZ=UTC
RUN set -exu \
  && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
  && echo $TZ > /etc/timezone
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /code/dist/ /usr/share/nginx/html/
