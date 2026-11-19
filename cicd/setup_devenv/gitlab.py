"""A GitLab API client built from the standard library alone.

`cicd/setup-devenv` runs before Nix, devenv and the project venv exist, so it cannot
import `python-gitlab` the way `cicd/aitools/` does. This is the small subset of the API
that first-time setup needs, over `urllib`.

Every call returns a typed model or raises `GitLabError` carrying a `Failure` that says
*which* thing went wrong -- an expired token, a token without the scope, and an
unreachable network each need a different sentence in front of the operator, and a
transport that cannot tell them apart ends up blaming the wrong one.

Python 3.9 is the floor here; see the note in the package docstring.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

GITLAB_API = "https://gitlab.com/api/v4"

# urlopen blocks forever without one, and pylint's `timeout-methods` is the only
# thing that would catch a missing one.
TIMEOUT_SECONDS = 15.0

USER_AGENT = "loom-setup-devenv"


class Failure(Enum):
    """Why a GitLab call did not produce an answer."""

    AUTH = "auth"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    NETWORK = "network"
    MALFORMED = "malformed"
    SERVER = "server"


class GitLabError(Exception):
    """A GitLab call that did not produce an answer."""

    def __init__(
        self, failure: Failure, detail: str, status: Optional[int] = None
    ) -> None:
        super().__init__(failure, detail, status)
        self.failure = failure
        self.detail = detail
        self.status = status

    def __str__(self) -> str:
        """The explanation, which is the part every caller puts on screen."""
        return self.detail


@dataclass(frozen=True)
class GitLabUser:
    """The authenticated account, as `/user` reports it."""

    name: str
    username: str
    email: str


@dataclass(frozen=True)
class SshKey:
    """A public key registered on the account."""

    key_id: int
    title: str
    key: str

    @property
    def fingerprint(self) -> str:
        """The OpenSSH SHA256 fingerprint of this key."""
        return fingerprint_of(self.key)


def fingerprint_of(public_key: str) -> str:
    """The OpenSSH SHA256 fingerprint of a public key, as `ssh-keygen -lf` prints it.

    Empty when the key is not in `<type> <base64> [comment]` form.
    """
    parts = public_key.split()
    if len(parts) < 2:
        return ""
    try:
        blob = base64.b64decode(parts[1], validate=True)
    except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
        return ""
    digest = base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii")
    return "SHA256:" + digest.rstrip("=")


class NoRedirects(urllib.request.HTTPRedirectHandler):
    """Refuses every redirect.

    `HTTPRedirectHandler` copies non-content headers onto the new request, and `PRIVATE-
    TOKEN` is one of them, so following one would hand the token to whatever host it
    names. The API lives at a fixed URL that has no business redirecting; answering None
    makes urllib surface the 3xx as an error rather than follow it.
    """

    def redirect_request(
        self, *_args: Any, **_kwargs: Any
    ) -> Optional[urllib.request.Request]:
        """Never follow a redirect.

        None is `HTTPRedirectHandler`'s own way of declining one, which makes urllib
        raise the 3xx instead of acting on it.
        """
        return None


def _build_opener() -> urllib.request.OpenerDirector:
    """An opener that will not follow a redirect away from the API."""
    return urllib.request.build_opener(NoRedirects())


def _explanation(raw: str) -> str:
    """GitLab's own words for a failure, from a body that may not be JSON."""
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()[:200]
    if not isinstance(decoded, dict):
        return raw.strip()[:200]
    for key in ("message", "error_description", "error"):
        value = decoded.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            # {"message": {"fingerprint": ["has already been taken"]}}
            return "; ".join(
                f"{field_name}: {', '.join(str(item) for item in reasons)}"
                for field_name, reasons in value.items()
            )
    return raw.strip()[:200]


def _from_http_error(error: urllib.error.HTTPError) -> GitLabError:
    """Map a status and its body onto a typed failure."""
    try:
        raw = error.read().decode("utf-8", errors="replace")
    except OSError:
        raw = ""
    detail = _explanation(raw) or str(error.reason) or f"HTTP {error.code}"

    if error.code == 401:
        return GitLabError(Failure.AUTH, f"GitLab rejected the token: {detail}", 401)
    if error.code == 403:
        return GitLabError(
            Failure.FORBIDDEN,
            f"the token is valid but not permitted to do this: {detail}"
            " (it needs the `api` scope)",
            403,
        )
    if error.code in (400, 409, 422):
        return GitLabError(Failure.CONFLICT, detail, error.code)
    if error.code >= 500:
        return GitLabError(
            Failure.SERVER, f"gitlab.com returned {error.code}", error.code
        )
    return GitLabError(Failure.NETWORK, f"HTTP {error.code}: {detail}", error.code)


