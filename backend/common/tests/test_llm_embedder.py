from common.llm.embedder import _build_embedding_settings
from common.settings import LLMEmbeddingSettings


def test_embedding_settings_never_send_dimensions() -> None:
    """`dimensions` sizes the Elasticsearch `dense_vector` mapping; sending it to the
    API would additionally ask the server to truncate to that width.

    Whether it should is open (see `_build_embedding_settings`), and the field sits
    right there on the settings class -- so the only thing keeping today's behaviour is
    this assertion. Flip it deliberately, not by adding the obvious-looking line.
    """
    assert "dimensions" not in _build_embedding_settings(
        LLMEmbeddingSettings(dimensions=1024)
    )


def test_embedding_settings_carry_the_operator_supplied_extras() -> None:
    """`extra_headers`/`extra_body` are the one thing an operator can push through to
    the embeddings API, so they must survive the translation."""
    result = _build_embedding_settings(
        LLMEmbeddingSettings(
            extra_headers={"x-loom": "1"}, extra_body={"truncate": True}
        )
    )

    assert result.get("extra_headers") == {"x-loom": "1"}
    assert result.get("extra_body") == {"truncate": True}
