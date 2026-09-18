import logging
from email import message_from_bytes
from email.message import EmailMessage
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

EMAIL_HTML_HEAD = """
<head>
    <meta charset="utf-8">
    <title>Email Preview</title>
    <style>
        body { margin: 20px; font-family: sans-serif; background-color: #ffffff; }

        .email-body { width: 100%; max-width: 100%; overflow: hidden; }
        .email-body img { max-width: 100%; height: auto; }
        .email-body img:not([src]) { display: inline-block; background-color: #e0e0e0; }
        .email-body table { max-width: 100%; table-layout: fixed; }
        .email-body pre { white-space: pre-wrap; overflow-wrap: break-word; }
        .email-body * { max-width: 100%; }

        @page { margin: 0; }


        /* Avatar Container Styling */
        .avatar-circle {
            width: 42px;
            height: 42px;
            background-color: #e0e0e0; /* Neutral light grey background */
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        /* Person Icon Styling */
        .avatar-icon {
            width: 24px;
            height: 24px;
            fill: #4a4a4a; /* Neutral dark grey silhouette */
        }
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


class ParsedEmail(BaseModel):
    html_body: str
    attachment_names: list[str] = []
    attachment_sizes: list[int] = []


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
        <h4 style="padding: 3px 0; font-weight: bold;"> {nh3.escape(data['Subject'])}</h4>

        <!-- Main Layout Table -->
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; color: #333333; margin-bottom: 15px;">
            <tr>
                <!-- Left Column: Avatar Container -->
                <td style="width: 55px; vertical-align: top; padding-top: 3px;">
                    <div class="avatar-circle">
                        <!-- Inline HTML Person SVG Icon -->
                        <svg class="avatar-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                    </div>
                </td>
    {email_html_right_col}
            </tr>
        </table>
    {email_attachments}

        <div class="email-body">{sanitized_body}</div>

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

    attachments = []
    for index, name in enumerate(email_data.attachment_names):
        size = email_data.attachment_sizes[index]
        attachments.append(name + " " + size_to_string(size))

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


def _parse_email_body(
    msg: EmailMessage,
) -> ParsedEmail:
    # pylint: disable=too-many-locals

    html_body = ""
    plain_body = ""
    cid_map = {}
    attachment_names = []
    attachment_sizes = []

    for part in msg.walk():

        # Continue for multipart container
        if part.is_multipart():
            continue

        # Continue for empty payload
        if part.get_payload() is None:
            continue

        # Save attachment names
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if filename:
                attachment_names.append(filename)
                data = part.get_payload(decode=True) or b""
                attachment_sizes.append(len(data))

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
        attachment_names=attachment_names,
        attachment_sizes=attachment_sizes,
    )