def _from_transport_error(base_url: str, error: Exception) -> GitLabError:
    """Map a connection-level failure onto a typed failure."""
    cause = error.reason if isinstance(error, urllib.error.URLError) else error
    if isinstance(cause, ssl.SSLCertVerificationError):
        return GitLabError(
            Failure.NETWORK,
            f"the TLS certificate for {base_url} did not verify ({cause})."
            " A network that intercepts TLS needs its CA in SSL_CERT_FILE",
        )
    return GitLabError(Failure.NETWORK, f"cannot reach {base_url}: {error}")


@dataclass(frozen=True)
class GitLabClient:
    """The slice of the GitLab API that first-time setup needs.

    A dataclass so that `opener` stays injectable: the tests hand it a fake with an
    `open(request, timeout=...)` method, which is the whole seam -- no sockets, no
    monkeypatching.
    """

    token: str
    base_url: str = GITLAB_API
    timeout: float = TIMEOUT_SECONDS
    opener: urllib.request.OpenerDirector = field(default_factory=_build_opener)

    def fetch_user(self) -> GitLabUser:
        """The account the token belongs to."""
        decoded = self._request("GET", "/user")
        if not isinstance(decoded, dict):
            raise GitLabError(Failure.MALFORMED, "GitLab did not describe an account")
        return GitLabUser(
            name=str(decoded.get("name") or ""),
            username=str(decoded.get("username") or ""),
            email=str(decoded.get("email") or ""),
        )

    def list_ssh_keys(self) -> List[SshKey]:
        """Every public key registered on the account."""
        decoded = self._request("GET", "/user/keys")
        if not isinstance(decoded, list):
            raise GitLabError(Failure.MALFORMED, "GitLab did not return a list of keys")
        return [_ssh_key_from(entry) for entry in decoded if isinstance(entry, dict)]

    def upload_ssh_key(self, title: str, public_key: str) -> SshKey:
        """Register a public key, returning the existing one if it is already there."""
        try:
            decoded = self._request(
                "POST",
                "/user/keys",
                {
                    "title": title,
                    "key": public_key,
                    "usage_type": "auth_and_signing",
                },
            )
        except GitLabError as error:
            if error.failure is Failure.CONFLICT and "already been taken" in (
                error.detail
            ):
                existing = self._key_matching_or_none(public_key)
                if existing is not None:
                    return existing
            raise
        if not isinstance(decoded, dict):
            raise GitLabError(Failure.MALFORMED, "GitLab did not describe the new key")
        return _ssh_key_from(decoded)

    def _key_matching_or_none(self, public_key: str) -> Optional[SshKey]:
        """The registered key with the same fingerprint, when there is one.

        Answers None rather than raising when the lookup itself fails: this runs
        inside the handler for a rejected upload, and the rejection is the thing
        worth reporting -- a second failure on top of it would hide the first.
        """
        wanted = fingerprint_of(public_key)
        if not wanted:
            return None
        try:
            registered = self.list_ssh_keys()
        except GitLabError:
            return None
        for key in registered:
            if key.fingerprint == wanted:
                return key
        return None

    def _request(self, method: str, path: str, payload: Optional[Any] = None) -> Any:
        """Call the API and return the decoded JSON body."""
        body = None
        # urllib title-cases header names, so this goes out as `Private-token`.
        # HTTP header names are case-insensitive and GitLab normalises them.
        headers = {
            "PRIVATE-TOKEN": self.token,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        try:
            # HTTPError subclasses URLError and must be caught first, or every
            # status collapses into "cannot reach gitlab.com".
            with self.opener.open(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset("utf-8")
                raw = response.read().decode(charset, errors="replace")
        except urllib.error.HTTPError as error:
            raise _from_http_error(error) from error
        except (http.client.HTTPException, OSError) as error:
            # OSError is the wide one on purpose: URLError, TimeoutError and
            # socket.timeout are all subclasses of it, and a protocol-level fault
            # arrives as HTTPException, which is not.
            raise _from_transport_error(self.base_url, error) from error

        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise GitLabError(
                Failure.MALFORMED, "GitLab returned a body that is not JSON"
            ) from error


def _ssh_key_from(entry: Any) -> SshKey:
    """One key out of an API response."""
    return SshKey(
        key_id=int(entry.get("id") or 0),
        title=str(entry.get("title") or ""),
        key=str(entry.get("key") or ""),
    )
