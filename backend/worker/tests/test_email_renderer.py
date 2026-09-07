# pylint: disable=redefined-outer-name
# typos: disable-file
from email import message_from_bytes
from email.message import EmailMessage
from email.policy import default
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from common.services.lazybytes_service import InMemoryTempLazyBytesService

from worker.index_file.parse_and_render_email_task import (
    RenderedEmail,
    _parse_email_body,
    generate_email,
    parse_and_render_email_task,
)

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


# basic checks


def test_parse_and_render_email_task_not_detected():
    """Verifies that the task returns None if no email is detected."""
    result = parse_and_render_email_task(
        is_email_detected=False, file_content=MagicMock()
    )
    assert result is None

    result = parse_and_render_email_task(is_email_detected=False, file_content=None)
    assert result is None


def test_parse_and_render_email_task_content_none():
    """Verifies that the task returns None if file_content is none."""
    result = parse_and_render_email_task(is_email_detected=True, file_content=None)
    assert result is None


# email fixtures


@pytest.fixture
def basic_email_bytes() -> bytes:
    """Load sample bytes from test assets."""
    email_path = TEST_ASSETS_DIR / "basic_email.eml"
    return email_path.read_bytes()


@pytest.fixture
def basic_email_plaintext_bytes() -> bytes:
    """Load sample bytes from test assets."""
    email_path = TEST_ASSETS_DIR / "basic_email_plain_text.eml"
    return email_path.read_bytes()


@pytest.fixture
def email_img_01_bytes() -> bytes:
    """Load sample bytes from test assets."""
    email_path = TEST_ASSETS_DIR / "email_img_01.eml"
    return email_path.read_bytes()


@pytest.fixture
def email_img_02_bytes() -> bytes:
    """Load sample bytes from test assets."""
    email_path = TEST_ASSETS_DIR / "email_img_02.eml"
    return email_path.read_bytes()


@pytest.fixture
def very_long_email_bytes() -> bytes:
    email_path = TEST_ASSETS_DIR / "very_long_email.eml"
    return email_path.read_bytes()


@pytest.fixture
def very_long_email_html_bytes() -> bytes:
    email_path = TEST_ASSETS_DIR / "very_long_html_email.eml"
    return email_path.read_bytes()


# render email tests


def test_parse_and_render_basic_email_task_success(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    basic_email_bytes: bytes,
) -> None:
    """Verifies successful payload parsing, HTML wrapping, and escaping."""
    lazy_bytes = lazybytes_service_inmemory.from_bytes(basic_email_bytes)
    result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )

    assert isinstance(result, RenderedEmail)
    assert "Mikel&#32;Lindsaar" in result.rendered_content
    assert "test@lindsaar.net" in result.rendered_content
    assert "Date" in result.rendered_content
    assert "22&#32;Nov&#32;2008" in result.rendered_content
    assert "Cc:" not in result.rendered_content
    assert "Bcc:" not in result.rendered_content
    assert "Hope it works" in result.rendered_content


def test_parse_and_render_basic_plaintext_email_task_success(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    basic_email_plaintext_bytes: bytes,
) -> None:
    """Testing plain text escape."""
    msg = message_from_bytes(basic_email_plaintext_bytes, policy=default)

    result = _parse_email_body(msg)

    # plain text is escaped in _parse_email_body
    assert "Hello&#32;&amp;" in result.html_body

    lazy_bytes = lazybytes_service_inmemory.from_bytes(basic_email_plaintext_bytes)
    render_result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )

    # escape should survive rendering
    assert "Hello &amp;" in render_result.rendered_content

    # Cc and Bcc should be in rendered content
    assert "Cc" in render_result.rendered_content
    assert "Bcc" in render_result.rendered_content


# parse html body


def test_sanitization_strips_external_urls(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
) -> None:
    """External http/https URLs are stripped; data:, cid:, and mailto: survive."""
    raw = (
        b"From: sender@example.com\r\n"
        b"To: recipient@example.com\r\n"
        b"Subject: External URL test\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body>"
        b'<img src="https://via.placeholder.com/150">'
        b'<img src="http://evil.com/tracker.gif">'
        b'<img src="data:image/png;base64,iVBORw0KGgo=">'
        b'<a href="mailto:user@example.com">Email</a>'
        b'<a href="https://evil.com">Click</a>'
        b"</body></html>"
    )
    lazy_bytes = lazybytes_service_inmemory.from_bytes(raw)
    result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )

    assert result is not None
    # External URLs must be stripped
    assert "via.placeholder.com" not in result.rendered_content
    assert "evil.com" not in result.rendered_content
    # data: URIs must survive
    assert "data:image/png;base64,iVBORw0KGgo=" in result.rendered_content
    # mailto: links must survive
    assert "mailto:user@example.com" in result.rendered_content


def test_parse_email_body_html_priority():
    """Ensures HTML payloads take precedence and are used verbatim."""
    msg = EmailMessage()
    msg.set_content("Plain content")
    msg.add_alternative("<p>HTML content</p>", subtype="html")

    parsed_email = _parse_email_body(msg)
    assert "<p>HTML content</p>" in parsed_email.html_body
    assert "Plain content" not in parsed_email.html_body


def test_parse_email_body_plain_text_only():
    """Plain-text-only email wraps body in a styled div for wrapping."""
    msg = EmailMessage()
    msg.set_content("Hello & Welcome <User>")

    parsed_email = _parse_email_body(msg)
    assert "Hello&#32;&amp;&#32;Welcome&#32;&lt;User&gt;&#10;" in parsed_email.html_body
    assert "div style=" in parsed_email.html_body


