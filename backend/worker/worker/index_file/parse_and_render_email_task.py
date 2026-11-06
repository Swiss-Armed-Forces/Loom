import logging
from collections.abc import Iterator
from email import message_from_bytes
from email.message import EmailMessage, MIMEPart
from email.policy import default
from re import IGNORECASE, escape, sub
from typing import TypedDict

import nh3
from common.dependencies import (
    get_celery_app,
    get_lazybytes_service,
)
from common.services.lazybytes_service import TempLazyBytes
from pydantic import BaseModel

from worker.index_file.infra.file_indexing_task import FileIndexingTask

logger = logging.getLogger(__name__)

app = get_celery_app()

# The content type of an email carried as an attachment by another email.
ATTACHED_MESSAGE_TYPE = "message/rfc822"

# Shown for an attached message that names neither a file nor a subject.
UNNAMED_ATTACHED_MESSAGE = "attached_message.eml"

# Tags beyond nh3.ALLOWED_TAGS needed for email HTML rendering
_EMAIL_EXTRA_TAGS: set[str] = {"style", "font", "big", "tfoot"}

# Tags whose content (not just the tag) must be removed entirely.
# Without this, nh3 strips the tag but leaves the text content visible —
# leaking non-visible metadata, form labels, or markup as bare text.
_EMAIL_CLEAN_CONTENT_TAGS: set[str] = {
    "script",
    "noscript",
    "iframe",
    "object",
    "embed",
    "applet",
    "head",
    "title",
    "textarea",
    "select",
    "option",
    "button",
    "svg",
    "math",
}

# Attributes allowed on all elements — nh3 defaults don't include style or class
_EMAIL_GLOBAL_ATTRIBUTES: set[str] = {"style", "class", "id", "dir", "lang", "title"}

# Tag-specific attributes for email layout (merge with nh3 defaults)
_EMAIL_TAG_ATTRIBUTES: dict[str, set[str]] = {
    "table": {
        "width",
        "height",
        "cellpadding",
        "cellspacing",
        "border",
        "bgcolor",
        "summary",
        "align",
        "char",
        "charoff",
    },
    "td": {
        "width",
        "height",
        "bgcolor",
        "valign",
        "colspan",
        "rowspan",
        "headers",
        "align",
        "char",
        "charoff",
    },
    "th": {
        "width",
        "height",
        "bgcolor",
        "valign",
        "colspan",
        "rowspan",
        "headers",
        "align",
        "scope",
        "char",
        "charoff",
    },
    "tr": {"bgcolor", "valign", "align", "char", "charoff"},
    "col": {"width", "span", "align", "char", "charoff"},
    "colgroup": {"width", "span", "align", "char", "charoff"},
    "img": {"src", "alt", "width", "height", "align"},
    "font": {"color", "face", "size"},
    "a": {"href", "hreflang", "name"},
    "hr": {"size", "width", "align"},
    "ol": {"start", "type"},
    "ul": {"type"},
    "body": {"bgcolor"},
    "div": {"align"},
    "p": {"align"},
    "blockquote": {"cite", "type"},
    "del": {"datetime", "cite"},
    "ins": {"datetime", "cite"},
    "bdo": {"dir"},
    "q": {"cite"},
    "thead": {"align", "char", "charoff"},
    "tbody": {"align", "char", "charoff"},
    "tfoot": {"align", "char", "charoff"},
}

# flake8: noqa: B950

# The element carrying the page gutter. Everything the renderer generates lives
# inside it, out of reach of the email's own stylesheet.
EMAIL_PAGE_CLASS = "loom-email-page"

# The element wrapping the sanitized email. Prefixed so an email's own CSS is
# unlikely to address it by name.
EMAIL_BODY_CLASS = "loom-email-body"

EMAIL_HTML_HEAD = f"""
<head>
    <meta charset="utf-8">
    <title>Email Preview</title>
    <style>
        body {{ margin: 0; font-family: sans-serif; background-color: #ffffff; }}

        /* The page gutter belongs on an element the email cannot address. On `body`
        it is at the mercy of the `body {{ margin: 0 }}` reset nearly every email
        carries, which leaves the header and avatar against the paper edge. */
        .{EMAIL_PAGE_CLASS} {{ padding: 20px !important; }}

        .{EMAIL_BODY_CLASS} {{ width: 100%; max-width: 100%; overflow: hidden; }}
        .{EMAIL_BODY_CLASS} img {{ max-width: 100%; height: auto; }}
        .{EMAIL_BODY_CLASS} img:not([src]) {{ display: inline-block; background-color: #e0e0e0; }}
        .{EMAIL_BODY_CLASS} table {{ max-width: 100%; table-layout: fixed; }}
        .{EMAIL_BODY_CLASS} pre {{ white-space: pre-wrap; overflow-wrap: break-word; }}
        .{EMAIL_BODY_CLASS} * {{ max-width: 100%; }}

        @page {{ margin: 0; }}


        /* Avatar Container Styling */
        .loom-avatar-circle {{
            width: 42px;
            height: 42px;
            background-color: #e0e0e0; /* Neutral light grey background */
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        /* Person Icon Styling */
        .loom-avatar-icon {{
            width: 24px;
            height: 24px;
            fill: #4a4a4a; /* Neutral dark grey silhouette */
        }}
    </style>
</head>
"""


