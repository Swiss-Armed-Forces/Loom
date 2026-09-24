"""Sanitization of untrusted document text before it reaches a prompt."""

_SANITIZATION_REPLACEMENTS: list[tuple[str, str]] = [
    # Separator sequence that spoofs the prompt boundary used in legacy prompts
    ("--------------------", "- - - - - - - - - -"),
    # XML tags used to delimit the document region — escaping these prevents
    # a crafted document from breaking out of the <document>...</document> wrapper
    ("</document>", "<\\/document>"),
    ("<document>", "<document\\/>"),
    # ChatML role-boundary tokens (used by Qwen, Mistral, OpenHermes, etc.)
    ("<|im_start|>", "< | im_start | >"),
    ("<|im_end|>", "< | im_end | >"),
    # Llama / Mistral instruction tokens
    ("[INST]", "[ INST ]"),
    ("[/INST]", "[ /INST ]"),
    # Llama 3 special tokens
    ("<|begin_of_text|>", "< | begin_of_text | >"),
    ("<|end_of_text|>", "< | end_of_text | >"),
    ("<|start_header_id|>", "< | start_header_id | >"),
    ("<|end_header_id|>", "< | end_header_id | >"),
    ("<|eot_id|>", "< | eot_id | >"),
]


def sanitize_document_text(text: str) -> str:
    """Sanitize document text to prevent prompt injection.

    Replaces separator sequences and model-specific boundary tokens that could spoof
    prompt structure or escape the document delimiter region.
    """
    for needle, replacement in _SANITIZATION_REPLACEMENTS:
        text = text.replace(needle, replacement)
    return text
