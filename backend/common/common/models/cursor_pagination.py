import hashlib
from typing import (
    Any,
    Literal,
)

from pydantic import BaseModel, model_validator

CursorSource = Literal[
    "execute_query",
    "flat_files",
    "list_folder_contents",
]

_CURSOR_DIGEST_SEPARATOR = "\x1f"
_CURSOR_DIGEST_LENGTH = 16


class InvalidPaginationCursorError(ValueError):
    """Raised when a pagination cursor does not belong to the search being run."""

    MESSAGE = (
        "Invalid pagination cursor. Pass back the exact cursor returned "
        "by the previous page, or omit it to start from the first page."
    )

    # The message is an argument so that the exception survives the pickle
    # round-trip Celery does when re-raising it in the caller.
    def __init__(self, message: str = MESSAGE) -> None:
        super().__init__(message)


def _is_valid_sort_value(value: Any) -> bool:
    """Whether ES would accept the value inside a ``search_after`` tuple.

    ``None`` is accepted: ES returns null in the sort array for a document missing the
    sort field, and takes it back in ``search_after`` — rejecting it here would wedge
    paging permanently at such a document.  ``bool`` is rejected explicitly because
    ``isinstance(True, int)`` is True, and ES answers a boolean sort value with an
    opaque error.
    """
    if isinstance(value, bool):
        return False
    return value is None or isinstance(value, (int, float, str))


class SearchAfterCursor(BaseModel):
    """Opaque cursor for search_after based pagination.

    Attributes:
        src: Identifies the search that produced the cursor.  Every producer
            sorts on a different tuple, so a cursor handed to the wrong search
            would otherwise be applied to an unrelated sort and return a
            plausible but wrong page instead of an error.
        last_sort: ES sort values of the last hit of the previous page.
        pit: Point-in-time id the previous page was read against.  Carried in
            the cursor so that every page of a run sees the same index
            snapshot instead of a fresh one.  ``None`` for searches that do
            not use a point-in-time.
        query_digest: Digest of the inputs defining the result set.  Without it
            nothing ties a cursor to its query, and replaying it against a
            different one silently pages through the wrong results.
    """

    src: CursorSource
    last_sort: list[Any]
    pit: str | None = None
    query_digest: str | None = None

    @staticmethod
    def digest(*parts: str) -> str:
        """Digest the inputs that define a result set, to bind a cursor to them."""
        joined = _CURSOR_DIGEST_SEPARATOR.join(parts)
        return hashlib.sha256(joined.encode()).hexdigest()[:_CURSOR_DIGEST_LENGTH]

    @model_validator(mode="after")
    def _sort_values_are_usable(self) -> "SearchAfterCursor":
        """Reject a sort tuple Elasticsearch would not take back.

        Guards every way into the type — the REST body, the agent's handle store and the
        Celery round-trip alike — because ``last_sort`` is typed ``list[Any]`` and
        nothing else constrains what lands in it.  An empty tuple resumes nothing, and a
        value of the wrong type is answered by ES with an opaque error rather than
        something a caller can act on.
        """
        if not self.last_sort:
            raise InvalidPaginationCursorError()
        if not all(_is_valid_sort_value(value) for value in self.last_sort):
            raise InvalidPaginationCursorError()
        return self

    def validate_for(
        self,
        *,
        expected_src: CursorSource,
        expected_digest: str | None = None,
    ) -> None:
        """Assert this cursor was minted for the search that is about to run.

        Applies to cursors handed over as objects just as much as to parsed ones: a
        cursor the agent passed to the wrong tool arrives intact, and is only wrong
        in relation to the search it is being applied to.

        Args:
            expected_src: The producer the cursor has to belong to.
            expected_digest: When given, the digest the cursor has to carry.

        Raises:
            InvalidPaginationCursorError: The cursor was not produced by this
                search, or does not belong to this query.
        """
        if self.src != expected_src:
            raise InvalidPaginationCursorError()
        if expected_digest is not None and self.query_digest != expected_digest:
            raise InvalidPaginationCursorError()
