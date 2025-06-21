import copy
import logging
import re
from datetime import datetime, timedelta
from typing import Generator, List, Literal

from libretranslatepy import LibreTranslateAPI
from luqum.check import LuceneCheck
from luqum.exceptions import ParseError
from luqum.thread import parse
from luqum.tree import (
    AndOperation,
    FieldGroup,
    Group,
    Item,
    OrOperation,
    Phrase,
    Range,
    SearchField,
    UnknownOperation,
    Word,
)
from luqum.visitor import TreeTransformer
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# According to ElasticSearch:
# Units can be nanos, micros, ms (milliseconds),
# s (seconds), m (minutes), h (hours) and d (days).
# Also accepts "0" without a unit and "-1" to indicate an unspecified value.
KeepAlive = Literal["10s", "30m"]

# Default keepalive for point in time
DEFAULT_PIT_KEEPALIVE: KeepAlive = "10s"


class QueryBuilderException(Exception):
    """Base class for QueryBuilder exceptions."""


class RFTransformer(TreeTransformer):
    """RenameField Transformer:
    Allows renaming of certain fields of an already parsed query
    to multiple new field names with the logic operator OR."""

    def __init__(self, old_field_name: str, new_field_names: List[str]):
        super().__init__(track_parents=True)
        self.old_field_name = old_field_name
        self.new_field_names = new_field_names

    def has_leftmost_head(self, item: Item) -> bool:
        if item.head:
            return True
        if isinstance(item, Group) or not item.children:
            return False
        return self.has_leftmost_head(item.children[0])

    def has_rightmost_tail(self, item: Item) -> bool:
        if item.tail:
            return True
        if isinstance(item, Group) or not item.children:
            return False
        return self.has_rightmost_tail(item.children[-1])

    def clear_leftmost_head(self, item: Item):
        item.head = ""
        if isinstance(item, Group) or not item.children:
            return
        self.clear_leftmost_head(item.children[0])

    def clear_rightmost_tail(self, item: Item):
        item.tail = ""
        if isinstance(item, Group) or not item.children:
            return
        self.clear_rightmost_tail(item.children[-1])

    def visit_search_field(self, node: SearchField, context: dict):
        """If node.name matches old_field_name the node.expr is transformed to a
        OrOperation of all possible new fieldnames."""

        if node.name != self.old_field_name:
            yield from self.generic_visit(node, context)
            return

        if len(self.new_field_names) == 1:
            transformed_node = SearchField(
                self.new_field_names[0], copy.deepcopy(node.expr)
            )
        else:
            children = []
            # Create a new child node for every new field and clone its children
            for i, field_name in enumerate(self.new_field_names):
                child_node = SearchField(field_name, copy.deepcopy(node.expr))

                self.clear_leftmost_head(child_node)
                self.clear_rightmost_tail(child_node)
                if i == 0:
                    # first node: Add space to tail
                    child_node.tail = " "
                elif i == len(self.new_field_names) - 1:
                    # last node: Add space to head
                    child_node.head = " "
                else:
                    # else: add space to head and tail
                    child_node.head = " "
                    child_node.tail = " "
                children.append(child_node)

            transformed_node = Group(OrOperation(*children))

        if self.has_leftmost_head(node) and not self.has_leftmost_head(
            transformed_node
        ):
            transformed_node.head = " "

        if self.has_rightmost_tail(node) and not self.has_rightmost_tail(
            transformed_node
        ):
            transformed_node.tail = " "

        yield from self.generic_visit(transformed_node, context)


class OpTransformer(TreeTransformer):
    """Operator Transformer:
    Takes operators which have been parsed as Words cause
    they are not uppercase and makes them upper case"""

    def __init__(self):
        super().__init__(track_parents=True)
        self.ops = ["AND", "OR", "NOT"]

    def visit(self, tree: Item, context: dict | None = None) -> Item:
        """Overwriting visit to reparse the tree for the changes below to come into
        effect."""
        _tree = super().visit(tree, context)
        return parse(str(_tree))

    def visit_unknown_operation(self, node: UnknownOperation, context: dict):
        """Checks children of UnknownOperation for non-upper operators like AND/OR/NOT
        and makes them upper case.

        This process only modifies the literal of the Word object inside the
        UnknownOperation!
        """
        for i, child in enumerate(node.children):
            if isinstance(child, Word) and child.value.upper() in self.ops:
                node.children[i].value = child.value.upper()
        yield from self.generic_visit(node, context)


