import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_imap_service, get_lazybytes_service
from common.file.file_repository import File, ImapInfo
from common.services.lazybytes_service import LazyBytes
from httpx import HTTPStatusError

from worker.dependencies import get_gotenberg_client, get_rspamd_service
from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.index_file.tasks import create_thumbnail, render
from worker.index_file.tasks.render import RenderFile
from worker.settings import settings
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)

app = get_celery_app()

# see /etc/mime.types
EMAIL_MIMETYPES = ["message/rfc822"]
EMAIL_EXTENSIONS = [
    ".eml",
]
EMAIL_RENDER_EXPRESSION_JAVASCRIPT = """
(
    document.readyState === 'complete'
    && !!document.querySelector('#messagebody')
    && Array.from(
        document.querySelectorAll('#messagebody img, #attachment-list img')
    ).every(i => i.complete)
    && (!document.fonts || document.fonts.status === 'loaded')
)
"""


def signature(file_content: LazyBytes, file: File) -> Signature:
    return chain(
        detect_email_task.s(file.extension),
        group(
            chain(detect_spam_task.s(file_content), persist_spam_task.s(file)),
            chain(
                upload_email_to_imap_task.s(file_content, file),
                group(
                    persist_imap_info.s(file),
                    chain(
                        render_email_to_image.s(),
                        create_thumbnail.signature_pass_file_content(file),
                    ),
                    chain(
                        render_email_to_pdf.s(),
                        render.signature_pass_file_content(
                            file,
                            RenderFile(short_name=file.short_name, extension=".pdf"),
                        ),
                    ),
                ),
            ),
        ),
    )


def is_email(extension: str, mimetype: str) -> bool:
    return extension in EMAIL_EXTENSIONS or mimetype in EMAIL_MIMETYPES


@app.task(base=FileIndexingTask)
def detect_email_task(
    tika_file_type: str,
    file_extension: str,
) -> bool:
    return is_email(extension=file_extension, mimetype=tika_file_type)


@app.task(base=FileIndexingTask)
def detect_spam_task(
    is_email_detected: bool,
    file_content: LazyBytes,
) -> bool:
    if not is_email_detected:
        return False

    rspamd_service = get_rspamd_service()

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        is_spam = rspamd_service.detect_spam(memview)
        return is_spam


@persisting_task(app, IndexingPersister)
def persist_spam_task(persister: IndexingPersister, is_spam: bool):
    persister.set_is_spam(is_spam)


@app.task(base=FileIndexingTask)
def upload_email_to_imap_task(
    is_email_detected: bool,
    file_content: LazyBytes,
    file: File,
) -> ImapInfo | None:

    if not is_email_detected:
        return None

    imap_service = get_imap_service()
    email_file = file.full_path
    email_folder = file.full_path.parent

    with get_lazybytes_service().load_memoryview(file_content) as memview:
        email = bytes(memview)
        uid = imap_service.get_uid_of_email(email, email_folder)
        if uid:
            logger.info(
                "Not uploading, IMAP deduplication: %s",
                email_file,
            )
            return ImapInfo(
                uid=uid,
                folder=imap_service.get_imap_folder(email_folder),
            )
        imap_info = imap_service.append_email(email, email_folder)
        return imap_info


@persisting_task(app, IndexingPersister)
def persist_imap_info(persister: IndexingPersister, imap_info: ImapInfo | None):
    if imap_info is None:
        return
    persister.set_imap_info(imap_info)


def _get_roundcube_email_url(imap_info: ImapInfo) -> str:
    """Generate Roundcube email viewer URL."""
    params = {
        "_task": "mail",
        "_extwin": "1",
        "_action": "print",
        "_uid": str(imap_info.uid),
        "_mbox": imap_info.folder,
    }

    query_string = urlencode(params)
    return f"{settings.roundcube_host}?{query_string}"


@app.task(base=FileIndexingTask)
def render_email_to_image(
    imap_info: ImapInfo | None,
) -> LazyBytes | None:
    if imap_info is None:
        return None

    with get_gotenberg_client().chromium.screenshot_url() as route:
        email_url = _get_roundcube_email_url(imap_info)
        route = route.url(email_url)
        route = route.width(settings.rendered_image_width)
        route = route.use_network_idle()
        route = route.render_expression(EMAIL_RENDER_EXPRESSION_JAVASCRIPT)
        try:
            response = route.run()
        except HTTPStatusError:
            logger.warning("Unable to render email as image in browser", exc_info=True)
            return None
        with NamedTemporaryFile("rb", dir=settings.tempfile_dir) as fd:
            response.to_file(Path(fd.name))
            lazy_bytes = get_lazybytes_service().from_file(fd)
        return lazy_bytes


@app.task(base=FileIndexingTask)
def render_email_to_pdf(
    imap_info: ImapInfo | None,
) -> LazyBytes | None:
    if imap_info is None:
        return None

    with get_gotenberg_client().chromium.url_to_pdf() as route:
        email_url = _get_roundcube_email_url(imap_info)
        route = route.url(email_url)
        route = route.use_network_idle()
        route = route.size(size=settings.rendered_pdf_page_size)
        route = route.render_expression(EMAIL_RENDER_EXPRESSION_JAVASCRIPT)
        try:
            response = route.run()
        except HTTPStatusError:
            logger.warning("Unable to render email to pdf in browser", exc_info=True)
            return None
        file_content = get_lazybytes_service().from_bytes(response.content)
    return file_content
