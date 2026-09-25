import pytest
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles import InlineDefsJsonSchemaTransformer, ModelProfile

from common.llm.provider import build_provider
from common.settings import LLMClientSettings, LLMProvider

# The services that execute an open-weight chat template, as opposed to answering for a
# vendor whose own lookup table knows the model. Everything Loom asserts about templates,
# reasoning support and strict tool definitions is asserted about this set, so a new
# `LLMProvider` value gains coverage in one place or in none.
_OPEN_WEIGHT_PROVIDERS = [
    LLMProvider.OLLAMA,
    LLMProvider.LITELLM,
    LLMProvider.INFOMANIAK,
]


def _profile(client_settings: LLMClientSettings) -> ModelProfile:
    """The profile as pydantic-ai finally resolves it.

    The provider layers the family and Loom's claims into its own profile, so only the
    model can say what they add up to.
    """
    return OpenAIChatModel(
        client_settings.model, provider=build_provider(client_settings)
    ).profile


@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_services_running_open_weight_templates_merge_system_messages(
    provider: LLMProvider,
) -> None:
    """Regression guard for !756.

    vLLM rendering Qwen's template answers "System message must be at the beginning" as
    soon as a capability's instructions add a second `InstructionPart`. Both keys are
    needed: one folds consecutive leading system messages, the other demotes the ones
    that follow.
    """
    profile = _profile(LLMClientSettings(provider=provider))

    assert profile.get("openai_chat_supports_multiple_system_messages") is False
    assert profile.get("supports_inline_system_prompts") is False


def test_hosted_openai_keeps_its_system_messages() -> None:
    """The API takes repeated system messages at full weight; demoting them to user text
    would weaken instructions for no reason.

    The key name is pinned by the positive assertion above, which fails outright if it
    is ever misspelled here.
    """
    profile = _profile(LLMClientSettings(provider=LLMProvider.OPENAI))

    assert profile.get("openai_chat_supports_multiple_system_messages", True) is True


@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_services_running_open_weight_templates_withhold_strict_tools(
    provider: LLMProvider,
) -> None:
    """No family transformer computes strict compatibility.

    `InlineDefsJsonSchemaTransformer` and `GoogleJsonSchemaTransformer` both leave
    `is_strict_compatible` at its `True` default without emitting `additionalProperties:
    false`, and pydantic-ai reads the tool's `strict` flag straight off that -- so a
    backend honouring the flag would reject every tool and every `NativeOutput` schema.
    Upstream withholds it for Ollama; the other two must too.
    """
    profile = _profile(LLMClientSettings(provider=provider))

    assert profile.get("json_schema_transformer") is InlineDefsJsonSchemaTransformer
    assert profile.get("openai_supports_strict_tool_definition") is False


def test_ollama_provider_is_selected() -> None:
    model = OpenAIChatModel(
        LLMClientSettings().model,
        provider=build_provider(LLMClientSettings(provider=LLMProvider.OLLAMA)),
    )

    assert model.system == "ollama"
    # `openai_chat_supports_max_completion_tokens` is LoomOllamaProvider's own; the other
    # two also come from upstream's `OllamaProvider`, and are asserted here to prove the
    # subclass still layers over that base rather than replacing it.
    assert model.profile.get("openai_chat_supports_max_completion_tokens") is False
    assert model.profile.get("openai_supports_strict_tool_definition") is False
    assert model.profile.get("openai_chat_thinking_field") == "reasoning"


def test_infomaniak_reports_its_own_service_name() -> None:
    """`OpenAIProvider.name` is the literal "openai", which would label Infomaniak usage
    and latency as OpenAI's and arm pydantic-ai's `system == 'openai'` branches."""
    model = OpenAIChatModel(
        LLMClientSettings().model,
        provider=build_provider(LLMClientSettings(provider=LLMProvider.INFOMANIAK)),
    )

    assert model.system == "infomaniak"


def test_infomaniak_withholds_openai_only_fields() -> None:
    """Infomaniak answers 422 validation_failed for fields it does not know, and
    published integrations whitelist `max_tokens` without `max_completion_tokens`."""
    profile = _profile(LLMClientSettings(provider=LLMProvider.INFOMANIAK))

    assert profile.get("openai_chat_supports_max_completion_tokens") is False


@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_family_is_matched_through_an_author_namespace(provider: LLMProvider) -> None:
    """`huihui_ai/qwen3.5-abliterated:9b` matches no prefix upstream, on any provider,
    so no family rules would apply at all. Dropping the namespace restores the match.

    `ignore_streamed_leading_whitespace` comes only from the qwen family profile, so it
    is the key that says the match happened.
    """
    profile = _profile(
        LLMClientSettings(provider=provider, model="huihui_ai/qwen3.5-abliterated:9b")
    )

    assert profile.get("ignore_streamed_leading_whitespace") is True
    assert profile.get("json_schema_transformer") is InlineDefsJsonSchemaTransformer


def test_a_model_name_carrying_no_family_gets_no_family_rules() -> None:
    """The match is a claim about the weights; an opaque deployment alias makes none."""
    profile = _profile(
        LLMClientSettings(provider=LLMProvider.LITELLM, model="prod-deployment-1")
    )

    assert profile.get("json_schema_transformer") is not InlineDefsJsonSchemaTransformer
    assert profile.get("ignore_streamed_leading_whitespace") is not True


@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_self_hosted_providers_claim_thinking_support(provider: LLMProvider) -> None:
    """No lookup table recognises an open-weight model name, so pydantic-ai's default
    `supports_thinking=False` is absence of knowledge on every service serving one.

    Infomaniak included: it answers 200 to `reasoning_effort`, measured against a real
    product_id (see `InfomaniakProvider`), so the strict field validation that withholds
    `max_completion_tokens` is no reason to withhold this one too.
    """
    profile = _profile(LLMClientSettings(provider=provider))

    assert profile.get("supports_thinking", False) is True


@pytest.mark.parametrize(
    ("model", "claims_thinking"),
    [
        pytest.param("huihui_ai/qwen3.5-abliterated:9b", True, id="author-namespace"),
        pytest.param("prod-deployment-1", True, id="opaque-alias"),
        pytest.param("openai/gpt-4o", False, id="vendor-prefix"),
    ],
)
def test_litellm_leaves_a_vendors_own_thinking_knowledge_alone(
    model: str, claims_thinking: bool
) -> None:
    """A `/` is an author namespace on open weights or a vendor prefix upstream
    resolves, and only the family table tells them apart.

    The thinking claim is an admission that no table recognised the name, so it must not
    override the vendor's own answer -- `openai/gpt-4o` accepts no `reasoning_effort`
    and would answer 400.
    """
    profile = _profile(LLMClientSettings(provider=LLMProvider.LITELLM, model=model))

    assert profile.get("supports_thinking", False) is claims_thinking
