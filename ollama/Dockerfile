# Image version
ARG OLLAMA_IMAGE_VERSION="0.18.0"

ARG DOCKER_REGISTRY="docker.io"
FROM ${DOCKER_REGISTRY}/ollama/ollama:${OLLAMA_IMAGE_VERSION}

ARG LLM_MODELS="huihui_ai/qwen3.5-abliterated:9b smollm2:135m nomic-embed-text-v2-moe"
ENV LLM_MODELS=${LLM_MODELS}

# Python
ARG PYTHON_VERSION="3.12.*"
RUN set -exu \
  && apt-get -y update \
  && apt-get -y install --no-install-recommends python3=${PYTHON_VERSION} \
  && rm -rf /var/lib/apt/lists/*

COPY ollama_wrapper.py /bin/ollama_wrapper.py

RUN set -exu \
  && for llm_model in ${LLM_MODELS}; do \
  /bin/ollama_wrapper.py setup pull "${llm_model}"; \
  done

# Make service accessible from extern
ENV OLLAMA_HOST="0.0.0.0"
ENV OLLAMA_DEBUG=1
ENV OLLAMA_NO_CLOUD=1

ENTRYPOINT ["/bin/ollama_wrapper.py", "entry"]
CMD ["serve"]