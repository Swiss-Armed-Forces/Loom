from typing import Literal
from urllib.parse import unquote

import pytest

from api.utils import FILENAME_ENCODING, get_content_disposition_header


@pytest.mark.parametrize(
    "disposition_type",
    [
        "inline",
        "attachment",
    ],
)
def test_get_content_disposition_header(
    disposition_type: Literal["inline", "attachment"],
):
    header_value = get_content_disposition_header(disposition_type)[
        "Content-Disposition"
    ]
    assert header_value == disposition_type


@pytest.mark.parametrize(
    "file_name",
    [
        "一隻貓睡在椅子上的照片",
        "कुर्सी पर सो रही बिल्ली की तस्वीर",
        "фото кота спящего на стуле",
        "תמונה של חתול ישן על כיסא",
        "صورة قطة نائمة على كرسي",
        "zdjęcie kota śpiącego na krześle",
        "εικόνα μιας γάτας που κοιμάται σε μια καρέκλα",
    ],
)
def test_get_content_disposition_header_filename_encoding(file_name: str):
    """Test the encoding of various UTF-8 strings as content_disposition_name."""

    header_value = get_content_disposition_header("attachment", file_name)[
        "Content-Disposition"
    ]
    assert FILENAME_ENCODING in header_value

    _, _, encoded_file_name = header_value.partition(FILENAME_ENCODING)
    decoded_file_name = unquote(encoded_file_name)
    assert file_name == decoded_file_name
