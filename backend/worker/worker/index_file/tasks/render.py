import logging
from enum import Enum
from pathlib import Path

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import (
    get_celery_app,
    get_file_storage_service,
    get_lazybytes_service,
)
from common.file.file_repository import File
from common.services.lazybytes_service import LazyBytes
from common.utils.cache import cache
from common.utils.object_id_str import ObjectIdStr
from httpx import HTTPStatusError
from pydantic import BaseModel
from wand.exceptions import MissingDelegateError, WandException
from wand.image import Image

from worker.dependencies import get_gotenberg_client
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()


class RenderFile(BaseModel):
    short_name: str
    extension: str
    cache_key: str

    @staticmethod
    def from_file(file: File) -> "RenderFile":
        return RenderFile(
            short_name=file.short_name, extension=file.extension, cache_key=file.sha256
        )


class RenderType(Enum):
    IMAGE = "image"
    BROWSER = "browser"
    OFFICE = "office"


BROWSER_RENDER_EXTENSIONS = {
    # spellchecker: off
    ".html",
    ".htm",
    ".xhtml",
    ".shtml",
    ".shtm",  # HTML variants
    ".svg",
    ".svgz",  # SVG graphics
    ".mhtml",
    ".mht",  # MHTML (web archive)
    # spellchecker:on
}


# from: https://gotenberg.dev/docs/routes#office-documents-into-pdfs-route
OFFICE_RENDER_EXTENSIONS = {
    # spellchecker:off
    ".123",
    ".602",
    ".abw",
    ".bib",
    ".bmp",
    ".cdr",
    ".cgm",
    ".cmx",
    ".csv",
    ".cwk",
    ".dbf",
    ".dif",
    ".doc",
    ".docm",
    ".docx",
    ".dot",
    ".dotm",
    ".dotx",
    ".dxf",
    ".emf",
    ".eps",
    ".epub",
    ".fodg",
    ".fodp",
    ".fods",
    ".fodt",
    ".fopd",
    ".gif",
    ".htm",
    ".html",
    ".hwp",
    ".jpeg",
    ".jpg",
    ".key",
    ".ltx",
    ".lwp",
    ".mcw",
    ".met",
    ".mml",
    ".mw",
    ".numbers",
    ".odd",
    ".odg",
    ".odm",
    ".odp",
    ".ods",
    ".odt",
    ".otg",
    ".oth",
    ".otp",
    ".ots",
    ".ott",
    ".pages",
    ".pbm",
    ".pcd",
    ".pct",
    ".pcx",
    ".pdb",
    ".pdf",
    ".pgm",
    ".png",
    ".pot",
    ".potm",
    ".potx",
    ".ppm",
    ".pps",
    ".ppt",
    ".pptm",
    ".pptx",
    ".psd",
    ".psw",
    ".pub",
    ".pwp",
    ".pxl",
    ".ras",
    ".rtf",
    ".sda",
    ".sdc",
    ".sdd",
    ".sdp",
    ".sdw",
    ".sgl",
    ".slk",
    ".smf",
    ".stc",
    ".std",
    ".sti",
    ".stw",
    ".svg",
    ".svm",
    ".swf",
    ".sxc",
    ".sxd",
    ".sxg",
    ".sxi",
    ".sxm",
    ".sxw",
    ".tga",
    ".tif",
    ".tiff",
    ".txt",
    ".uof",
    ".uop",
    ".uos",
    ".uot",
    ".vdx",
    ".vor",
    ".vsd",
    ".vsdm",
    ".vsdx",
    ".wb2",
    ".wk1",
    ".wks",
    ".wmf",
    ".wpd",
    ".wpg",
    ".wps",
    ".xbm",
    ".xhtml",
    ".xls",
    ".xlsb",
    ".xlsm",
    ".xlsx",
    ".xlt",
    ".xltm",
    ".xltx",
    ".xlw",
    ".xml",
    ".xpm",
    ".zabw",
    # spellchecker:on
}


def signature(file: File, file_content: LazyBytes) -> Signature:
    render_file = RenderFile.from_file(file)
    return group(
        chain(
            render_image_png_task.s(file_content, render_file),
            upload_rendered_task.s(render_file, RenderType.IMAGE),
            persist_rendered_file_image_file_id_task.s(file),
        ),
        chain(
            render_browser_to_pdf_task.s(file_content, render_file),
            upload_rendered_task.s(render_file, RenderType.BROWSER),
            persist_rendered_file_browser_pdf_file_id_task.s(file),
        ),
        chain(
            render_office_to_pdf_task.s(file_content, render_file),
            upload_rendered_task.s(render_file, RenderType.OFFICE),
            persist_rendered_file_office_pdf_file_id_task.s(file),
        ),
    )