class RenderedEmail(BaseModel):
    rendered_content: str


class EmailTemplateData(TypedDict):
    From: str
    To: str
    Cc: str
    Bcc: str
    Subject: str
    Date: str
    Body: str
    Attachments: list[str]


class EmailAttachment(BaseModel):
    name: str
    size: int


class ParsedEmail(BaseModel):
    html_body: str
    attachments: list[EmailAttachment] = []


def generate_email(data: EmailTemplateData) -> str:
    # pylint: disable=no-member
    """
    Note:
    Main defence line is Gotenberg pod isolation + Chromium sandbox.
    We use a permissive nh3 configuration that preserves email styling
    (inline CSS, <style> tags, table layout attributes, <font> tags)
    while stripping genuinely dangerous elements (<script>, <iframe>,
    event handlers). This is safe because the HTML is only rendered in
    Gotenberg's sandboxed Chromium, never embedded in our app's DOM.
    """
    email_html_cc = ""
    if data["Cc"]:
        email_html_cc = f"""
                        <tr>
                            <td style="padding: 3px 0; font-weight: bold; vertical-align: top;">Cc </td>
                            <td style="padding: 3px 0;">{nh3.escape(data['Cc'])}</td>
                        </tr>
        """

    email_html_bcc = ""
    if data["Bcc"]:
        email_html_bcc = f"""
                        <tr>
                            <td style="padding: 3px 0; font-weight: bold; vertical-align: top;">Bcc </td>
                            <td style="padding: 3px 0;">{nh3.escape(data['Bcc'])}</td>
                        </tr>
        """

    email_html_right_col = f"""
    <!-- Right Column: Email Details -->
                <td style="vertical-align: top;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 3px 0; font-weight: bold; vertical-align: top; width: 60px;">From </td>
                            <td style="padding: 3px 0;">{nh3.escape(data['From'])}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px 0; font-weight: bold; vertical-align: top;">To </td>
                            <td style="padding: 3px 0;">{nh3.escape(data['To'])}</td>
                        </tr>
                        {email_html_cc}
                        {email_html_bcc}
                        <tr>
                            <td style="padding: 3px 0; font-weight: bold; vertical-align: top;">Date </td>
                            <td style="padding: 3px 0;">{nh3.escape(data['Date'])}</td>
                        </tr>
                    </table>
                </td>
    """

    email_attachments = ""
    if len(data["Attachments"]) > 0:
        attachment_list = ""
        for x in data["Attachments"]:
            attachment_list += "&#128196; " + x + " "

        email_attachments = f"""
            <table style="width: 100%; border-collapse: collapse;">
            <tr bgcolor="#f2f2f2">
                <td>
                {attachment_list}
                </td>
            </tr>
            </table>
            <br>
        """

    sanitized_body = nh3.clean(
        data["Body"],
        tags=nh3.ALLOWED_TAGS | _EMAIL_EXTRA_TAGS,
        clean_content_tags=_EMAIL_CLEAN_CONTENT_TAGS,
        attributes={"*": _EMAIL_GLOBAL_ATTRIBUTES, **_EMAIL_TAG_ATTRIBUTES},
        url_schemes={"data", "cid", "mailto"},
    )

    email_html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    {EMAIL_HTML_HEAD}
    <body>
    <div class="{EMAIL_PAGE_CLASS}">
        <h4 style="padding: 3px 0; font-weight: bold;"> {nh3.escape(data['Subject'])}</h4>

        <!-- Main Layout Table -->
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; color: #333333; margin-bottom: 15px;">
            <tr>
                <!-- Left Column: Avatar Container -->
                <td style="width: 55px; vertical-align: top; padding-top: 3px;">
                    <div class="loom-avatar-circle">
                        <!-- Inline HTML Person SVG Icon -->
                        <svg class="loom-avatar-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                    </div>
                </td>
    {email_html_right_col}
            </tr>
        </table>
    {email_attachments}

        <div class="{EMAIL_BODY_CLASS}">{sanitized_body}</div>
    </div>
    </body>

    </html>
    """
    return email_html_template


def size_to_string(size: int) -> str:
    text = "("
    if size < 1024:
        text += str(size) + "B"
    elif size < 1024**2:
        text += "~" + str(int(size / 1024)) + "KB"
    elif size < 1024**3:
        text += "~" + str(int(size / 1024**2)) + "MB"
    elif size < 1024**4:
        text += "~" + str(int(size / 1024**3)) + "GB"
    elif size < 1024**5:
        text += "~" + str(int(size / 1024**4)) + "TB"
    else:
        text += ":-O"

    return text + ")"


@app.task(base=FileIndexingTask)
def parse_and_render_email_task(
    is_email_detected: bool, file_content: TempLazyBytes | None
) -> RenderedEmail | None:

    if not is_email_detected:
        return None

    if file_content is None:
        return None

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        msg = message_from_bytes(bytes(memview), policy=default)

    # cast to str to handle structured header objects (i.e date)
    # headers are auto-decoded string objects when policy=default
    email_data: ParsedEmail = _parse_email_body(msg)

    attachments = [
        attachment.name + " " + size_to_string(attachment.size)
        for attachment in email_data.attachments
    ]

    data: EmailTemplateData = {
        "From": str(msg.get("From", "")),
        "To": str(msg.get("To", "")),
        "Cc": str(msg.get("Cc", "")),
        "Bcc": str(msg.get("Bcc", "")),
        "Subject": str(msg.get("Subject", "")),
        "Date": str(msg.get("Date", "")),
        "Body": email_data.html_body,
        "Attachments": attachments,
    }

    return RenderedEmail(rendered_content=generate_email(data))


def _iter_parts(part: MIMEPart) -> Iterator[MIMEPart]:
    """Yield a message and its parts, treating an attached message as a leaf.

    `walk` descends through a `message/rfc822` part into the message it carries, which
    puts that message's body, attachments and inline images into the preview of the
    message carrying it. An attached message is an attachment: it is yielded whole and
    not entered.
    """
    yield part

    if part.get_content_type() == ATTACHED_MESSAGE_TYPE:
        return

    for subpart in part.iter_parts():
        yield from _iter_parts(subpart)


def _describe_attached_message(part: MIMEPart) -> EmailAttachment:
    """Name and measure an attached message.

    A forwarded message frequently carries no `filename` parameter, so the subject of
    the message it carries stands in as the name.
    """
    carried = next(iter(part.iter_parts()), None)
    size = len(carried.as_bytes()) if carried is not None else 0

    filename = part.get_filename()
    if not filename and carried is not None:
        subject = str(carried.get("Subject", "")).strip()
        filename = f"{subject}.eml" if subject else ""

    return EmailAttachment(name=filename or UNNAMED_ATTACHED_MESSAGE, size=size)


def _collect_attachments(msg: EmailMessage) -> list[EmailAttachment]:
    attachments = []

    for part in _iter_parts(msg):
        if part.get_content_type() == ATTACHED_MESSAGE_TYPE:
            attachments.append(_describe_attached_message(part))
            continue

        if part.get_content_disposition() != "attachment":
            continue

        filename = part.get_filename()
        if filename:
            data = part.get_payload(decode=True) or b""
            attachments.append(EmailAttachment(name=filename, size=len(data)))

    return attachments


def _parse_email_body(
    msg: EmailMessage,
) -> ParsedEmail:

    html_body = ""
    plain_body = ""
    cid_map = {}

    for part in _iter_parts(msg):

        # Continue for multipart container, which an attached message also is
        if part.is_multipart():
            continue

        # Continue for empty payload
        if part.get_payload() is None:
            continue

        # Attachments are collected separately
        if part.get_content_disposition() == "attachment":
            continue

        content_type = part.get_content_type()

        # HTML
        if content_type == "text/html":
            html_body += part.get_content()

        # Plain
        elif content_type == "text/plain":
            plain_body += part.get_content()

        # collect inline image assets referencing CID
        elif part.get("Content-ID") and content_type.startswith("image/"):
            # strip out brackets whitespaces and any embedded newlines from the CID header value
            raw_cid = str(part.get("Content-ID"))
            cid = sub(r"[<>\s]", "", raw_cid).strip()

            raw_payload = part.get_payload(decode=False)

            # Should always be str
            if isinstance(raw_payload, str):
                # Strip out line breaks
                base64_clean = raw_payload.replace("\r", "").replace("\n", "").strip()

                cid_map[cid] = f"data:{content_type};base64,{base64_clean}"

    # fallback assignment logic if no html
    if not html_body:
        html_body = f'<div style="white-space:pre-wrap;word-break:break-word;font-family:monospace"><pre>{nh3.escape(plain_body)}</pre></div>'  # noqa: B950  # pylint: disable=line-too-long,no-member
    elif cid_map:
        for cid, inline_uri in cid_map.items():
            pattern = rf'(src=["\'])\s*cid:{escape(cid)}\s*(["\'])'

            html_body = sub(pattern, rf"\1{inline_uri}\2", html_body, flags=IGNORECASE)

    return ParsedEmail(
        html_body=html_body,
        attachments=_collect_attachments(msg),
    )
