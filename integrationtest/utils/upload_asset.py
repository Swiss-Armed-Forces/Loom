from hashlib import sha256
from io import BytesIO
from typing import Optional

import requests
from api.routers.files import FileUploadResponse
from requests import Response
from requests_toolbelt import MultipartEncoder

from utils.consts import ASSETS_DIR, FILES_ENDPOINT, REQUEST_TIMEOUT


def upload_asset(
    asset_name: str,
    upload_file_name: Optional[str] = None,
    request_timeout=REQUEST_TIMEOUT,
) -> FileUploadResponse:
    """Upload a file from the assets dir to the API.

    :param asset_name: Name of the file in the assets dir
    :param upload_file_name: Name that will be used for the upload, if not provided, the
        asset name will be used
    """
    asset = ASSETS_DIR / asset_name

    if not upload_file_name:
        upload_file_name = asset_name

    with open(asset, "rb") as asset_file:
        multipart_form_data = {
            "file": (upload_file_name, asset_file),
        }
        encoder = MultipartEncoder(multipart_form_data)

        api_response: Response = requests.post(
            f"{FILES_ENDPOINT}/",
            data=encoder,
            headers={"Content-Type": encoder.content_type},
            timeout=request_timeout,
        )
        api_response.raise_for_status()

    return FileUploadResponse(**api_response.json())


def upload_many_assets(
    asset_names: list,
    upload_file_names: Optional[list] = None,
    request_timeout=REQUEST_TIMEOUT,
) -> list[FileUploadResponse]:
    """Upload a list of files from the assets dir to the API.

    :param asset_names: List of names of the files in the assets dir
    :param upload_file_names: List of names that will be used for the uploads, if not
        provided, the original names will be used
    """
    if upload_file_names is None:
        upload_file_names = [None] * len(asset_names)
    if len(upload_file_names) < len(asset_names):
        upload_file_names.extend([None] * (len(asset_names) - len(upload_file_names)))

    responses = []

    for index, asset_name in enumerate(asset_names):
        upload_file_name = (
            upload_file_names[index]
            if upload_file_names[index] is not None
            else asset_name
        )
        response = upload_asset(
            asset_name=asset_name,
            upload_file_name=upload_file_name,
            request_timeout=request_timeout,
        )
        responses.append(response)

    return responses


def upload_bytes_asset(
    bytes_to_upload: bytes,
    upload_file_name: str | None = None,
    request_timeout=REQUEST_TIMEOUT,
) -> FileUploadResponse:
    """Upload a file which contains the given bytes.

    :param string_to_upload: The string to upload
    :param upload_file_name: Name that will be used for the upload, if not provided, the
        original name will be used
    """
    if not upload_file_name:
        upload_file_name = sha256(bytes_to_upload).hexdigest()

    api_response: Response = requests.post(
        f"{FILES_ENDPOINT}/",
        files={
            "file": (
                upload_file_name,
                BytesIO(bytes_to_upload),
            ),
            "action": (None, "store"),
            "path": (None, "/path1"),
        },
        timeout=request_timeout,
    )
    api_response.raise_for_status()

    return FileUploadResponse(**api_response.json())