def signature_pass_file_content(
    file: File,
    render_file: RenderFile,
) -> Signature:
    return group(
        chain(
            render_image_png_task.s(render_file),
            upload_rendered_task.s(render_file, RenderType.IMAGE),
            persist_rendered_file_image_file_id_task.s(file),
        ),
        chain(
            render_browser_to_pdf_task.s(render_file),
            upload_rendered_task.s(render_file, RenderType.BROWSER),
            persist_rendered_file_browser_pdf_file_id_task.s(file),
        ),
        chain(
            render_office_to_pdf_task.s(render_file),
            upload_rendered_task.s(render_file, RenderType.OFFICE),
            persist_rendered_file_office_pdf_file_id_task.s(file),
        ),
    )


@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, render_file: render_file.cache_key)
def render_image_png_task(
    file_content: LazyBytes | None, _: RenderFile
) -> LazyBytes | None:
    if file_content is None:
        return None

    try:
        with (
            get_lazybytes_service().load_file(file_content) as fd,
            Image(file=fd, resolution=settings.rendered_image_resolution) as image,
        ):
            image.smush(stacked=True, offset=settings.rendered_image_smush_offset)
            image.transform(resize=f"{settings.rendered_image_width}>")
            image.unsharp_mask()
            blob = image.make_blob(format="png")
    except (MissingDelegateError, WandException):
        logger.warning(
            "Unable to render image with Wand",
            exc_info=True,
        )
        return None

    if not isinstance(blob, bytes):
        return None

    blob_lazy = get_lazybytes_service().from_bytes(blob)
    return blob_lazy


@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, render_file: render_file.cache_key)
def render_browser_to_pdf_task(
    file_content: LazyBytes | None,
    render_file: RenderFile,
) -> LazyBytes | None:
    if file_content is None:
        return None

    if render_file.extension not in BROWSER_RENDER_EXTENSIONS:
        return None

    with (
        get_gotenberg_client().chromium.html_to_pdf() as route,
        get_lazybytes_service().load_file_named(file_content) as fd,
    ):
        route = route.index(Path(fd.name))
        route = route.size(size=settings.rendered_pdf_page_size)
        route = route.use_network_idle()
        try:
            response = route.run()
        except HTTPStatusError:
            logger.warning("Unable to render pdf in browser", exc_info=True)
            return None
        pdf_lazy = get_lazybytes_service().from_bytes(response.content)
        return pdf_lazy


@app.task(base=FileIndexingTask)
@cache(key_function=lambda _, render_file: render_file.cache_key)
def render_office_to_pdf_task(
    file_content: LazyBytes,
    render_file: RenderFile,
) -> LazyBytes | None:
    if file_content is None:
        return None
    if render_file.extension not in OFFICE_RENDER_EXTENSIONS:
        return None
    with (
        get_gotenberg_client().libre_office.to_pdf() as route,
        get_lazybytes_service().load_file_named(
            lazy_bytes=file_content, suffix=render_file.extension
        ) as fd,
    ):
        route = route.convert(Path(fd.name))
        try:
            response = route.run()
        except HTTPStatusError:
            logger.warning("Unable to render pdf in libretranslate", exc_info=True)
            return None
        pdf_lazy = get_lazybytes_service().from_bytes(response.content)
        return pdf_lazy


@app.task(base=FileIndexingTask)
def upload_rendered_task(
    rendered_lazy: LazyBytes | None,
    render_file: RenderFile,
    render_type: RenderType,
) -> ObjectIdStr | None:
    if rendered_lazy is None:
        return None
    with get_lazybytes_service().load_file(rendered_lazy) as fd:
        file_id = get_file_storage_service().upload_from_stream(
            f"{render_file.short_name}.{render_type.value}-rendered.{render_file.extension}",
            fd,
        )
    return ObjectIdStr(file_id)


@persisting_task(app, IndexingPersister)
def persist_rendered_file_image_file_id_task(
    persister: IndexingPersister, rendered_file_image_file_id: ObjectIdStr | None
):
    if rendered_file_image_file_id is None:
        return
    persister.set_rendered_file_image_file_id(rendered_file_image_file_id)


@persisting_task(app, IndexingPersister)
def persist_rendered_file_browser_pdf_file_id_task(
    persister: IndexingPersister, rendered_file_browser_pdf_file_id: ObjectIdStr | None
):
    if rendered_file_browser_pdf_file_id is None:
        return
    persister.set_rendered_file_browser_pdf_file_id(rendered_file_browser_pdf_file_id)


@persisting_task(app, IndexingPersister)
def persist_rendered_file_office_pdf_file_id_task(
    persister: IndexingPersister, rendered_file_office_pdf_file_id: ObjectIdStr | None
):
    if rendered_file_office_pdf_file_id is None:
        return
    persister.set_rendered_file_office_pdf_file_id(rendered_file_office_pdf_file_id)
