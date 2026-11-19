"""Tests for `cicd/gitlab_client.py`.

The client exists because `curl` could not tell these cases apart: without `--fail` it
exits 0 on a 401, so an expired token was reported as a GitLab profile missing its name.
What is checked here is the classification, and that a request carries what GitLab
needs.

The seam is the injected opener, so none of this opens a socket.
"""

from __future__ import annotations

import io
import json
import socket
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

import pytest

from setup_devenv.gitlab import (
    Failure,
    GitLabClient,
    GitLabError,
    NoRedirects,
    fingerprint_of,
)


class FakeResponse(io.BytesIO):
    """Just enough of an HTTP response for the client to read."""

    def __init__(self, payload: Any, charset: str = "utf-8") -> None:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        super().__init__(body.encode(charset))
        self.headers = _Headers(charset)

    def __enter__(self) -> "FakeResponse":
        """Support the `with` the client uses."""
        return self

    def __exit__(self, *_: object) -> None:
        """Close on the way out."""
        self.close()


class _Headers:
    """The one header lookup the client makes."""

    def __init__(self, charset: str) -> None:
        self.charset = charset

    def get_content_charset(self, default: str) -> str:
        """The body's charset."""
        return self.charset or default


class FakeOpener:
    """Replays a scripted reply and records the request that asked for it."""

    def __init__(self, reply: Any) -> None:
        self.reply = reply
        self.requests: List[urllib.request.Request] = []
        self.timeouts: List[Optional[float]] = []

    def open(self, request: urllib.request.Request, timeout: Optional[float] = None):
        """Record the request, then raise or return the scripted reply."""
        self.requests.append(request)
        self.timeouts.append(timeout)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def client_for(reply: Any) -> GitLabClient:
    """A client wired to a scripted reply."""
    return GitLabClient(token="glpat-x", opener=FakeOpener(reply))  # type: ignore[arg-type]


def http_error(code: int, body: Any) -> urllib.error.HTTPError:
    """An HTTPError carrying a readable body, as urllib produces."""
    encoded = body if isinstance(body, str) else json.dumps(body)
    return urllib.error.HTTPError(
        "https://gitlab.com/api/v4/user",
        code,
        "boom",
        {},  # type: ignore[arg-type]
        io.BytesIO(encoded.encode("utf-8")),
    )


#
# Classification -- the reason this module exists
#


def test_a_401_is_an_expired_token_not_a_missing_profile() -> None:
    """`curl` exits 0 here, which is how this became a profile complaint."""
    client = client_for(http_error(401, {"message": "401 Unauthorized"}))
    with pytest.raises(GitLabError) as excinfo:
        client.fetch_user()

    assert excinfo.value.failure is Failure.AUTH
    assert excinfo.value.status == 401


def test_a_403_names_the_scope_the_token_is_missing() -> None:
    """A valid token without `api` fails differently from an invalid one."""
    client = client_for(http_error(403, {"message": "403 Forbidden"}))
    with pytest.raises(GitLabError) as excinfo:
        client.fetch_user()

    assert excinfo.value.failure is Failure.FORBIDDEN
    assert "api" in excinfo.value.detail


def test_an_unreachable_network_is_not_an_auth_failure() -> None:
    """HTTPError subclasses URLError; catching them the wrong way round collapses every
    status into "cannot reach gitlab.com"."""
    client = client_for(urllib.error.URLError(socket.gaierror("no such host")))
    with pytest.raises(GitLabError) as excinfo:
        client.fetch_user()

    assert excinfo.value.failure is Failure.NETWORK


def test_a_body_that_is_not_json_is_malformed_not_empty() -> None:
    """A proxy's HTML error page used to parse as a user with no name."""
    client = client_for(FakeResponse("<html>gateway</html>"))
    with pytest.raises(GitLabError) as excinfo:
        client.fetch_user()

    assert excinfo.value.failure is Failure.MALFORMED


def test_gitlabs_own_explanation_survives_a_nested_message() -> None:
    """GitLab answers field errors as {"message": {"field": ["reason"]}}."""
    client = client_for(
        http_error(400, {"message": {"fingerprint": ["has already been taken"]}})
    )
    with pytest.raises(GitLabError) as excinfo:
        client.upload_ssh_key("t", "ssh-ed25519 AAAA x")

    assert excinfo.value.failure is Failure.CONFLICT
    assert "has already been taken" in excinfo.value.detail


#
# What goes on the wire
#


def test_a_request_carries_the_token_and_a_timeout() -> None:
    """Urlopen blocks forever without one, and no linter here checks for it."""
    opener = FakeOpener(
        FakeResponse({"name": "Ada", "username": "ada", "email": "a@b"})
    )
    GitLabClient(token="glpat-secret", opener=opener).fetch_user()  # type: ignore[arg-type]

    assert len(opener.requests) == 1
    request = opener.requests[0]
    # urllib title-cases header names on the way in.
    assert request.get_header("Private-token") == "glpat-secret"
    assert opener.timeouts == [pytest.approx(15.0)]


def test_uploading_a_key_sends_real_json() -> None:
    """The shell this replaces interpolated inside single quotes, so GitLab received the
    literal strings `$TITLE` and `$KEY_CONTENT`."""
    opener = FakeOpener(
        FakeResponse({"id": 7, "title": "t", "key": "ssh-ed25519 AAAA x"})
    )
    client = GitLabClient(token="glpat-x", opener=opener)  # type: ignore[arg-type]
    client.upload_ssh_key("loom-dev@box", "ssh-ed25519 AAAA x")

    assert len(opener.requests) == 1
    request = opener.requests[0]
    assert isinstance(request.data, bytes)
    sent: Dict[str, Any] = json.loads(request.data.decode("utf-8"))
    assert sent == {
        "title": "loom-dev@box",
        "key": "ssh-ed25519 AAAA x",
        "usage_type": "auth_and_signing",
    }
    assert request.get_header("Content-type") == "application/json"


def test_a_token_is_never_an_argument_vector() -> None:
    """The point of urllib over curl: /proc/<pid>/cmdline is world-readable."""
    opener = FakeOpener(
        FakeResponse({"name": "Ada", "username": "ada", "email": "a@b"})
    )
    GitLabClient(token="glpat-secret", opener=opener).fetch_user()  # type: ignore[arg-type]

    assert len(opener.requests) == 1
    request = opener.requests[0]
    assert "glpat-secret" not in request.full_url


def test_a_redirect_is_refused_rather_than_followed() -> None:
    """HTTPRedirectHandler copies PRIVATE-TOKEN onto the request it redirects to."""
    request = urllib.request.Request("https://gitlab.com/api/v4/user")
    handler = NoRedirects()
    assert (
        handler.redirect_request(
            request, io.BytesIO(b""), 302, "Found", {}, "https://evil.example/steal"
        )
        is None
    )


#
# Fingerprints
#


def test_fingerprint_matches_what_ssh_keygen_prints() -> None:
    """Computed here rather than by shelling out to ssh-keygen per key."""
    key = (
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEa1e4Vd7ZbmMLZhLUJCWWPcTKLSMYEr"
        "1pEV7WnEzMkd loom-dev@box"
    )
    assert fingerprint_of(key).startswith("SHA256:")
    assert not fingerprint_of(key).endswith("=")


def test_a_malformed_public_key_has_no_fingerprint() -> None:
    """An empty or truncated .pub must not look like a match for anything."""
    assert fingerprint_of("") == ""
    assert fingerprint_of("ssh-ed25519") == ""
    assert fingerprint_of("ssh-ed25519 not-base64!!") == ""
