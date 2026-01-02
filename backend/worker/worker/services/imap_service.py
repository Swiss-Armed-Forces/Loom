import email
import hashlib
from contextlib import contextmanager
from email.policy import default
from pathlib import PurePath

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from pydantic import AnyUrl


def _get_email_deduplication_fingerprint(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()


IMAP_DEDUPLICATION_HEADER = "X-Deduplication-Upload-Hash"
IMAP_TIMEOUT = 1200
IMAP_DIRECTORY_BASE = PurePath("INBOX")


class IMAPService:

    def __init__(self, imap_host: AnyUrl, user: str, password: str):
        self.host = imap_host
        self.user = user
        self.password = password

    @contextmanager
    def _imap_context(self):
        with IMAPClient(
            host=self.host.host if self.host.host else "",
            port=self.host.port if self.host.port else 143,
            ssl=False,
            timeout=IMAP_TIMEOUT,
        ) as client:
            client.login(self.user, self.password)
            yield client

    @staticmethod
    def _imap_folder(folder: PurePath | None) -> str:
        if folder is None:
            return str(IMAP_DIRECTORY_BASE)
        folder_path = str(IMAP_DIRECTORY_BASE / folder.relative_to(folder.anchor))
        return folder_path

    def count_messages(self, folder: PurePath | None = None) -> int:
        with self._imap_context() as client:

            select_info = client.select_folder(self._imap_folder(folder))
            return int(select_info[b"EXISTS"])

    def create_folder(self, folder: PurePath):
        with self._imap_context() as client:
            client.create_folder(self._imap_folder(folder))

    def contains_email(self, raw_email: bytes, folder: PurePath | None = None) -> bool:
        deduplication_finterprint = _get_email_deduplication_fingerprint(raw_email)
        imap_folder = self._imap_folder(folder)

        with self._imap_context() as client:
            try:
                client.select_folder(imap_folder)
            except IMAPClientError:
                # likely: folder does not exist
                return False
            search_info = client.search(
                ["HEADER", IMAP_DEDUPLICATION_HEADER, deduplication_finterprint]  # type: ignore
            )
            return len(search_info) > 0

    def append_email(self, raw_email: bytes, folder: PurePath | None = None):
        deduplication_finterprint = _get_email_deduplication_fingerprint(raw_email)

        imap_folder = self._imap_folder(folder)
        # Append with deterministic header
        email_parsed = email.message_from_bytes(raw_email, policy=default)
        email_parsed[IMAP_DEDUPLICATION_HEADER] = deduplication_finterprint

        with self._imap_context() as client:
            try:
                client.create_folder(imap_folder)
            except IMAPClientError:
                pass  # skip b"[ALREADYEXISTS]"
            client.append(imap_folder, str(email_parsed))

    @staticmethod
    def _is_noselect(flags: list[bytes]) -> bool:
        # flags are typically bytes like br'\Noselect'
        return any(f.upper() == rb"\NOSELECT" for f in flags)

    def wipe(self):
        with self._imap_context() as client:
            folders = (
                client.list_folders()
            )  # [(flags, delimiter, name), ...]  :contentReference[oaicite:3]{index=3}
            # Try to pick a delimiter; servers are usually consistent.
            delimiter = next((d for _, d, _ in folders if d), b"/").decode()

            # 1) Empty all selectable folders (including INBOX)
            for flags, _, name in folders:
                if self._is_noselect(flags):
                    continue
                client.select_folder(name, readonly=False)
                uids = client.search(["ALL"])  # type: ignore
                if uids:
                    client.delete_messages(
                        uids
                    )  # sets \Deleted :contentReference[oaicite:4]{index=4}
                    client.expunge()  # permanently removes

            # 2) Delete folders deepest-first (skip IMAP_DIRECTORY_BASE)
            # Sort by depth so we delete subfolders before parents.
            deletable = []
            for _, _, name in folders:
                if PurePath(name.upper()) == IMAP_DIRECTORY_BASE:
                    continue
                deletable.append(name)

            deletable.sort(key=lambda n: (n.count(delimiter), len(n)), reverse=True)

            for name in deletable:
                client.delete_folder(name)  # :contentReference[oaicite:6]{index=6}

            # Ensure IMAP_DIRECTORY_BASE is empty at the end
            # (some servers auto-move things)
            client.select_folder(str(IMAP_DIRECTORY_BASE), readonly=False)
            uids = client.search(["ALL"])  # type: ignore
            if uids:
                client.delete_messages(uids)
                client.expunge()