class TranslateTransformer(TreeTransformer):
    """Translate Transformer:
    Takes words or phrases and translates them to the languages passed"""

    MIN_TRANSLATION_LENGTH = 4

    def __init__(self, languages: list[str], translator: LibreTranslateAPI):
        super().__init__(track_parents=True)
        self._languages = languages
        self._translator = translator

    def _translate_node(self, node: Phrase) -> Generator[Group | Phrase, None, None]:
        if len(self._languages) <= 0:
            yield node
            return
        # phrases values must start and end with "
        node_value = node.value.strip('"')
        if len(node_value) < TranslateTransformer.MIN_TRANSLATION_LENGTH:
            yield node
            return
        translation_nodes = [node]
        for lang in self._languages:
            translation = self._translator.translate(node_value, "en", lang)
            translation_node = Phrase(f'"{translation}"')
            translation_nodes.append(translation_node)

        for i, translation_node in enumerate(translation_nodes):
            if i == 0:
                # first node: Add space to tail
                translation_node.tail = " "
            elif i == len(translation_nodes) - 1:
                # last node: Add space to head
                translation_node.head = " "
            else:
                # else: add space to head and tail
                translation_node.head = " "
                translation_node.tail = " "

        yield Group(OrOperation(*translation_nodes))

    def visit_range(self, node: Range, _: dict):
        """Do not translate Ranges."""
        yield node

    def visit_phrase(self, node: Phrase, _: dict):
        """Replace phrases with their translations."""
        yield from self._translate_node(node)

    def visit_word(self, node: Word, _: dict):
        """Replace words with their translations."""
        if len(self._languages) <= 0:
            yield node
            return
        if len(node.value) < TranslateTransformer.MIN_TRANSLATION_LENGTH:
            yield node
            return
        yield from self._translate_node(Phrase(f'"{node.value}"'))


class TimeTransformer(TreeTransformer):
    """Take words like today, yesterday...

    and replace them by real date values
    """

    def __init__(self, track_parents=False):
        super().__init__(track_parents=track_parents)

    def _to_start_of_day(self, ts: datetime) -> datetime:
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)

    def _to_start_of_month(self, ts: datetime) -> datetime:
        return ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _to_start_of_year(self, ts: datetime) -> datetime:
        return ts.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    def _format_datetime(self, ts: datetime) -> str:
        return ts.strftime("%Y-%m-%dT%H:%M:%S")

    def visit_word(self, node: Word, context: dict):
        """Replace words like today, yesterday...

        with real date values in ranges
        """
        keyword = node.value.upper()
        now = datetime.now()
        from_date: datetime
        to_date: datetime
        match keyword:
            case "TODAY":
                from_date = self._to_start_of_day(now)
                to_date = now
            case "YESTERDAY":
                from_date = self._to_start_of_day(now - timedelta(days=1))
                to_date = self._to_start_of_day(now)
            case "THISWEEK":
                from_date = self._to_start_of_day(now - timedelta(days=now.weekday()))
                to_date = now
            case "THISMONTH":
                from_date = self._to_start_of_month(now)
                to_date = now
            case "THISYEAR":
                from_date = self._to_start_of_year(now)
                to_date = now
            case _:
                yield from self.generic_visit(node, context)
                return

        start_word = Word(self._format_datetime(from_date))
        start_word.tail = " "
        stop_word = Word(self._format_datetime(to_date))
        stop_word.head = " "

        yield Range(start_word, stop_word)


class NumberTransformer(TreeTransformer):
    """Transforms numbers represented as words."""

    def visit_word(self, node: Word, context: dict):
        """Resolve unit prefixes to full numbers."""

        # Check if the word is a number with a unit prefix
        # which might start with a <, <=, >= or > sign
        number_regex = re.compile(r"^([<>]=?)?(\d+)([A-Za-z])$")
        if len(node.value) > 1 and number_regex.match(node.value):
            match = number_regex.match(node.value)
            if not match:
                yield from self.generic_visit(node, context)
                return
            value = int(match.group(2))
            unit = match.group(3).upper()
            match unit:
                case "T":
                    value *= 1_000_000_000_000
                case "G":
                    value *= 1_000_000_000
                case "M":
                    value *= 1_000_000
                case "K":
                    value *= 1_000
                case _:
                    yield from self.generic_visit(node, context)
                    return

            match = number_regex.match(node.value)
            if match:
                prefix = match.group(1)
            if not prefix:
                prefix = ""

            node.value = prefix + str(value)
            new_node = node.clone_item(value=prefix + str(value))
            yield new_node
        else:
            yield from self.generic_visit(node, context)


class NestedFieldTransformer(TreeTransformer):
    """Transform nested fields into a nested query like field.subfield:value into
    field:(subfield:value)"""

    def __init__(self):
        super().__init__(track_parents=True)

    def visit_search_field(self, node: SearchField, context: dict):
        """Apply transformation if field name contains a dot."""
        if "." in node.name:
            field_name = node.name.split(".", 1)[0]
            subfield_name = node.name.split(".", 1)[1]
            new_node = node.clone_item(name=field_name)

            # if the node is not the last child of its parent
            if "parents" in context and len(context["parents"]) > 0:
                parent = context["parents"][-1]
                if parent.children.index(node) < len(parent.children) - 1:
                    new_node.tail = " "

            new_node.expr = FieldGroup(SearchField(name=subfield_name, expr=node.expr))

            # set the tail of the object below
            # SearchField > FieldGroup > SearchField
            new_node.expr.expr.expr.tail = ""
            yield from self.generic_visit(new_node, context)
        else:
            yield from self.generic_visit(node, context)