def test_parse_email_body_with_cid_replacement():
    """Validates that inline images with a Content-ID have their src parameters mapped
    to inline Base64 Data URIs."""
    msg = EmailMessage()
    msg.set_content("Fallback text")
    msg.add_alternative(
        '<html><body><img src="cid:logo_123"></body></html>', subtype="html"
    )

    html_part = msg.get_payload()[1]
    html_part.add_related(
        b"\x89PNG\r\n\x1a\n", maintype="image", subtype="png", cid="logo_123"
    )

    parsed_email = _parse_email_body(msg)
    # Verifies that the string matches the expected base64-encoded Data URI layout
    assert 'src="data:image/png;base64,iVBORw0KGgo="' in parsed_email.html_body


def test_parse_email_body_none_payload():
    """Tests that nested parts returning None payloads don't crash."""
    msg = EmailMessage()
    msg.set_type("multipart/mixed")

    good_part = EmailMessage()
    good_part.set_content("Visible content")

    no_payload_part = EmailMessage()
    no_payload_part.set_type("text/plain")
    no_payload_part.set_payload(None)

    msg.set_payload([no_payload_part, good_part])

    parsed_email = _parse_email_body(msg)
    assert "Visible&#32;content&#10;" in parsed_email.html_body


def test_parse_and_render_email_rfc2047_encoded_headers(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    email_img_02_bytes: bytes,
) -> None:

    lazy_bytes = lazybytes_service_inmemory.from_bytes(email_img_02_bytes)
    render_result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )

    assert "René&#32;Dupond" in render_result.rendered_content


def test_very_long_email(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    very_long_email_bytes: bytes,
) -> None:
    """Testing very long email rendering."""
    lazy_bytes = lazybytes_service_inmemory.from_bytes(very_long_email_bytes)
    render_result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )
    end_of_paragraph = "Proin porttitor, orci nec nonummy molestie, enim est eleifend mi, non fermentum diam nisl sit amet erat. Duis semper. Duis arcu massa, scelerisque vitae, consequat in, pretium a, enim."  # noqa: B950  # pylint: disable=line-too-long
    assert end_of_paragraph in render_result.rendered_content


def test_very_long_html_email(
    lazybytes_service_inmemory: InMemoryTempLazyBytesService,
    very_long_email_html_bytes: bytes,
) -> None:
    """Testing rendering of the very long email with HTML body."""
    lazy_bytes = lazybytes_service_inmemory.from_bytes(very_long_email_html_bytes)
    render_result = parse_and_render_email_task(
        is_email_detected=True, file_content=lazy_bytes
    )

    # after sanitization, there should be <h1> tag left
    body_chunk = "<h1>Very Long HTML Email Test</h1>"
    assert body_chunk in render_result.rendered_content


# sanitization tests


def _render_body(html_body: str) -> str:
    """Helper that renders an email with the given HTML body and returns the result."""
    data = {
        "From": "test@example.com",
        "To": "recipient@example.com",
        "Cc": "",
        "Bcc": "",
        "Subject": "Test",
        "Date": "2024-01-01",
        "Body": html_body,
        "Attachments": [],
    }
    return generate_email(data)


def test_sanitization_preserves_inline_styles() -> None:
    """Inline style attributes must survive sanitization."""
    result = _render_body('<div style="color: red; font-size: 14px">Styled text</div>')
    assert 'style="color: red; font-size: 14px"' in result
    assert "Styled text" in result


def test_sanitization_preserves_style_tag() -> None:
    """Embedded <style> blocks must survive sanitization."""
    result = _render_body(
        '<style>.x { color: red; }</style><div class="x">Styled</div>'
    )
    assert "<style>.x { color: red; }</style>" in result
    assert 'class="x"' in result


def test_sanitization_preserves_table_layout_attrs() -> None:
    """Table layout attributes (bgcolor, width, cellpadding) must survive."""
    html = (
        '<table bgcolor="#ffffff" width="600" cellpadding="10" cellspacing="0">'
        '<tr bgcolor="#f0f0f0"><td width="300" valign="top">Cell</td></tr>'
        "</table>"
    )
    result = _render_body(html)
    assert 'bgcolor="#ffffff"' in result
    assert 'width="600"' in result
    assert 'cellpadding="10"' in result
    assert 'cellspacing="0"' in result
    assert 'valign="top"' in result


def test_sanitization_strips_script_tags() -> None:
    """<script> tags and their content must be removed entirely."""
    result = _render_body("<script>alert('xss')</script><p>Safe content</p>")
    assert "<script>" not in result
    assert "alert" not in result
    assert "<p>Safe content</p>" in result


def test_sanitization_strips_non_visible_tag_content() -> None:
    """Non-visible tags must have their content removed, not leaked as bare text."""
    cases = [
        ("title", "Secret Title", "Secret Title"),
        ("head", "<title>Head Content</title>", "Head Content"),
        ("textarea", "Hidden Template", "Hidden Template"),
        ("select", "<option>Dropdown Item</option>", "Dropdown Item"),
        ("button", "Submit Button", "Submit Button"),
        ("svg", "<text>SVG Label</text>", "SVG Label"),
        ("math", "<mi>formula</mi>", "formula"),
    ]
    for tag, content, leak_text in cases:
        result = _render_body(f"<{tag}>{content}</{tag}><p>Visible</p>")
        assert leak_text not in result, f"<{tag}> content leaked: {leak_text!r}"
        assert "<p>Visible</p>" in result


def test_sanitization_strips_event_handlers() -> None:
    """Event handler attributes (onclick, onerror, etc.) must be stripped."""
    result = _render_body(
        '<div onclick="alert(1)">Click</div>'
        '<img src="data:image/png;base64,x" onerror="alert(2)">'
    )
    assert "onclick" not in result
    assert "onerror" not in result
    assert "alert" not in result
    assert ">Click</div>" in result
