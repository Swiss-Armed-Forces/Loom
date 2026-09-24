"""The pydantic-ai providers Loom connects through.

A provider handles the authentication and connection to one LLM service, and supplies
the model profile describing how requests for that service must be shaped. pydantic-ai
ships one for Ollama, one for LiteLLM and one for OpenAI; it ships nothing for
Infomaniak, and the two it does ship do not know the model names Loom uses.

Rather than keep that knowledge in a lookup table beside them, each gap is closed the
way pydantic-ai documents -- "if a model API is compatible with the OpenAI API, you do
not need a custom model class and can provide your own custom provider instead" -- by
subclassing the provider and overriding `model_profile`. One `LLMProvider` value, one
provider class, one place per service where its quirks are written down.

Everything the profile needs is resolved here, from the two facts a provider has: which
service it is, and what model name it was asked for. Nothing in this module reads
settings, which is why `model_profile` can stay the plain static hook pydantic-ai
declares it as.
"""

from typing import Callable, assert_never

from openai import AsyncOpenAI
from pydantic_ai.profiles import ModelProfile, merge_profile
from pydantic_ai.profiles.cohere import cohere_model_profile
from pydantic_ai.profiles.deepseek import deepseek_model_profile
from pydantic_ai.profiles.google import google_model_profile
from pydantic_ai.profiles.harmony import harmony_model_profile
from pydantic_ai.profiles.meta import meta_model_profile
from pydantic_ai.profiles.mistral import mistral_model_profile
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.profiles.qwen import qwen_model_profile
from pydantic_ai.providers import Provider
from pydantic_ai.providers.litellm import LiteLLMProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from common.settings import LLMClientSettings, LLMProvider

# Request-construction rules per model family, keyed by the prefix the weights' own name
# carries. The same eight prefixes `OllamaProvider` matches on, applied to every service
# Loom talks to rather than that one: the rules describe the weights, and a family is no
# less true of a checkpoint because vLLM is serving it.
#
# Kept at parity with upstream's table so the two can be diffed; `mixtral` is the one
# addition.
_FAMILY_PROFILES: dict[str, Callable[[str], ModelProfile | None]] = {
    "llama": meta_model_profile,
    "gemma": google_model_profile,
    "qwen": qwen_model_profile,
    "qwq": qwen_model_profile,
    "deepseek": deepseek_model_profile,
    "mistral": mistral_model_profile,
    # Not a typo for the line above: Infomaniak serves Mistral's MoE under `mixtral`,
    # which shares none of `mistral`'s prefix.
    "mixtral": mistral_model_profile,
    "command": cohere_model_profile,
    "gpt-oss": harmony_model_profile,
}

# Claimed for services on which no lookup table recognises the model name: pydantic-ai's
# `supports_thinking=False` default is absence of knowledge there, and leaving it makes
# `Model.prepare_request` strip `thinking` and send no reasoning_effort at all (#307).
#
# Merged above the family profile, which spells the same ignorance as a hard `False`:
# gemma reaches it through Google's `'gemini-2.5' in model_name` test and gpt-oss through
# OpenAI's reasoning table -- neither is a claim about the open weights being served.
#
# Not claimed for OpenAIProvider -- its own table knows, per model, and a blanket claim
# would send reasoning_effort to gpt-4o and earn a 400.
_CLAIMS_THINKING_SUPPORT = ModelProfile(supports_thinking=True)

# Asserted for services that execute an open-weight chat template, which is what decides
# whether a request may carry more than one system message. Merging folds consecutive
# leading system messages into one; `supports_inline_system_prompts` demotes any that
# follow to user-role text.
#
# Required for vLLM behind LiteLLM: rendering Qwen's template, it answers "System message
# must be at the beginning" as soon as a capability's instructions add a second
# `InstructionPart` (!756). Claimed for Ollama and Infomaniak as well -- they run the same
# family of templates, and merging costs nothing where it is not needed, as it is a no-op
# on the single leading instruction every non-agent client sends.
#
# Absent deliberately:
#   OpenAIProvider  -- accepts repeated system messages, and demoting them to user text
#                      would weaken instructions the API takes at full weight.
_MERGES_SYSTEM_MESSAGES = OpenAIModelProfile(
    openai_chat_supports_multiple_system_messages=False,
    supports_inline_system_prompts=False,
)

