# Image version
ARG KUBE_STATE_METRICS_IMAGE_VERSION="v2.18.0"
ARG KUBE_STATE_METRICS_IMAGE_DIGEST="sha256:1545919b72e3ae035454fc054131e8d0f14b42ef6fc5b2ad5c751cafa6b2130e"

# We can not pull this through CI_DEPENDENCY_PROXY_DIRECT_GROUP_IMAGE_PREFIX
# as this is not hosted on dockerhub
FROM registry.k8s.io/kube-state-metrics/kube-state-metrics:${KUBE_STATE_METRICS_IMAGE_VERSION}@${KUBE_STATE_METRICS_IMAGE_DIGEST}
