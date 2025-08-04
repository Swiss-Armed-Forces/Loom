"""Tests for all Transformer classes in query_builder.py."""

from freezegun import freeze_time
from luqum.thread import parse

from common.dependencies import get_libretranslate_api
from common.services.query_builder import (
    CustomLuceneCheck,
    HiddenTransformer,
    NestedFieldTransformer,
    NumberTransformer,
    OpTransformer,
    QueryBuilder,
    QueryBuilderException,
    QueryParameters,
    RFTransformer,
    TimeTransformer,
    TranslateTransformer,
)


def get_checker():
    return CustomLuceneCheck(zeal=1)


def test_rftransformer_simple1():
    """Check simple renaming of field."""
    search_string = "alpha:value"
    result = str(RFTransformer("alpha", ["omega"]).visit(parse(search_string)))
    assert result == "omega:value"


def test_rftransformer_simple2():
    """Check simple renaming of field."""
    search_string = "alpha:value OR beta:value"
    result = str(RFTransformer("alpha", ["omega"]).visit(parse(search_string)))
    assert result == "omega:value OR beta:value"


def test_rftransformer_simple3():
    """Check renaming with multiple replacements."""
    search_string = "alpha:value"
    result = str(RFTransformer("alpha", ["psi", "omega"]).visit(parse(search_string)))
    assert result == "(psi:value OR omega:value)"


def test_rftransformer_simple4():
    """Check renaming with multiple replacements."""
    search_string = "alpha:value"
    result = str(
        RFTransformer("alpha", ["psi", "omega", "tau"]).visit(parse(search_string))
    )
    assert result == "(psi:value OR omega:value OR tau:value)"


def test_rftransformer_nested1():
    """Check nested property with rftransformer."""
    search_string = "(alpha:value AND beta) AND gamma"
    result = str(RFTransformer("alpha", ["psi", "omega"]).visit(parse(search_string)))
    assert result == "((psi:value OR omega:value) AND beta) AND gamma"


def test_rftransformer_nested2():
    """Check 2 level nested property with rftransformer."""
    search_string = "((alpha:value OR delta) AND beta) AND gamma"
    result = str(RFTransformer("alpha", ["psi", "omega"]).visit(parse(search_string)))
    # noqa: E501
    assert result == "(((psi:value OR omega:value) OR delta) AND beta) AND gamma"


def test_rftransformer_multiple():
    """Check rftransformer with multiple occurrences of target field."""
    search_string = "alpha:value1 AND alpha:value2"
    result = str(RFTransformer("alpha", ["omega"]).visit(parse(search_string)))
    assert result == "omega:value1 AND omega:value2"


def test_rftransformer_complex_values1():
    """Check rftransformer with multiple occurrences of target field."""
    search_string = "alpha:(value1 OR value2)"
    result = str(RFTransformer("alpha", ["omega"]).visit(parse(search_string)))
    assert result == "omega:(value1 OR value2)"


def test_rftransformer_complex_values2():
    """Check rftransformer with multiple occurrences of target field."""
    search_string = "alpha:(value1 OR value2)"
    result = str(
        RFTransformer(
            "alpha",
            [
                "psi",
                "omega",
            ],
        ).visit(parse(search_string))
    )
    assert result == "(psi:(value1 OR value2) OR omega:(value1 OR value2))"


def test_rftransformer_complex_values3():
    """Check rftransformer with multiple occurrences of target field."""
    search_string = "(filename:1.txt) OR filename:2.txt"
    result = str(
        RFTransformer(
            "filename",
            [
                "file",
                "name",
            ],
        ).visit(parse(search_string))
    )
    assert result == "((file:1.txt OR name:1.txt)) OR (file:2.txt OR name:2.txt)"


def test_optransformer_simple_and():
    """Check simple case of lower case and."""
    search_string = "value1 and value2"
    result = str(OpTransformer().visit(parse(search_string)))
    assert result == "value1 AND value2"


def test_optransformer_simple_or():
    """Check simple case of lower case "or"."""
    search_string = "value1 or value2"
    result = str(OpTransformer().visit(parse(search_string)))
    assert result == "value1 OR value2"


def test_optransformer_simple_not():
    """Check simple case of lower case "not"."""
    search_string = "not value2"
    result = str(OpTransformer().visit(parse(search_string)))
    assert result == "NOT value2"


