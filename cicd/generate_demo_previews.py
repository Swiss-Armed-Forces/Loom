"""Capture demo preview assets from a running Loom stack."""

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict
from uuid import uuid4

import requests

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIRECTORY = REPOSITORY_ROOT / "integrationtest" / "assets"
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "Frontend" / "src" / "demo" / "previews"


@dataclass(frozen=True)
class PreviewCapture:
    key: str
    source: Path
    renderer_outputs: tuple[tuple["RendererField", str], ...]


class FileEntry(TypedDict):
    file_id: str


class RendererOutputs(TypedDict, total=False):
    image_file_id: str
    office_pdf_file_id: str
    browser_pdf_file_id: str


RendererField = Literal[
    "image_file_id",
    "office_pdf_file_id",
    "browser_pdf_file_id",
]


class ApiResponse(TypedDict, total=False):
    files: list[FileEntry]
    rendered_file: RendererOutputs
    thumbnail_file_id: str
    thumbnail_total_frames: int


@dataclass(frozen=True)
class CapturedDocument:
    file_id: str
    detail: ApiResponse
    preview: ApiResponse


CAPTURES = (
    PreviewCapture(
        key="network-security",
        source=ASSETS_DIRECTORY / "knn1.txt",
        renderer_outputs=(("office_pdf_file_id", "network-security.pdf"),),
    ),
    PreviewCapture(
        key="basic-email",
        source=ASSETS_DIRECTORY / "basic_email.eml",
        renderer_outputs=(
            ("image_file_id", "basic-email.png"),
            ("office_pdf_file_id", "basic-email.pdf"),
        ),
    ),
    PreviewCapture(
        key="sample3",
        source=ASSETS_DIRECTORY / "sample3.docx",
        renderer_outputs=(("office_pdf_file_id", "sample3.pdf"),),
    ),
)


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    **kwargs: Any,
) -> ApiResponse:
    response = session.request(method, url, timeout=60, **kwargs)
    response.raise_for_status()
    value = response.json()
    if not isinstance(value, dict):
        raise TypeError(f"Expected an object from {url}")
    return ApiResponse(**value)


def upload_capture(
    session: requests.Session, files_endpoint: str, capture: PreviewCapture
) -> str:
    upload_name = f"demo-preview-{capture.key}-{uuid4().hex}{capture.source.suffix}"
    with capture.source.open("rb") as source_file:
        response = session.post(
            files_endpoint,
            files={"file": (upload_name, source_file)},
            timeout=60,
        )
    response.raise_for_status()
    return upload_name


def find_file_id(
    session: requests.Session, files_endpoint: str, upload_name: str
) -> str | None:
    payload = request_json(
        session,
        "GET",
        files_endpoint,
        params={"search_string": f'filename:"{upload_name}"'},
    )
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        return None
    file_id = files[0].get("file_id")
    return file_id if isinstance(file_id, str) else None


def wait_for_outputs(
    session: requests.Session,
    files_endpoint: str,
    upload_name: str,
    capture: PreviewCapture,
    timeout_seconds: int,
) -> CapturedDocument:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        file_id = find_file_id(session, files_endpoint, upload_name)
        if file_id is None:
            time.sleep(2)
            continue

        detail = request_json(
            session,
            "GET",
            f"{files_endpoint}/{file_id}",
            params={"search_string": "*"},
        )
        preview = request_json(
            session,
            "GET",
            f"{files_endpoint}/{file_id}/preview",
            params={"search_string": "*"},
        )
        rendered = detail.get("rendered_file")
        if not isinstance(rendered, dict):
            rendered = {}
        renderer_ids_ready = all(
            isinstance(rendered.get(field), str)
            for field, _output_name in capture.renderer_outputs
        )
        if isinstance(preview.get("thumbnail_file_id"), str) and renderer_ids_ready:
            return CapturedDocument(
                file_id=file_id,
                detail=detail,
                preview=preview,
            )
        time.sleep(2)

    raise TimeoutError(
        f"Loom did not finish rendering {upload_name} within {timeout_seconds}s"
    )


def download_asset(
    session: requests.Session, url: str, output_path: Path
) -> None:
    response = session.get(url, timeout=60)
    response.raise_for_status()
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_bytes(response.content)
    temporary_path.replace(output_path)


def get_renderer_id(outputs: RendererOutputs, field: RendererField) -> str:
    if field == "image_file_id":
        return outputs[field]
    if field == "office_pdf_file_id":
        return outputs[field]
    return outputs[field]


def capture_previews(api_url: str, timeout_seconds: int) -> None:
    files_endpoint = f"{api_url.rstrip('/')}/v1/files"
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        for capture in CAPTURES:
            upload_name = upload_capture(session, files_endpoint, capture)
            print(f"Uploaded {capture.source.name} as {upload_name}")
            captured = wait_for_outputs(
                session,
                files_endpoint,
                upload_name,
                capture,
                timeout_seconds,
            )
            thumbnail_id = captured.preview["thumbnail_file_id"]
            download_asset(
                session,
                f"{files_endpoint}/{captured.file_id}/thumbnail/{thumbnail_id}",
                OUTPUT_DIRECTORY / f"{capture.key}-thumbnail.png",
            )

            rendered = captured.detail["rendered_file"]
            for renderer_field, output_name in capture.renderer_outputs:
                rendered_id = get_renderer_id(rendered, renderer_field)
                download_asset(
                    session,
                    f"{files_endpoint}/{captured.file_id}/rendered/{rendered_id}",
                    OUTPUT_DIRECTORY / output_name,
                )
            print(f"Captured renderer outputs for {capture.source.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://api.loom")
    parser.add_argument("--timeout", type=int, default=600)
    arguments = parser.parse_args()
    capture_previews(arguments.api_url, arguments.timeout)


if __name__ == "__main__":
    main()
