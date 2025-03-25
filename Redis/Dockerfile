ARG CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
FROM ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/redis:7.2.4-alpine

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]

EXPOSE 6379