class HiddenTransformer(TreeTransformer):
    """Hide files marked with hidden:true if not specified otherwise."""

    def __init__(self):
        super().__init__(track_parents=True)
        self.has_hidden_clause = False

    def visit(self, tree: Item, context: dict | None = None) -> Item:
        """Check if a searchfield with name hidden is present.

        Otherwise add hidden clause
        """
        self.has_hidden_clause = False
        _tree = super().visit(tree, context)

        if not self.has_hidden_clause:
            hidden_clause = SearchField(name="hidden", expr=Word("false"), head=" ")
            return AndOperation(Group(_tree, tail=" "), hidden_clause)
        return _tree

    def visit_search_field(self, node: SearchField, context: dict):
        """Check if any SearchField has the name hidden."""
        if node.name == "hidden":
            if "parents" not in context:
                self.has_hidden_clause = True
            elif all(
                not isinstance(parent, SearchField) for parent in context["parents"]
            ):
                self.has_hidden_clause = True
        yield from self.generic_visit(node, context)


class CustomLuceneCheck(LuceneCheck):
    """Temporary LuceneCheck class to add checks which are currently outstanding in the
    upstream project. After the fixes have been made the class can be removed and.

    the original LuceneCheck should be used again.
    - https://github.com/jurismarches/luqum/issues/92
    - https://github.com/jurismarches/luqum/issues/95
    """

    # This line allows the checker to also check Object fields.  This causes
    #   fields such as 'sha256' 'tika_meta.Content-Type' and
    #   'tika_meta.width' to all evaluate as valid field
    #   names.  Otherwise they would try to be evaluated as Nested field
    #   types, and fail the check.

    field_name_re = re.compile(r"^[-\w]+(\.[-\w]+)*$")

    def __init__(self, *args, **kwargs):
        """Adds the Range and FieldGroup to the list of allowed EXPRESSION_FIELDS."""
        super().__init__(*args, **kwargs)

        # pylint: disable=invalid-name
        self.FIELD_EXPR_FIELDS = tuple(
            list(self.SIMPLE_EXPR_FIELDS) + [FieldGroup, Range]
        )

    # pylint: disable=unused-argument
    def check_phrase(self, item: Phrase, context: dict):
        """Parser for phrase queries which does not exist in original LuceneCheck
        class."""
        if not item.value.endswith('"') or not item.value.startswith('"'):
            yield "Phrase value must start and end with double quote"


class QueryParameters(BaseModel):
    query_id: str = Field(min_length=1)
    keep_alive: KeepAlive = Field(default=DEFAULT_PIT_KEEPALIVE)
    search_string: str = Field(default="*", min_length=1)
    languages: list[str] = Field(default_factory=list)


class QueryBuilder:
    """Builds ES queries."""

    def __init__(self, translator: LibreTranslateAPI):
        self.translator = translator

    def parse_and_transform(self, query: QueryParameters) -> Item:
        """Takes query parameters, parses it into a query-tree and then transforms it.

        Args:
            query (QueryParams): the query parameters

        Raises:
            QueryBuilderException: Something is wrong with the
                                   search-string as-is

        Returns:
            Tree.Item: A query tree representing the query
                       in Lucene-tree form
        """
        try:
            tree = parse(query.search_string)
            tree = OpTransformer().visit(tree, {})
            tree = TimeTransformer().visit(tree, {})
            tree = NumberTransformer().visit(tree, {})
            tree = RFTransformer(
                "filename", [r"short_name", r"full_name", r"full_path"]
            ).visit(tree, {})
            tree = RFTransformer(
                "file_type",
                [
                    r"magic_file_type",
                    r"tika_file_type",
                ],
            ).visit(tree, {})
            tree = RFTransformer(
                "when",
                [
                    r"uploaded_datetime",
                    r"tika_meta.dcterms\:created",
                    r"tika_meta.dcterms\:modified",
                    r"tika_meta.pdf\:docinfo\:created",
                ],
            ).visit(tree, {})
            tree = RFTransformer(
                "author",
                [
                    r"tika_meta.dc\:creator",
                    r"tika_meta.Message\:From-Name",
                    r"tika_meta.meta\:last-author",
                ],
            ).visit(tree, {})
            tree = TranslateTransformer(query.languages, self.translator).visit(
                tree, {}
            )
            tree = HiddenTransformer().visit(tree, {})

        except ParseError as ex:
            raise QueryBuilderException(str(ex)) from ex

        return tree

    def build(self, query: QueryParameters) -> str:
        """Uses the provided search object to build."""
        search_string = str(self.parse_and_transform(query))

        logger.info(
            "Query '%s' was transformed to '%s'", query.search_string, search_string
        )

        return search_string
