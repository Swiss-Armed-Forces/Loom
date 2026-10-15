"""Test rendering an email to PDF via Gotenberg's Chromium route."""

from dataclasses import dataclass, field

import pytest
from common.services.lazybytes_service import InMemoryTempLazyBytesService
from gotenberg_client.options import PageSize
from httpx import HTTPStatusError, Request, Response, TransportError

from worker import dependencies
from worker.index_file.parse_and_render_email_task import RenderedEmail
from worker.index_file.tasks.email_processing import render_email_to_pdf
from worker.index_file.tasks.render import GotenbergError

# pylint: disable=redefined-outer-name

PDF_BYTES = b"%PDF-1.4 single page"
PAGINATED_PDF_BYTES = b"%PDF-1.4 paginated"


@dataclass
class RenderAttempt:
    """One html_to_pdf call made against the fake Gotenberg client."""

    single_page: bool | None = None
    page_size: PageSize | None = None
    html: str | None = None
    skipped_network_idle: bool = False


class FakeRoute:
    """Records what a render asked for and replays a canned outcome."""

    def __init__(self, attempt: RenderAttempt, outcome: object) -> None:
        self._attempt = attempt
        self._outcome = outcome

    def __enter__(self) -> "FakeRoute":
        return self

    def __exit__(self, *_) -> None:
        return None

    def string_index(self, html: str) -> "FakeRoute":
        self._attempt.html = html
        return self

    def skip_network_idle(self) -> "FakeRoute":
        self._attempt.skipped_network_idle = True
        return self

    def size(self, size: PageSize) -> "FakeRoute":
        self._attempt.page_size = size
        return self

    def single_page(self, *, use_single_page: bool) -> "FakeRoute":
        self._attempt.single_page = use_single_page
        return self

    def run(self) -> Response:
        if isinstance(self._outcome, Exception):
            raise self._outcome
        assert isinstance(self._outcome, bytes)
        return Response(200, content=self._outcome)


@dataclass
class FakeChromium:
    """Hands out one route per call, following a scripted list of outcomes."""

    outcomes: list[object]
    attempts: list[RenderAttempt] = field(default_factory=list)

    def html_to_pdf(self) -> FakeRoute:
        attempt = RenderAttempt()
        self.attempts.append(attempt)
        outcome = self.outcomes[min(len(self.attempts) - 1, len(self.outcomes) - 1)]
        return FakeRoute(attempt, outcome)


@dataclass
class FakeGotenbergClient:
    chromium: FakeChromium


def too_large_error() -> HTTPStatusError:
    """The 400 Gotenberg answers when Chromium cannot print a page that tall."""
    return HTTPStatusError(
        "Chromium failed to print the PDF; "
        "this usually happens when the page is too large",
        request=Request("POST", "http://gotenberg.loom"),
        response=Response(400),
    )


@pytest.fixture
def email() -> RenderedEmail:
    return RenderedEmail(rendered_content="<html><body>a long email</body></html>")


def install_client(*outcomes: object) -> FakeChromium:
    """Inject a fake Gotenberg client that replays the given outcomes in order."""
    chromium = FakeChromium(outcomes=list(outcomes))
    dependencies._gotenberg_client = (  # pylint: disable=protected-access
        FakeGotenbergClient(chromium=chromium)
    )
    return chromium


def test_returns_none_when_email_is_none() -> None:
    assert render_email_to_pdf(None) is None


def test_renders_a_single_continuous_page(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    email: RenderedEmail,
) -> None:
    chromium = install_client(PDF_BYTES)

    result = render_email_to_pdf(email)

    assert result is not None
    with lazybytes_service_inmemory.load_memoryview(result) as content:
        assert bytes(content) == PDF_BYTES

    assert len(chromium.attempts) == 1
    attempt = chromium.attempts[0]
    assert attempt.single_page is True
    assert attempt.html == email.rendered_content
    assert attempt.skipped_network_idle is True


@pytest.mark.usefixtures("lazybytes_service_inmemory")
def test_still_sets_the_page_width(email: RenderedEmail) -> None:
    """The page size is what gives the single page its A4 width."""
    chromium = install_client(PDF_BYTES)

    render_email_to_pdf(email)

    assert chromium.attempts[0].page_size is not None


def test_falls_back_to_pagination_when_the_page_is_too_large(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    email: RenderedEmail,
) -> None:
    """A paginated preview beats no preview for an email past Chromium's limit."""
    chromium = install_client(too_large_error(), PAGINATED_PDF_BYTES)

    result = render_email_to_pdf(email)

    assert result is not None
    with lazybytes_service_inmemory.load_memoryview(result) as content:
        assert bytes(content) == PAGINATED_PDF_BYTES

    assert [attempt.single_page for attempt in chromium.attempts] == [True, False]


def test_returns_none_when_pagination_also_fails(email: RenderedEmail) -> None:
    chromium = install_client(too_large_error(), too_large_error())

    assert render_email_to_pdf(email) is None
    assert len(chromium.attempts) == 2


def test_connectivity_failure_is_retried_rather_than_paginated(
    email: RenderedEmail,
) -> None:
    """A transport error means Gotenberg is unreachable, not that the page is too
    tall."""
    chromium = install_client(TransportError("connection refused"))

    with pytest.raises(GotenbergError):
        render_email_to_pdf(email)

    assert len(chromium.attempts) == 1
