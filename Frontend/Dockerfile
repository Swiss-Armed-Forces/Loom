# Image version
ARG NODE_IMAGE_VERSION="24.2.0-alpine3.22"
ARG NGINX_IMAGE_VERSION="1.27.5-alpine3.21"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/node:${NODE_IMAGE_VERSION} AS base
WORKDIR /code
# Copy dependencies separately and install them once
RUN set -exu \
  && corepack enable
COPY package.json pnpm-lock.yaml .npmrc ./
RUN set -exu \
  && pnpm install --frozen-lockfile
COPY ./ ./

FROM base AS dev
CMD [ "pnpm", "dev" ]

FROM base AS build
ENV NODE_ENV=production
RUN set -exu \
  && pnpm run build

FROM ${DOCKER_REGISTRY}/nginx:${NGINX_IMAGE_VERSION} AS production
# Set a timezone
ENV TZ=UTC
RUN set -exu \
  && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
  && echo $TZ > /etc/timezone
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /code/dist/ /usr/share/nginx/html/