def test_optransformer_advanced2_not():
    """Check nested case of lower case "not"."""
    search_string = "not not value2"
    result = str(OpTransformer().visit(parse(search_string)))
    assert result == "NOT NOT value2"


def test_optransformer_advanced3_not():
    """Check nested case of lower case "not"."""
    search_string = "nOT (Not value2)"  # spellchecker:disable-line
    result = str(OpTransformer().visit(parse(search_string)))
    assert result == "NOT (NOT value2)"


def test_numbertransformer_simple1():
    """Check simple case of unit prefixes."""
    search_string = "size:100K"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:100000"

    search_string = "size:100M"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:100000000"


def test_numbertransformer_simple2():
    """Check simple case of unit prefixes in lower case."""
    search_string = "size:100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:100000"

    search_string = "size:100m"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:100000000"


def test_numbertransformer_compare1():
    """Check simple case of units with prefixes like >, <, >=, <="""
    search_string = "size:>100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:>100000"

    search_string = "size:<=100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:<=100000"

    search_string = "size:>100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:>100000"

    search_string = "size:>=100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:>=100000"


def test_numbertransformer_wrong1():
    """Check test for invalid syntax with units."""
    search_string = "size:100kk"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:100kk"

    search_string = "size:2ek"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:2ek"

    search_string = "size:10e"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:10e"


def test_numbertransformer_wrong2():
    """Check test for invalid syntax with invalid prefixes."""
    search_string = "size:=>100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:=>100k"

    search_string = "size:=100k"
    result = str(NumberTransformer().visit(parse(search_string)))
    assert result == "size:=100k"


@freeze_time("2022-08-27T17:42:30")
def test_timetransformer_today():
    """Check for correct range translation using TODAY."""
    search_string = "upload:TODAY"
    result = TimeTransformer().visit(parse(search_string))
    assert str(result) == "upload:[2022-08-27T00:00:00 TO 2022-08-27T17:42:30]"


@freeze_time("2022-08-27T17:42:30")
def test_timetransformer_yesterday():
    """Check for correct range translation using YESTERDAY."""
    search_string = "upload:YESTERDAY"
    result = TimeTransformer().visit(parse(search_string))
    assert str(result) == "upload:[2022-08-26T00:00:00 TO 2022-08-27T00:00:00]"


@freeze_time("2022-08-27T17:42:30")
def test_timetransformer_thisweek():
    """ " check for correct range translation using THISWEEK."""
    search_string = "upload:THISWEEK"
    result = TimeTransformer().visit(parse(search_string))
    assert str(result) == "upload:[2022-08-22T00:00:00 TO 2022-08-27T17:42:30]"


@freeze_time("2022-08-27T17:42:30")
def test_timetransformer_thismonth():
    """ " check for correct range translation using THISMONTH."""
    search_string = "upload:THISMONTH"
    result = TimeTransformer().visit(parse(search_string))
    assert str(result) == "upload:[2022-08-01T00:00:00 TO 2022-08-27T17:42:30]"


@freeze_time("2022-08-27T17:42:30")
def test_timetransformer_thisyear():
    """ " check for correct range translation using THISYEAR."""
    search_string = "upload:THISYEAR"
    result = TimeTransformer().visit(parse(search_string))
    assert str(result) == "upload:[2022-01-01T00:00:00 TO 2022-08-27T17:42:30]"


@freeze_time("2022-08-27T17:42:30")
def test_hiddentransformer_simple1():
    """Test if hidden:false is added if field hidden is not present."""
    search_string = "alpha:beta"
    result = str(HiddenTransformer().visit(parse(search_string)))
    assert result == "(alpha:beta) AND hidden:false"


def test_hiddentransformer_simple2():
    """Test if nothing is changed if field hidden is present."""
    search_string = "hidden:true"
    result = str(HiddenTransformer().visit(parse(search_string)))
    assert result == "hidden:true"


def test_hiddentransformer_nested1():
    """Test if hidden:false is added the hidden is only part of a nested query and as a
    standalone field."""
    search_string = "hidden.alpha:true"
    result = str(HiddenTransformer().visit(parse(search_string)))
    assert result == "(hidden.alpha:true) AND hidden:false"


def test_hiddentransformer_nested2():
    """Test if hidden:false is added the hidden is only part of a nested query and as a
    standalone field."""
    search_string = "alpha:(hidden:true)"
    result = str(HiddenTransformer().visit(parse(search_string)))
    assert result == "(alpha:(hidden:true)) AND hidden:false"


