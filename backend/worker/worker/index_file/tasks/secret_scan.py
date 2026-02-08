import json
import logging
import subprocess

from celery import chain, group
from celery.canvas import Signature
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File, Secret
from common.services.lazybytes_service import LazyBytes

from worker.index_file.infra.file_indexing_task import FileIndexingTask
from worker.index_file.infra.indexing_persister import IndexingPersister
from worker.services.tika_service import TikaResult
from worker.utils.persisting_task import persisting_task

logger = logging.getLogger(__name__)
app = get_celery_app()


def signature(file: File) -> Signature:
    return chain(
        extract_text_from_tika_result.s(),
        group(
            chain(
                trufflehog_scan_task.s(file.extension),
                persist_trufflehog_scan_task.s(file),
            ),
            chain(
                ripsecrets_scan_task.s(file.extension),
                persist_ripsecrets_scan_task.s(file),
            ),
        ),
    )


@app.task(base=FileIndexingTask)
def extract_text_from_tika_result(tika_result: TikaResult) -> LazyBytes | None:
    return tika_result.text


@app.task(base=FileIndexingTask)
def ripsecrets_scan_task(
    tika_text: LazyBytes | None, extension: str
) -> list[Secret] | None:
    if tika_text is None:
        return None
    with get_lazybytes_service().load_file_named(
        lazy_bytes=tika_text, suffix=extension
    ) as fd:
        proc = subprocess.run(
            ["ripsecrets", fd.name],
            capture_output=True,
            text=True,
            check=False,
        )

    if not proc.stdout.strip():
        return []

    return parse_ripsecrets_output(proc.stdout)


@app.task(base=FileIndexingTask)
def trufflehog_scan_task(
    tika_text: LazyBytes | None, extension: str
) -> list[Secret] | None:
    if tika_text is None:
        return None
    with get_lazybytes_service().load_file_named(
        lazy_bytes=tika_text, suffix=extension
    ) as fd:
        proc = subprocess.run(
            ["trufflehog", "filesystem", fd.name, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )

    if not proc.stdout.strip():
        return []

    return parse_trufflehog_output(proc.stdout)


def parse_ripsecrets_output(output: str) -> list[Secret]:
    secrets: list[Secret] = []
    for line in output.splitlines():
        if not line.strip():
            continue

        # Ripsecrets output is separated by ':' in this format -> path:line_number:secret
        try:
            secret_entry_parts = line.split(":", 2)
            if len(secret_entry_parts) != 3:
                raise ValueError("ripsecret output does not contain 3 parts")
        except ValueError as ex:
            logger.warning(
                "Could not parse ripsecrets results line: '%s'", line, exc_info=ex
            )
            continue

        secrets.append(
            Secret(
                line_number=int(secret_entry_parts[1]),
                secret=secret_entry_parts[2],
            )
        )
    return secrets


def parse_trufflehog_output(output: str) -> list[Secret]:
    secrets: list[Secret] = []
    for line in output.splitlines():
        try:
            data = json.loads(line)
            secret_value = data["Raw"]
            fs_meta = data["SourceMetadata"]["Data"]["Filesystem"]
            line_number = fs_meta.get("line", None)
        except (json.JSONDecodeError, KeyError) as ex:
            logger.warning(
                "Could not parse trufflehog results line: '%s'", line, exc_info=ex
            )
            continue

        secrets.append(
            Secret(
                line_number=line_number,
                secret=secret_value,
            )
        )

    return secrets


@persisting_task(app, IndexingPersister)
def persist_ripsecrets_scan_task(
    persister: IndexingPersister, secrets: list[Secret] | None
):
    if secrets is None:
        return
    persister.set_ripsecrets_secret(secrets)


@persisting_task(app, IndexingPersister)
def persist_trufflehog_scan_task(
    persister: IndexingPersister, secrets: list[Secret] | None
):
    if secrets is None:
        return
    persister.set_trufflehog_secret(secrets)