# Withheld wherever a family profile decides the schema transformer, because none of them
# computes strict compatibility: `InlineDefsJsonSchemaTransformer` and
# `GoogleJsonSchemaTransformer` both leave `is_strict_compatible` at its `True` default
# without emitting `additionalProperties: false` or promoting optional properties into
# `required`. pydantic-ai reads the tool's `strict` flag straight off that
# (`strict=schema_transformer.is_strict_compatible if tool_def.strict is None`), so every
# tool and every `NativeOutput` schema would be declared strict while being nothing of the
# sort -- and a backend that honours the flag answers "'additionalProperties' is required
# to be supplied and to be false", or builds a guided-decoding grammar off the wrong
# schema. Upstream's Ollama profile withholds it for exactly this reason; the other two
# services need the same guard rather than inheriting it by accident.
#
# Applied to the whole provider rather than per family: strict is a capability of the
# tool-calling implementation, and the services Loom points these classes at serve open
# weights, where a grammar derived from a non-strict schema is the failure mode, not the
# feature.
_WITHHOLDS_STRICT_TOOL_DEFINITIONS = OpenAIModelProfile(
    openai_supports_strict_tool_definition=False,
)


def _family_profile(model_name: str) -> ModelProfile | None:
    """Family rules for a model name, matched on the name the weights actually carry.

    pydantic-ai matches the family with `model_name.startswith(...)` against the name as
    served, which misses every community re-upload published under an author namespace:
    `huihui_ai/qwen3.5-abliterated:9b` matches no prefix, so no family rules apply at
    all. Dropping the namespace restores the match; the remaining tag (`:9b`) does not
    interfere, as the family functions only read the leading name.

    The match is what makes structured output work -- the family profile is where
    `json_schema_transformer` comes from, and a generic OpenAI transformer applied to
    Qwen inlines no `$defs`, so the model answers unparsable JSON rather than erroring.
    """
    name = model_name.rsplit("/", 1)[-1].lower()

    for prefix, profile in _FAMILY_PROFILES.items():
        if name.startswith(prefix):
            return profile(name)

    return None


class LoomOllamaProvider(OllamaProvider):
    """Ollama, with the family matched on the re-uploaded model name."""

    @staticmethod
    def model_profile(model_name: str) -> ModelProfile | None:
        return merge_profile(
            # Taken as the base for everything upstream knows about Ollama; its own
            # family lookup misses the namespaced name, which is what the layer above
            # restores.
            OllamaProvider.model_profile(model_name),
            _family_profile(model_name),
            _CLAIMS_THINKING_SUPPORT,
            _MERGES_SYSTEM_MESSAGES,
            _WITHHOLDS_STRICT_TOOL_DEFINITIONS,
            OpenAIModelProfile(
                # Ollama's ChatCompletionRequest carries `max_tokens` only, mapped onto
                # its native `num_predict`. Unknown fields are dropped without an error,
                # so sending `max_completion_tokens` would silently stop capping
                # anything.
                openai_chat_supports_max_completion_tokens=False,
                # Re-asserted, not inherited: upstream applies it last so that it wins,
                # and the family layer above sits between. No family profile sets this
                # key today, so restating it changes nothing now and keeps an upstream
                # release from inverting the precedence later.
                openai_chat_thinking_field="reasoning",
            ),
        )


