import logging
from imaplib import IMAP4
from pathlib import Path, PurePath

import requests

from worker.settings import settings

logger = logging.getLogger(__name__)

EMAIL_RSPAMD_TIMEOUT = 1200
EMAIL_IMAP_TIMEOUT = 1200

# see /etc/mime.types
EMAIL_MIMETYPES = ["message/rfc822"]

EMAIL_EXTENSIONS = [
    ".eml",
]


class ImapOperationException(Exception):
    pass


def sanitize_imap_folder_name(folder_name: str) -> str:
    """Sanitizes a directory structure string to be compatible with the IMAP CREATE
    command, allowing directory structures with slashes but preventing double slashes
    (//).

    Args:
        folder_name (str): The directory structure string to sanitize.

    Returns:
        str: A sanitized version of the folder name that complies with IMAP rules,
             with slashes for directories and no double slashes.

    Example:
        sanitize_imap_folder_name("folder1/folder2/folder3/file")
        -> "folder1/folder2/folder3/file"

        sanitize_imap_folder_name("folder1//folder2")
        -> "folder1/folder2"
    """
    # Strip leading/trailing whitespace
    folder_name = folder_name.strip()

    # Split the folder path by slashes to handle each part individually
    parts = folder_name.split("/")

    # Define valid characters for folder/file names
    valid_chars = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-_+"
    )

    # Initialize a list to collect sanitized parts
    sanitized_parts = []

    for part in parts:
        # Skip empty parts that result from consecutive slashes (e.g., "//")
        if not part:
            continue

        # Sanitize the individual part
        sanitized_part = [char for char in part if char in valid_chars]

        # Join the valid characters into a string and append to sanitized_parts
        sanitized_parts.append("".join(sanitized_part))

    # Rebuild the folder structure, ensuring no double slashes (//)
    sanitized_folder = "/".join(sanitized_parts)

    # Ensure no trailing slash or period
    if sanitized_folder.endswith((".", "/")):
        sanitized_folder = sanitized_folder[:-1]

    return sanitized_folder


def is_email(extension: str, mimetype: str) -> bool:
    return extension in EMAIL_EXTENSIONS or mimetype in EMAIL_MIMETYPES


def detect_spam(data: memoryview) -> bool:
    response = requests.post(
        f"{settings.rspam_host}symbols", data, timeout=EMAIL_RSPAMD_TIMEOUT
    )
    response.raise_for_status()
    json_response = response.json()
    return bool(json_response["default"]["is_spam"])


def upload_email_to_imap(email_path: PurePath, data: memoryview):
    email_dir = f"{settings.imap_directory}/{Path(email_path).parent}"
    email_dir_sanitized = sanitize_imap_folder_name(email_dir)
    with IMAP4(
        settings.imap_host.host if settings.imap_host.host is not None else "",
        timeout=EMAIL_IMAP_TIMEOUT,
    ) as imap:
        imap.login(settings.imap_user, settings.imap_password)
        create_response = imap.create(email_dir_sanitized)
        match create_response:
            case ["OK", _]:
                pass
            case ["NO", imap_data] if b"[ALREADYEXISTS]" in imap_data[0]:
                pass
            case _:
                raise ImapOperationException(str(data))
        imap.append(email_dir_sanitized, "", "", data)
