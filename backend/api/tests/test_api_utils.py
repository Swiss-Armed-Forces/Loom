from urllib.parse import unquote

import pytest

from api.utils import CONTENT_DISPOSITION_HEADER_PREFIX, get_content_disposition_header


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
def test_get_content_disposition_header(file_name: str):
    """Test the encoding of various UTF-8 strings as content_disposition_name."""

    header_value = get_content_disposition_header(file_name)["Content-Disposition"]
    assert header_value.startswith(CONTENT_DISPOSITION_HEADER_PREFIX)

    content_disposition_file_name = header_value.removeprefix(
        CONTENT_DISPOSITION_HEADER_PREFIX
    )
    decoded_file_name = unquote(content_disposition_file_name)
    assert file_name == decoded_file_name
