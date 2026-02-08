# Image version
ARG GOTENBERG_IMAGE_VERSION="8.26.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/gotenberg/gotenberg:${GOTENBERG_IMAGE_VERSION}


USER root
# Install Fonts
# see: https://wiki.debian.org/Fonts
ARG FONTS_RECOMMENDED_VERSION="2"
ARG FONTS_LIBERATION_VERSION="1:2.1.*"
ARG FONTS_NOTO_CYK_EXTRA_VERSION="1:20240730+repack1-1"
ARG FONTS_ARAPHIC_UMING_VERSION="0.2.*"
ARG FONTS_WQY_ZENHEI_VERSION="0.9.*"
ARG FONTS_UNFONTS_CORE_VERSION="1:1.0.*"
ARG FONTS_INDIC_VERSION="2:1.*"
ARG FONTS_DZONGKHA_VERSION="0.*"


RUN set -exu \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    fonts-recommended="${FONTS_RECOMMENDED_VERSION}" \
    fonts-liberation="${FONTS_LIBERATION_VERSION}" \
    fonts-noto-cjk-extra="${FONTS_NOTO_CYK_EXTRA_VERSION}" \
    fonts-arphic-uming="${FONTS_ARAPHIC_UMING_VERSION}" \
    fonts-wqy-zenhei="${FONTS_WQY_ZENHEI_VERSION}" \
    fonts-unfonts-core="${FONTS_UNFONTS_CORE_VERSION}" \
    fonts-indic="${FONTS_INDIC_VERSION}" \
    fonts-dzongkha="${FONTS_DZONGKHA_VERSION}" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


USER gotenberg