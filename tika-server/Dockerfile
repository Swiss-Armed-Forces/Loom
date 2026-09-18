# Image version
ARG TIKA_IMAGE_VERSION="3.3.1.0-full"
ARG TIKA_IMAGE_DIGEST="sha256:d8e6ed96260ad89307a93195a1b856102987a818ac648502f8efbaf313d32470"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/apache/tika:${TIKA_IMAGE_VERSION}@${TIKA_IMAGE_DIGEST}

# from: https://github.com/apache/tika-docker/blob/master/full/Dockerfile#L16
# "random" uid/gid hopefully not used anywhere else
# This needs to be set globally and then referenced in
# the subsequent stages -- see TIKA-3912
ARG UID_GID="35002:35002"

USER root:root

# Package versions
ARG TESSERACT_OCR_ALL_VERSION="5.5.*"
ARG IMAGEMAGICK_VERSION="8:7.*"
ARG PYTHON3_SKIMAGE_VERSION="0.26.*"
ARG TINI_VERSION="0.19.*"
ARG CURL_VERSION="8.*"

# install language package for OCR, zstd-jni for compression support, and dependencies for custom-entry-point
# ImageMagick and python3-skimage are required for Tika's image preprocessing (rotation detection, normalization)
RUN set -exu \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  tesseract-ocr-all="${TESSERACT_OCR_ALL_VERSION}" \
  imagemagick="${IMAGEMAGICK_VERSION}" \
  python3-skimage="${PYTHON3_SKIMAGE_VERSION}" \
  tini="${TINI_VERSION}" \
  curl="${CURL_VERSION}" \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Download and install zstd-jni JAR to tika-extras directory
ARG ZSTD_JNI_VERSION="1.5.7-7"

RUN set -exu \
  && mkdir --parents /tika-extras \
  && wget \
    --directory-prefix=/tika-extras \
    --quiet \
    "https://repo1.maven.org/maven2/com/github/luben/zstd-jni/${ZSTD_JNI_VERSION}/zstd-jni-${ZSTD_JNI_VERSION}.jar" \
  && chmod 644 /tika-extras/zstd-jni-${ZSTD_JNI_VERSION}.jar

# Sweeps scratch files left behind by parses that were killed before they could
# clean up. Shipped with the image because the patterns it matches belong to this
# image's Tika and ImageMagick versions.
COPY --chmod=755 tmp-reaper.sh /usr/local/bin/tika-tmp-reaper

USER $UID_GID

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
# Default invocation for running the image on its own. The Helm chart replaces
# it wholesale so that it can pass JVM flags derived from the pod's memory
# budget - no environment variable carries them, as neither this image nor
# upstream's expands one.
CMD ["/bin/sh", "-c", "exec java -cp \"/tika-server-standard-${TIKA_VERSION}.jar:/tika-extras/*\" org.apache.tika.server.core.TikaServerCli -h 0.0.0.0"]
