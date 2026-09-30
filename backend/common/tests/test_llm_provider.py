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
    backend honouring the flag would reject every tool and every native-output schema.
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


# The checkpoints `values-development.yaml` swaps in, both far below the floor.
_DEVELOPMENT_MODELS = ["qwen2.5:0.5b", "moondream:1.8b"]


@pytest.mark.parametrize("model", _DEVELOPMENT_MODELS)
@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_weights_below_the_floor_get_grammar_constrained_output(
    provider: LLMProvider, model: str
) -> None:
    """Tool output is only as good as the weights; native output is not.

    A tool call has to come back well-formed from the model's own chat template, and
    nothing between the sampler and the parser checks its shape -- which `qwen2.5:0.5b`,
    the model the development profile and the integration tests run, cannot manage.
    Native output compiles the schema into a grammar in the service and decodes under
    it, so the schema holds whatever the weights would rather have said.

    Asserted for all three services because each merges the claim in its own chain.
    """
    profile = _profile(LLMClientSettings(provider=provider, model=model))

    assert profile.get("default_structured_output_mode") == "native"


@pytest.mark.parametrize("provider", _OPEN_WEIGHT_PROVIDERS)
def test_the_production_model_keeps_tool_output(provider: LLMProvider) -> None:
    """The floor is a claim about small weights, not a preference for grammars.

    Tool output has the broader support and keeps the output schema out of the prompt,
    so a model large enough to follow its own template keeps pydantic-ai's default. Also
    pins that the author namespace does not confuse the tag read.
    """
    profile = _profile(
        LLMClientSettings(provider=provider, model="huihui_ai/qwen3.5-abliterated:9b")
    )

    assert profile.get("default_structured_output_mode", "tool") == "tool"


@pytest.mark.parametrize(
    ("model", "mode"),
    [
        pytest.param("qwen2.5:0.5b", "native", id="half-a-billion"),
        pytest.param("qwen2.5:3b", "native", id="just-under-the-floor"),
        pytest.param("gemma3:4b", "tool", id="on-the-floor"),
        pytest.param("llama3.3:70b-instruct-q4_K_M", "tool", id="quantisation-suffix"),
        pytest.param("mixtral:8x7b", "tool", id="expert-layout-not-a-size"),
        pytest.param("Qwen/Qwen3.5-122B-A10B-FP8", "tool", id="no-tag"),
        pytest.param("prod-deployment-1", "tool", id="opaque-alias"),
        pytest.param("qwen3.5:latest", "tool", id="unhelpful-tag"),
    ],
)
def test_the_parameter_tag_decides_the_output_mode(model: str, mode: str) -> None:
    """The tag is the claim, and the floor is exclusive.

    `8x7b` is an expert layout rather than a parameter count, and a name stating no size
    states nothing -- both fall back to `tool`, which is the mode every other layer in
    the provider is already written for.
    """
    profile = _profile(LLMClientSettings(provider=LLMProvider.OLLAMA, model=model))

    assert profile.get("default_structured_output_mode", "tool") == mode


def test_hosted_openai_decides_its_own_output_mode() -> None:
    """`OpenAIProvider` is left exactly as pydantic-ai ships it.

    The deliberately absurd model name is the point: it proves the floor is not merged
    into that branch at all, rather than merely never firing there.
    """
    profile = _profile(
        LLMClientSettings(provider=LLMProvider.OPENAI, model="qwen2.5:0.5b")
    )

    assert profile.get("default_structured_output_mode", "tool") == "tool"
