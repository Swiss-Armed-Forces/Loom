ARG TIKA_IMAGE_VERSION="2.9.2.1-full"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/apache/tika:${TIKA_IMAGE_VERSION}

# from: https://github.com/apache/tika-docker/blob/master/full/Dockerfile#L16
# "random" uid/gid hopefully not used anywhere else
# This needs to be set globally and then referenced in
# the subsequent stages -- see TIKA-3912
ARG UID_GID="35002:35002"

USER root:root

# Package versions
ARG TESSERACT_OCR_ALL_VERSION="5.3.*"

# install language package for OCR and dependencies for custom-entry-point
RUN set -exu \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
	tesseract-ocr-all=${TESSERACT_OCR_ALL_VERSION} \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY tika-config.xml /tika-config.xml

USER $UID_GID

ENV TIKA_JAVA_OPS="-XX:InitialRAMPercentage=90 -XX:MaxRAMPercentage=90"

EXPOSE 8000

ENTRYPOINT [ "/bin/sh", "-c", "exec java ${TIKA_JAVA_OPS} -cp \"/tika-server-standard-${TIKA_VERSION}.jar:/tika-extras/*\" org.apache.tika.server.core.TikaServerCli -h 0.0.0.0 $0 $@"]

CMD [ "-c", "/tika-config.xml"]
