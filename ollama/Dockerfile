# Image version
ARG OLLAMA_IMAGE_VERSION="0.9.0"

ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/ollama/ollama:${OLLAMA_IMAGE_VERSION}

# Package versions
ARG CURL_VERSION="7.68.*"
RUN set -exu \
  && apt-get -y update \
  && apt-get -y install --no-install-recommends curl=${CURL_VERSION} \
  && rm -rf /var/lib/apt/lists/*

ARG LLM_MODELS="qwen3:8b smollm2:135m nomic-embed-text:v1.5"
ENV LLM_MODELS=${LLM_MODELS}

RUN set -exu \
  && fork() { (setsid "$@" &); } \
  && fork ollama serve \
  && for i in $(seq 1 3); do \
  [ "$i" -gt 1 ] && sleep 1; \
  curl --silent localhost:11434 && s=0 && break || s=$?; \
  done; if [ "$s" -ne 0 ]; then exit "$s"; fi\
  && for llm_model in ${LLM_MODELS}; do \
  ollama pull "${llm_model}"; \
  done

# Make service accessible from extern
ENV OLLAMA_HOST="0.0.0.0"

ENV OLLAMA_DEBUG=1