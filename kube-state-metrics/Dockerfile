# Image version
ARG KUBE_STATE_METRICS_IMAGE_VERSION="v2.18.0"

# We can not pull this through CI_DEPENDENCY_PROXY_DIRECT_GROUP_IMAGE_PREFIX
# as this is not hosted on dockerhub
FROM registry.k8s.io/kube-state-metrics/kube-state-metrics:${KUBE_STATE_METRICS_IMAGE_VERSION}
