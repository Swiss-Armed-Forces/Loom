import email
import hashlib
import re
from contextlib import contextmanager
from itertools import chain
from typing import Generator

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from pydantic import AnyUrl

from common.file.file_repository import FilePurePath, ImapInfo, ImapPurePath


def _get_email_deduplication_fingerprint(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()


class IMAPServiceError(Exception):
    pass


class IMAPServiceErrorFolderNotSelectable(IMAPServiceError):
    pass


IMAP_DEDUPLICATION_HEADER = "X-Deduplication-Upload-Hash"
IMAP_TIMEOUT = 1200
IMAP_DIRECTORY_BASE = ImapPurePath("INBOX")
IMAP_FOLDER_DELIMITER = "/"


class IMAPService:

    def __init__(self, imap_host: AnyUrl, user: str, password: str):
        self.host = imap_host
        self.user = user
        self.password = password

    @staticmethod
    def get_imap_folder(
        folder: ImapPurePath | FilePurePath | None = None,
    ) -> ImapPurePath:
        """Convert a full_path path to an IMAP folder path by prepending
        IMAP_DIRECTORY_BASE."""
        if isinstance(folder, ImapPurePath):
            return folder
        if folder is None:
            return IMAP_DIRECTORY_BASE
        folder_path = IMAP_DIRECTORY_BASE / folder.relative_to(folder.anchor)
        return ImapPurePath(folder_path)

    @staticmethod
    def get_folder(
        imap_folder: ImapPurePath | FilePurePath | None = None,
    ) -> FilePurePath | None:
        """Convert an IMAP folder path to a full_path path by removing
        IMAP_DIRECTORY_BASE."""
        if isinstance(imap_folder, FilePurePath):
            return imap_folder
        if imap_folder is None:
            return None
        if imap_folder == IMAP_DIRECTORY_BASE:
            return None
        # Remove IMAP_DIRECTORY_BASE prefix to get the relative folder path
        return FilePurePath(imap_folder.relative_to(IMAP_DIRECTORY_BASE))

    @contextmanager
    def _imap_context(self) -> Generator[IMAPClient, None, None]:
        with IMAPClient(
            host=self.host.host if self.host.host else "",
            port=self.host.port if self.host.port else 143,
            ssl=False,
            timeout=IMAP_TIMEOUT,
        ) as client:
            client.login(self.user, self.password)
            yield client

    @contextmanager
    def _select_folder(
        self,
        client: IMAPClient,
        imap_folder: ImapPurePath,
        readonly: bool = False,
    ) -> Generator[None, None, None]:
        try:
            client.select_folder(folder=str(imap_folder), readonly=readonly)
        except IMAPClientError as e:
            raise IMAPServiceErrorFolderNotSelectable(
                f"Can not select folder '{imap_folder}': '{e}'"
            ) from e
        yield
        client.unselect_folder()

    def count_messages(
        self, folder: ImapPurePath | FilePurePath | None = None, recurse: bool = False
    ) -> int:
        """Counts messages in a folder.

        - recurse=False: counts only the specified folder.
        - recurse=True: counts folder + all subfolders recursively.
        Raises IMAPServiceError on failure.
        """
        imap_folder = self.get_imap_folder(folder)

        with self._imap_context() as client:

            def _count_messages_in_folder(imap_folder: ImapPurePath) -> int:
                try:
                    status = client.folder_status(str(imap_folder), [b"MESSAGES"])
                except IMAPClientError:
                    return 0

                messages = status.get(b"MESSAGES")
                if not isinstance(messages, int):
                    raise IMAPServiceError(
                        f"Unexpected STATUS response for folder '{imap_folder}': {status}"
                    )
                return messages

            folders_to_count = chain([imap_folder])
            if recurse:
                folders_to_count = chain(
                    folders_to_count, self._iter_subfolders(client, imap_folder)
                )

            return sum(
                _count_messages_in_folder(imap_folder)
                for imap_folder in folders_to_count
            )

    def create_folder(self, folder: FilePurePath | ImapPurePath | None):
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client:
            client.create_folder(str(imap_folder))

    def get_uid_of_email(
        self, raw_email: bytes, folder: FilePurePath | ImapPurePath | None = None
    ) -> int | None:
        deduplication_finterprint = _get_email_deduplication_fingerprint(raw_email)
        imap_folder = self.get_imap_folder(folder)

        try:
            with self._imap_context() as client, self._select_folder(
                client, imap_folder, readonly=True
            ):
                try:
                    uids = client.search(
                        [
                            "HEADER",
                            IMAP_DEDUPLICATION_HEADER,
                            deduplication_finterprint,
                        ]  # type: ignore
                    )
                except IMAPClientError as e:
                    raise IMAPServiceError(
                        f"Can not search on folder '{folder}': '{e}'"
                    ) from e
                return uids[-1] if uids else None
        except IMAPServiceErrorFolderNotSelectable:
            return None

    def append_email(
        self, raw_email: bytes, folder: FilePurePath | ImapPurePath | None = None
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
            if not isinstance(response, bytes):
                raise IMAPServiceError("Append response not bytes")

            # Response format: [APPENDUID uidvalidity uid]
            match_regex = rb"\[APPENDUID\s+(\d+)\s+(\d+)\]"
            match = re.search(match_regex, response)
            if not match:
                raise IMAPServiceError(
                    f"Append response does not match '{match_regex!r}': '{response!r}'"
                )
            uid_raw = match.group(2)
            uid = int(uid_raw)
            return ImapInfo(
                uid=uid,
                folder=imap_folder,
            )

    def wipe(self):
        with self._imap_context() as client:
            imap_folders = list(
                self._iter_subfolders(client=client, imap_folder=IMAP_DIRECTORY_BASE)
            )

            # Sort by depth so later on we delete subfolders before parents.
            imap_folders.sort(
                key=lambda n: n.parts,
                reverse=True,
            )

            # 1) Empty all selectable folders
            for imap_folder in imap_folders:
                try:
                    with self._select_folder(client, imap_folder, readonly=False):
                        uids = client.search(["ALL"])  # type: ignore
                        if uids:
                            client.delete_messages(
                                uids
                            )  # sets \Deleted :contentReference[oaicite:4]{index=4}
                            client.expunge()  # permanently removes
                except IMAPServiceErrorFolderNotSelectable:
                    continue

            # 2) Delete folders (deepest-first)
            for imap_folder in imap_folders:
                client.delete_folder(str(imap_folder))

            # Ensure IMAP_DIRECTORY_BASE is empty at the end
            # (some servers auto-move things)
            with self._select_folder(client, IMAP_DIRECTORY_BASE, readonly=False):
                uids = client.search(["ALL"])  # type: ignore
                if uids:
                    client.delete_messages(uids)
                    client.expunge()

    def _iter_subfolders(
        self, client: IMAPClient, imap_folder: ImapPurePath
    ) -> Generator[ImapPurePath, None, None]:
        try:
            subtree = client.list_folders(
                directory="", pattern=f"{imap_folder}{IMAP_FOLDER_DELIMITER}*"
            )
        except IMAPClientError as e:
            raise IMAPServiceError(
                f"Failed to list folder subtree for '{imap_folder}': {e}"
            ) from e

        for _, _, name in subtree:
            if isinstance(name, bytes):
                name = name.decode()
            yield ImapPurePath(name)

    def get_emails(
        self,
        search_criteria: list[str] | None = None,
        folder: FilePurePath | ImapPurePath | None = None,
        recurse: bool = False,
    ) -> list[ImapInfo]:
        search_criteria = search_criteria if search_criteria else ["ALL"]
        infos: list[ImapInfo] = []
        imap_folder = self.get_imap_folder(folder)
        imap_folder_iter = chain([imap_folder])
        with self._imap_context() as client:
            if recurse:
                imap_folder_iter = chain(
                    imap_folder_iter, self._iter_subfolders(client, imap_folder)
                )
            for f in imap_folder_iter:
                try:
                    with self._select_folder(client, f):
                        try:
                            searched_uids = client.search(search_criteria)  # type: ignore
                        except IMAPClientError as e:
                            raise IMAPServiceError(
                                (
                                    f"Failed to search in folder '{f}'"
                                    f"for emails with criteria {search_criteria}"
                                )
                            ) from e
                except IMAPServiceErrorFolderNotSelectable:
                    continue

                for uid in searched_uids:
                    infos.append(ImapInfo(folder=imap_folder, uid=uid))
        return infos

    def add_flags_to_emails(
        self,
        folder: FilePurePath | ImapPurePath | None,
        uids: list[int],
        flags: list[bytes],
    ):
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client, self._select_folder(client, imap_folder):
            client.add_flags(uids, flags)

    def remove_flags_from_emails(
        self,
        folder: FilePurePath | ImapPurePath | None,
        uids: list[int],
        flags: list[bytes],
    ):
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client, self._select_folder(client, imap_folder):
            client.remove_flags(uids, flags)
