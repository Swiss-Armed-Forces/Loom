from common.utils.lucene import escape_lucene_phrase, escape_lucene_regexp


def test_escape_lucene_regexp_escapes_what_python_does_not():
    """`"`, `@`, `<` and `>` are Lucene metacharacters and not Python ones, so a Python
    escaper leaves exactly these four for Elasticsearch to reject."""
    assert escape_lucene_regexp('a"b@c<d>e') == 'a\\"b\\@c\\<d\\>e'


def test_escape_lucene_regexp_leaves_alphanumerics_bare():
    """Lucene rejects a backslash before a letter with "invalid character class", so
    escaping cannot simply be applied to every character."""
    assert escape_lucene_regexp("loom0") == "loom0"


def test_escape_lucene_phrase_escapes_quote_and_backslash_once_each():
    """Per-character escaping, so the backslash added for a quote is not itself escaped
    and the quote stays neutralised."""
    assert escape_lucene_phrase('a"b\\c') == 'a\\"b\\\\c'
