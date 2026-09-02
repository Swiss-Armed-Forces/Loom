# Image version
ARG OPEN_WEBUI_IMAGE_VERSION="v0.10.2-slim"
ARG OPEN_WEBUI_IMAGE_DIGEST="sha256:f03f7fcdaf5e3381b3d505c0e66f2bf4e82d1918082022b85dee7da1299b6efd"

# We can not pull this through CI_DEPENDENCY_PROXY_DIRECT_GROUP_IMAGE_PREFIX
# as this is not hosted on dockerhub
FROM ghcr.io/open-webui/open-webui:${OPEN_WEBUI_IMAGE_VERSION}@${OPEN_WEBUI_IMAGE_DIGEST}
