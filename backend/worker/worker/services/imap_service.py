import email
import hashlib
import re
from contextlib import contextmanager
from pathlib import PurePath

from common.file.file_repository import ImapInfo
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from pydantic import AnyUrl


def _get_email_deduplication_fingerprint(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()


IMAP_DEDUPLICATION_HEADER = "X-Deduplication-Upload-Hash"
IMAP_TIMEOUT = 1200
IMAP_DIRECTORY_BASE = PurePath("INBOX")


class IMAPServiceError(Exception):
    pass


class IMAPService:

    def __init__(self, imap_host: AnyUrl, user: str, password: str):
        self.host = imap_host
        self.user = user
        self.password = password

    @staticmethod
    def get_imap_folder(folder: PurePath | None) -> PurePath:
        if folder is None:
            return IMAP_DIRECTORY_BASE
        folder_path = IMAP_DIRECTORY_BASE / folder.relative_to(folder.anchor)
        return folder_path

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

    def count_messages(
        self, folder: PurePath | None = None, recurse: bool = False
    ) -> int:
        """Counts messages in a folder.

        - recurse=False: counts only the specified folder.
        - recurse=True: counts folder + all subfolders recursively.
        Raises IMAPServiceError on failure.
        """
        root = self.get_imap_folder(folder)

        with self._imap_context() as client:

            def _status_messages(mailbox: str) -> int:
                try:
                    status = client.folder_status(mailbox, [b"MESSAGES"])
                except IMAPClientError as e:
                    raise IMAPServiceError(
                        f"Failed to get STATUS for mailbox '{mailbox}': {e}"
                    ) from e

                messages = status.get(b"MESSAGES")
                if not isinstance(messages, int):
                    raise IMAPServiceError(
                        f"Unexpected STATUS response for mailbox '{mailbox}': {status}"
                    )
                return messages

            if not recurse:
                return _status_messages(str(root))

            # Recursive mode
            all_folders = client.list_folders()
            delimiter = next((d for _, d, _ in all_folders if d), b"/").decode()

            try:
                subtree = client.list_folders(
                    directory="", pattern=f"{root}{delimiter}*"
                )
            except IMAPClientError as e:
                raise IMAPServiceError(
                    f"Failed to list folder subtree for '{root}': {e}"
                ) from e

            mailboxes: set[str] = {str(root)}

            for flags, _, name in subtree:
                if self._is_noselect(flags):
                    continue
                if isinstance(name, bytes):
                    name = name.decode()
                mailboxes.add(name)

            return sum(_status_messages(mbox) for mbox in mailboxes)

    def create_folder(self, folder: PurePath):
        with self._imap_context() as client:
            client.create_folder(str(self.get_imap_folder(folder)))

    def get_uid_of_email(
        self, raw_email: bytes, folder: PurePath | None = None
    ) -> int | None:
        deduplication_finterprint = _get_email_deduplication_fingerprint(raw_email)
        imap_folder = self.get_imap_folder(folder)

        with self._imap_context() as client:
            try:
                client.select_folder(str(imap_folder))
            except IMAPClientError:
                # likely: folder does not exist
                return None
            uids = client.search(
                ["HEADER", IMAP_DEDUPLICATION_HEADER, deduplication_finterprint]  # type: ignore
            )
            return uids[-1] if uids else None

    def append_email(
        self, raw_email: bytes, folder: PurePath | None = None
    ) -> ImapInfo:
        deduplication_finterprint = _get_email_deduplication_fingerprint(raw_email)

        imap_folder = self.get_imap_folder(folder)
        # Append with deterministic header
        email_parsed = email.message_from_bytes(raw_email)
        email_parsed[IMAP_DEDUPLICATION_HEADER] = deduplication_finterprint

        with self._imap_context() as client:
            try:
                client.create_folder(str(imap_folder))
            except IMAPClientError:
                pass  # skip b"[ALREADYEXISTS]"

            # Check if server supports UIDPLUS
            response = client.append(str(imap_folder), email_parsed.as_bytes())
            if isinstance(response, bytes) and b"UIDPLUS" in client.capabilities():
                # Response format: [APPENDUID uidvalidity uid]
                match = re.search(rb"\[APPENDUID\s+(\d+)\s+(\d+)\]", response)
                if match:
                    uid_raw = match.group(2)
                    uid = int(uid_raw)
                    return ImapInfo(
                        uid=uid,
                        folder=imap_folder,
                    )
            # Fallback to search method
            found_uid = self.get_uid_of_email(raw_email, folder)
            if found_uid is None:
                raise IMAPServiceError("Failed to find the appended email UID.")
            return ImapInfo(
                uid=found_uid,
                folder=imap_folder,
            )

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