def test_hiddentransformer_group1():
    """Test if nothing is changed because hidden is part of a group."""
    search_string = "(alpha:beta OR hidden:true)"
    result = str(HiddenTransformer().visit(parse(search_string)))
    assert result == "(alpha:beta OR hidden:true)"


def test_nestedfieldstransformer_simple1():
    """Test if a 2.-level nested field is transformed."""
    search_string = "alpha.beta:gamma"
    result = str(NestedFieldTransformer().visit(parse(search_string)))
    assert result == "alpha:(beta:gamma)"


def test_nestedfieldstransformer_simple2():
    """Test if a 3.-level nested field is transformed."""
    search_string = "alpha.beta.gamma:delta"
    result = str(NestedFieldTransformer().visit(parse(search_string)))
    assert result == "alpha:(beta:(gamma:delta))"


def test_nestedfieldstransformer_group1():
    """Test if a nested field inside a group is transformed."""
    search_string = "(alpha.beta:gamma)"
    result = str(NestedFieldTransformer().visit(parse(search_string)))
    assert result == "(alpha:(beta:gamma))"


def test_nestedfieldstransformer_group2():
    """Test if a nested field inside a group is transformed."""
    search_string = "(alpha.beta:gamma OR delta.zetta:omega)"
    result = str(NestedFieldTransformer().visit(parse(search_string)))
    assert result == "(alpha:(beta:gamma) OR delta:(zetta:omega))"


def test_translationtransformer_star():
    """Test translation of *"""
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.return_value = "something"

    search_string = "*"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == "*"


def test_translationtransformer_starfield():
    """Test translation of * in a field."""
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.return_value = "something"

    search_string = "field:*"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == "field:*"


def test_translationtransformer_simple1():
    """Test translation of field search."""
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.return_value = "datei"

    search_string = "filename:file"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == 'filename:("file" OR "datei")'
    assert libretranslate_api.translate.call_args.args[0] == "file"
    assert libretranslate_api.translate.call_args.args[2] == "de"


def test_translationtransformer_simple2():
    """Test translation of nested field search."""
    libretranslate_api = get_libretranslate_api()
    libretranslate_api.translate.return_value = "datei"

    search_string = "alpha.beta.gamma:file"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == 'alpha.beta.gamma:("file" OR "datei")'
    assert libretranslate_api.translate.call_args.args[0] == "file"
    assert libretranslate_api.translate.call_args.args[2] == "de"


def test_translationtransformer_group1():
    """Test translation of groups."""
    libretranslate_api = get_libretranslate_api()

    def side_effect(*args, **_):
        if args[0] == "file":
            return "datei"
        return "haus"

    libretranslate_api.translate.side_effect = side_effect

    search_string = "filename:(file OR house)"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == 'filename:(("file" OR "datei")OR("house" OR "haus"))'


def test_translationtransformer_group2():
    """Test translation of groups."""
    libretranslate_api = get_libretranslate_api()

    def side_effect(*args, **_):
        if args[0] == "file":
            return "datei"
        return "haus"

    libretranslate_api.translate.side_effect = side_effect

    search_string = "(file AND house)"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )
    assert result == '(("file" OR "datei")AND("house" OR "haus"))'


def test_translationtransformer_range():
    """Test translation of ranges."""
    libretranslate_api = get_libretranslate_api()

    def side_effect(*args, **_):
        if args[0] == "file":
            return "datei"
        return "haus"

    libretranslate_api.translate.side_effect = side_effect

    search_string = "[file TO datei]"
    result = str(
        TranslateTransformer(["de"], libretranslate_api).visit(parse(search_string))
    )

    assert result == "[file TO datei]"


def test_translationtransformer_multi_language():
    """Test translation with multiple languages."""
    libretranslate_api = get_libretranslate_api()

    def side_effect(*args, **_):
        if args[2] == "de":
            if args[0] == "file":
                return "datei"
            return "haus"
        if args[0] == "file":
            return "fichier"
        return "maison"

    libretranslate_api.translate.side_effect = side_effect

    search_string = "(file AND house)"
    result = str(
        TranslateTransformer(["de", "fr"], libretranslate_api).visit(
            parse(search_string)
        )
    )
    assert (
        result == '(("file" OR "datei" OR "fichier")AND("house" OR "haus" OR "maison"))'
    )


