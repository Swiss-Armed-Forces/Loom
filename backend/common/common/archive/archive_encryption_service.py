import logging

from common.services.encryption_service import AESMasterKey, FileEncryptionService

LOOM_ARCHIVE_MAGIC_BYTES = b"LOOMARCHIVE"

logger = logging.getLogger(__name__)


class ArchiveEncryptionService(FileEncryptionService):
    """Handles LOOM archive file encryption and decryption."""

    def __init__(self, master_key: AESMasterKey | None = None):
        super().__init__(master_key, LOOM_ARCHIVE_MAGIC_BYTES)
