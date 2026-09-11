# SeaweedFS Image
# https://hub.docker.com/r/chrislusf/seaweedfs
ARG SEAWEEDFS_IMAGE_VERSION="4.23_full"
ARG SEAWEEDFS_IMAGE_DIGEST="sha256:6a4620b8cacc373a30fd5eb963c3e4a211b17acc8ad2257b7049abc1984ef2be"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/chrislusf/seaweedfs:${SEAWEEDFS_IMAGE_VERSION}@${SEAWEEDFS_IMAGE_DIGEST}

# Set timezone to UTC
ENV TZ=UTC

# SeaweedFS ports:
# 9333 - Master HTTP
# 19333 - Master gRPC
# 8080 - Volume HTTP
# 18080 - Volume gRPC
# 8888 - Filer HTTP
# 18888 - Filer gRPC
# 8333 - S3 API
EXPOSE 9333 19333 8080 18080 8888 18888 8333
