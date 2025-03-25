from typing import Dict
from urllib.parse import quote

CONTENT_DISPOSITION_HEADER_PREFIX = "attachment;filename*=UTF-8''"


def get_content_disposition_header(name: str | None) -> Dict[str, str]:
    """Returns the content disposition header filename of the name.

    The encoding is set to UTF-8 and the short_name is URL encoded.
    """
    if name is None:
        return {}
    url_encoded_name = quote(name.encode())
    return {
        "Content-Disposition": f"{CONTENT_DISPOSITION_HEADER_PREFIX}{url_encoded_name}"
    }
