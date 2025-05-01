ARG REDIS_IMAGE_VERSION="7.2.4-alpine"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/redis:${REDIS_IMAGE_VERSION}

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]

EXPOSE 6379
