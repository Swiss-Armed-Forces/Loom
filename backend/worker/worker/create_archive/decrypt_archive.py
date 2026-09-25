"""Opening an encrypted loom archive, when this deployment's key fits.

Beside `index_archive.py` rather than in `tasks/`, where it used to live: every other
module in that package is a registered Celery task, and this one deliberately is not
-- see the docstring below. A plain function sitting among tasks is exactly what the
next person will read as "a task somebody forgot to register".
"""

import logging

from common.archive.archive_encryption_service import ArchiveEncryptionService
from common.services.encryption_service import FileEncryptionServiceException
from common.services.lazybytes_service import (
    FileStorageLazyBytes,
    FileStorageLazyBytesService,
)

logger = logging.getLogger(__name__)


def decrypt_loom_archive(
    encrypted_file: FileStorageLazyBytes,
    file_storage_service: FileStorageLazyBytesService,
    archive_encryption_service: ArchiveEncryptionService,
) -> FileStorageLazyBytes | None:
    """Decrypt an encrypted loom archive; return the plain zip, or None.

    A plain function rather than a Celery task, because `index_archive_task` has to know
    the *outcome* in order to route: a blob carrying the LOOMENC header that
    nevertheless fails to decrypt is not an archive this box can import, and it has to
    be indexed as an opaque file rather than silently going nowhere. That decision
    cannot be made inside a chain -- a task returning None there just makes every task
    after it do nothing, which is the bug this replaces.

    The services are arguments rather than looked up here, so that the branch below can
    be exercised against a real encryptor on a known key without anything being patched
    into place. `index_archive.ArchiveServices` is what resolves them in production.

    Failure is expected rather than exceptional. `archive_enc_master_key` is unset by
    default and `FileEncryptionService` then invents a random key per process, so an
    archive from any other deployment arrives here.
    """
    try:
        encrypted_generator = file_storage_service.load_generator(encrypted_file)
        decrypted_stream = archive_encryption_service.get_decrypted_stream(
            encrypted_generator
        )
        decrypted = file_storage_service.from_generator(decrypted_stream)
    # ValueError as well as the service's own exception, and it is the one that
    # actually fires for a wrong key: get_decrypted_stream ends with
    # `cipher.verify(mac)`, and PyCryptodome raises a bare
    # ValueError("MAC check failed") from there rather than anything this
    # codebase defines. Catching only FileEncryptionServiceException -- as this
    # did before -- let that escape and fail the task, so an archive from
    # another deployment went round the retry chain into the graveyard queue
    # instead of being indexed.
    except (FileEncryptionServiceException, ValueError):
        logger.info(
            "Encrypted loom archive did not decrypt with this deployment's master key"
        )
        return None

    logger.info("Successfully decrypted loom archive")
    return decrypted
