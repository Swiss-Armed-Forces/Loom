# SeaweedFS Image
# https://hub.docker.com/r/chrislusf/seaweedfs
ARG SEAWEEDFS_IMAGE_VERSION="4.17_full"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/chrislusf/seaweedfs:${SEAWEEDFS_IMAGE_VERSION}

# Set timezone to UTC
ENV TZ=UTC

# Dependencies for restore.sh
ARG SQLITE_VERSION="3.51"
RUN set -exu \
    && apk add --no-cache \
    sqlite~=${SQLITE_VERSION}

# Copy restore script for filer metadata backup
COPY --chmod=755 restore.sh /scripts/restore.sh

# SeaweedFS ports:
# 9333 - Master HTTP
# 19333 - Master gRPC
# 8080 - Volume HTTP
# 18080 - Volume gRPC
# 8888 - Filer HTTP
# 18888 - Filer gRPC
# 8333 - S3 API
EXPOSE 9333 19333 8080 18080 8888 18888 8333
