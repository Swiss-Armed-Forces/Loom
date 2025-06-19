ARG REDIS_IMAGE_VERSION="7.4.4-alpine3.21"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/redis:${REDIS_IMAGE_VERSION}

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]

EXPOSE 6379