def test_translationtransformer_no_language():
    """Test translation with no language."""
    search_string = "file"
    result = str(
        TranslateTransformer([], get_libretranslate_api()).visit(parse(search_string))
    )
    assert result == "file"


def test_query_builder_simple_and():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: simple AND connection
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha:value and beta:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == "(alpha:value AND beta:value) AND hidden:false"


def test_query_builder_simple_or():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: simple OR connection
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha:value or beta:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == "(alpha:value OR beta:value) AND hidden:false"


def test_query_builder_subfield():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: double sub-field
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha.beta.gamma:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == "(alpha.beta.gamma:value) AND hidden:false"


def test_query_builder_dashed_field():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: double sub-field
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha-beta:value")
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == "(alpha-beta:value) AND hidden:false"


def test_query_builder_phrases():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: double sub-field
    """
    query = QueryParameters(
        query_id="0123456789", search_string="hello and hidden:true"
    )
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == "hello AND hidden:true"


def test_query_builder_show_hidden():
    """Test if the QueryBuilder build() function builds the correct queries for the
    elasticsearch backend.

    Case: double sub-field
    """
    query = QueryParameters(
        query_id="0123456789", search_string='"hello and world" and foo'
    )
    builder = QueryBuilder(get_libretranslate_api())
    result = builder.build(query)
    assert result == '("hello and world" AND foo) AND hidden:false'


def test_lucene_checker_simple():
    """Test to ensure the lucene checker validates queries correctly.

    Case: simple positive
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha:value")
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_simple_quoted():
    """Test to ensure the lucene checker validates queries correctly.

    Case: quoted value
    """
    query = QueryParameters(query_id="0123456789", search_string='alpha:"value"')
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_simple_and():
    """Test to ensure the lucene checker validates queries correctly.

    Case: simple and
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha:value AND beta:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_simple_or():
    """Test to ensure the lucene checker validates queries correctly.

    Case: simple or
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha:value OR beta:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_dashed_field():
    """Test to ensure the lucene checker validates queries correctly.

    Case: simple or
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha-beta:value")
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_single_subfield():
    """Test to ensure the lucene checker validates queries correctly.

    Case: single-nested values
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha.beta:value")
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_double_subfield():
    """Test to ensure the lucene checker validates queries correctly.

    Case: double-nested value
    """
    query = QueryParameters(
        query_id="0123456789", search_string="alpha.beta.gamma:value"
    )
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_nested_subfield():
    """Test to ensure the lucene checker validates queries correctly.

    Case: nested query with quoted value
    """
    query = QueryParameters(
        query_id="0123456789",
        search_string=(
            'alpha.beta.gamma:value AND epsilon.sigma:"quoted_value" AND'
            " delta:normal_value"
        ),
    )
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    tree = builder.parse_and_transform(query)
    assert check(tree)


def test_lucene_checker_mismatched_quote():
    """Test to ensure the lucene checker validates queries correctly.

    Case: extra/mismatched quote
    """
    query = QueryParameters(query_id="0123456789", search_string='alpha:"value')
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    try:
        tree = builder.parse_and_transform(query)
        assert not check(tree)
    except QueryBuilderException as ex:
        assert "Illegal character" in str(ex)


def test_lucene_checker_bad_colon():
    """Test to ensure the lucene checker validates queries correctly.

    Case: bad/extra colon
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha::value")
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    try:
        tree = builder.parse_and_transform(query)
        assert not check(tree)
    except QueryBuilderException as ex:
        assert "unexpected  ':' at" in str(ex)


def test_lucene_checker_bad_sub_field():
    """Test to ensure the lucene checker validates queries correctly.

    Case: bad/extra colon
    """
    query = QueryParameters(query_id="0123456789", search_string="alpha:beta:value")
    builder = QueryBuilder(get_libretranslate_api())
    check = get_checker()
    try:
        tree = builder.parse_and_transform(query)
        assert not check(tree)
    except QueryBuilderException as ex:
        assert "unexpected  ':' at" in str(ex)


# def test_lucene_checker_unknown_operation():
#     """
#     Test to ensure the lucene checker validates queries correctly.
#     Case: unknown operation
#     """
#     query = QueryParameters(query_id="0123456789", search_string="alpha:value ORS beta:value")
#     builder = get_query_builder()
#     check = get_checker()
#     tree = builder.parse_and_transform(query)
#     assert not check(tree)
