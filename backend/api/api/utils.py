from typing import Dict, Literal
from urllib.parse import quote

FILENAME_ENCODING = "filename*=UTF-8''"


def get_content_disposition_header(
    disposition_type: Literal["inline", "attachment"] = "inline",
    name: str | None = None,
) -> Dict[str, str]:
    """Returns the content disposition header filename of the name.

    The encoding is set to UTF-8 and the name is URL encoded.
    """
    if name is None:
        return {"Content-Disposition": disposition_type}
    url_encoded_name = quote(name.encode())
    return {
        "Content-Disposition": (
            f"{disposition_type};{FILENAME_ENCODING}{url_encoded_name}"
        )
    }
