"""Construction of the pydantic-ai embedder.

Embeddings go through the same OpenAI-compatible endpoint as the chat clients, so the
connection is built by `common.llm.provider`; this module adds only what is specific to
embedding.
"""

from pydantic_ai import Embedder
from pydantic_ai.embeddings import EmbeddingSettings
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel

from common.llm.provider import build_provider
from common.settings import LLMEmbeddingSettings


def _build_embedding_settings(
    embedding_settings: LLMEmbeddingSettings,
) -> EmbeddingSettings:
    """Embedder-level defaults.

    NOTE: `dimensions` is not sent, which keeps the behaviour the embedding path has
    always had. Its other consumer is `DenseVector(dims=...)` in
    `common.file.file_repository`, so the same number sizes the Elasticsearch field --
    and asking the server for that width would make the two agree by construction rather
    than by convention. Whether to do that is still open: it needs a model trained for
    truncation (the default `nomic-embed-text-v2-moe` is) on a server that implements the
    field, and neither Ollama's nor vLLM's behaviour here has been measured. Withholding
    it per service would also have to live outside the model profile, as pydantic-ai
    resolves no profile for embeddings at all -- `EmbeddingModel` has no `profile`.
    """
    result = EmbeddingSettings()

    if embedding_settings.extra_headers is not None:
        result["extra_headers"] = embedding_settings.extra_headers

    if embedding_settings.extra_body is not None:
        result["extra_body"] = embedding_settings.extra_body

    return result


def build_embedder(embedding_settings: LLMEmbeddingSettings) -> Embedder:
    """Build the embedder for one embedding setting.

    `document_prefix`/`query_prefix` are not applied here: pydantic-ai has no generic
    text-prefix feature, and `embed_documents` versus `embed_query` only forwards an
    input type that the OpenAI embeddings API does not carry. Callers keep prepending
    them.
    """
    return Embedder(
        OpenAIEmbeddingModel(
            embedding_settings.model,
            provider=build_provider(embedding_settings),
        ),
        settings=_build_embedding_settings(embedding_settings),
    )