class LoomLiteLLMProvider(LiteLLMProvider):
    """LiteLLM, with the family matched on the served model name.

    Upstream reads the family from a `vendor/model` prefix and otherwise falls back to
    an OpenAI profile. In Loom's deployments LiteLLM fronts vLLM, where the served name
    is whatever the operator configured it as -- usually the bare weights name, carrying
    no vendor prefix -- so that fallback is what a Qwen deployment actually gets.
    """

    @staticmethod
    def model_profile(model_name: str) -> ModelProfile | None:
        family = _family_profile(model_name)
        # A `/` in the name is one of two things, and only the family table tells them
        # apart: an author namespace on open weights (`huihui_ai/qwen3.5-abliterated:9b`,
        # which it resolves), or a vendor prefix upstream resolves itself
        # (`openai/gpt-4o`, which it does not). The thinking claim is an admission that
        # no table recognised the name, so it must not override a vendor's own answer --
        # LiteLLM is a proxy, and pointing it at a hosted vendor is its reason to exist.
        vendor_prefixed = family is None and "/" in model_name
        return merge_profile(
            LiteLLMProvider.model_profile(model_name),
            family,
            None if vendor_prefixed else _CLAIMS_THINKING_SUPPORT,
            _MERGES_SYSTEM_MESSAGES,
            _WITHHOLDS_STRICT_TOOL_DEFINITIONS,
        )


class InfomaniakProvider(OpenAIProvider):
    """Infomaniak's OpenAI-compatible AI service.

    OpenAI-compatible in protocol, but not in surface: it serves open-weight models
    under short slugs (`qwen3`, `llama3`, `mixtral`) that OpenAI's lookup table does not
    recognise, and it validates request fields strictly, answering `422
    validation_failed` for anything it does not know.

    `reasoning_effort` is measured, not assumed: against product 110572,
    `Qwen/Qwen3.5-122B-A10B-FP8` answers 200 to both `none` and `medium`, and `none`
    suppresses reasoning (269 completion tokens down to 4). Reasoning comes back on the
    `reasoning` field, which pydantic-ai already reads without a profile key.

    NOTE: `max_completion_tokens` stays withheld and is *not* measured. Published
    integrations whitelist `max_tokens` only, and a 422 on every request is a far worse
    failure than a cap that does not apply. Confirm against a real product_id before
    relaxing it.
    """

    @property
    def name(self) -> str:
        # Not inherited: `OpenAIProvider.name` is the literal `"openai"`, which would
        # label Infomaniak traffic as OpenAI in `ModelResponse.provider_name` and in
        # usage extraction, and would put pydantic-ai's `system == 'openai'` branches
        # (OpenAI's hard-coded embedding input limit, `tiktoken.encoding_for_model`) on
        # a service they know nothing about.
        return "infomaniak"

    @staticmethod
    def model_profile(model_name: str) -> ModelProfile | None:
        return merge_profile(
            # Layered over the base rather than replacing it: `OpenAIProvider` supplies
            # `json_schema_transformer`, without which structured output has no schema
            # rewriting at all.
            OpenAIProvider.model_profile(model_name),
            # The slugs are family names, so the same match that serves the self-hosted
            # services resolves them.
            _family_profile(model_name),
            _CLAIMS_THINKING_SUPPORT,
            _MERGES_SYSTEM_MESSAGES,
            _WITHHOLDS_STRICT_TOOL_DEFINITIONS,
            OpenAIModelProfile(openai_chat_supports_max_completion_tokens=False),
        )


def build_provider(client_settings: LLMClientSettings) -> Provider[AsyncOpenAI]:
    """Build the pydantic-ai provider for one LLM client setting.

    `timeout` has no equivalent on `Provider` or on `EmbeddingSettings`, so the
    `AsyncOpenAI` client is built here and injected -- which is also the only way to
    pass `base_url`/`api_key` together with a timeout, as the providers reject
    `openai_client` combined with either.
    """
    client = AsyncOpenAI(
        base_url=str(client_settings.endpoint),
        api_key=client_settings.api_key,
        timeout=client_settings.timeout,
    )

    match client_settings.provider:
        case LLMProvider.OLLAMA:
            return LoomOllamaProvider(openai_client=client)
        case LLMProvider.LITELLM:
            return LoomLiteLLMProvider(openai_client=client)
        case LLMProvider.INFOMANIAK:
            return InfomaniakProvider(openai_client=client)
        case LLMProvider.OPENAI:
            # Left as pydantic-ai ships it: hosted OpenAI is the one service whose model
            # names its own table knows, per model. Both a blanket thinking claim and a
            # prefix-matched family profile would replace that knowledge with a guess.
            return OpenAIProvider(openai_client=client)
        case _:
            assert_never(client_settings.provider)
