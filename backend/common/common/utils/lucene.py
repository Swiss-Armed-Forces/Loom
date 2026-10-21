"""Escaping for the Lucene grammars Elasticsearch parses on our behalf."""

# A terms aggregation's `include` is parsed as a Lucene RegExp, where `"` opens a
# quoted literal, `<` a numeric range and `@` matches any string. A backslash makes
# any of these literal, but a backslash before a letter is rejected outright
# ("invalid character class"), so only these characters may be escaped.
LUCENE_REGEXP_METACHARACTERS = frozenset('.?+*|{}[]()"\\#@&<>~')

# Inside a double-quoted phrase these two are the only characters that end the token.
LUCENE_PHRASE_METACHARACTERS = frozenset('"\\')


def escape_lucene_regexp(value: str) -> str:
    """Return a Lucene RegExp that matches ``value`` literally."""
    return "".join(
        f"\\{character}" if character in LUCENE_REGEXP_METACHARACTERS else character
        for character in value
    )


def escape_lucene_phrase(value: str) -> str:
    """Return ``value`` safe to place between the quotes of a Lucene phrase."""
    return "".join(
        f"\\{character}" if character in LUCENE_PHRASE_METACHARACTERS else character
        for character in value
    )
