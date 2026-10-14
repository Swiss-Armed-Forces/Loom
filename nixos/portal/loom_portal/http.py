"""The request and the response, as values.

`server.py` is the only module that touches a socket. Everything else is written against
these two types, so `Portal.handle` is a pure function of a `Request` and the files it was
given -- which is what lets the suite drive the whole application without binding a port.

The form parser returns a `FormFields`, not a dict, and the headers are a list of `Header`
rather than a mapping. That is the repository's rule about named types applied to the one
place where a dict is the obvious shape: a caller reading `fields.get("password")` cannot
mistake which half of a pair it has, and a response can carry the same header name twice.
"""

from dataclasses import dataclass, field
from typing import NamedTuple
from urllib.parse import parse_qsl

# A form the page submits is a password and at most two short words. Anything larger is
# not a mistake somebody made in a browser, and nginx caps the body at 4k as well -- this
# is the second half of that, for the case where something dials the loopback port
# directly.
MAX_FORM_BYTES = 4096


class Header(NamedTuple):
    name: str
    value: str


@dataclass(frozen=True)
class Request:
    """What arrived, with the path already split from the query."""

    method: str
    path: str
    query: str = ""
    body: bytes = b""
    headers: list[Header] = field(default_factory=list)

    def header(self, name: str, default: str = "") -> str:
        """One header, matched case-insensitively as HTTP requires."""
        wanted = name.lower()
        for entry in self.headers:
            if entry.name.lower() == wanted:
                return entry.value
        return default


@dataclass(frozen=True)
class Response:
    status: int
    headers: list[Header] = field(default_factory=list)
    body: bytes = b""


@dataclass(frozen=True)
class FormFields:
    """A parsed form body.

    Deliberately a list rather than a dict: a repeated field is kept rather than silently
    collapsed, and `get` states which one wins.
    """

    fields: list[Header] = field(default_factory=list)

    def get(self, name: str, default: str = "") -> str:
        """The first value for that name, or `default`."""
        for entry in self.fields:
            if entry.name == name:
                return entry.value
        return default


def parse_form(body: bytes) -> FormFields:
    """An `application/x-www-form-urlencoded` body.

    Never raises. A body that is not a form, or not UTF-8, yields no fields, and the
    caller then finds no password and refuses -- which is the same answer a wrong
    password gets, and the right one for a request nobody's browser sent.
    """
    if len(body) > MAX_FORM_BYTES:
        return FormFields()
    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError:
        return FormFields()
    return FormFields([Header(name, value) for name, value in parse_qsl(decoded)])


def no_store(headers: list[Header]) -> list[Header]:
    """Add the header every answer on this listener carries but the logo.

    The page states today's password prompt, a fingerprint and -- once -- a private key.
    None of it may sit in a shared cache, and a captive-portal webview is exactly the
    kind of client that keeps things longer than anyone expects.
    """
    return [*headers, Header("Cache-Control", "no-store")]


def html(markup: str, status: int = 200) -> Response:
    return Response(
        status=status,
        headers=no_store([Header("Content-Type", "text/html; charset=utf-8")]),
        body=markup.encode("utf-8"),
    )


def text(body: str, status: int = 200) -> Response:
    return Response(
        status=status,
        headers=no_store([Header("Content-Type", "text/plain; charset=utf-8")]),
        body=body.encode("utf-8"),
    )


def attachment(payload: bytes, filename: str, content_type: str) -> Response:
    return Response(
        status=200,
        headers=no_store(
            [
                Header("Content-Type", content_type),
                Header("Content-Disposition", f'attachment; filename="{filename}"'),
                Header("Content-Length", str(len(payload))),
            ]
        ),
        body=payload,
    )


def redirect(location: str, status: int = 303) -> Response:
    return Response(status=status, headers=no_store([Header("Location", location)]))
