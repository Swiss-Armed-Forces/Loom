import email
import hashlib
import re
from contextlib import contextmanager
from datetime import datetime
from itertools import chain
from typing import Generator

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from pydantic import AnyUrl, BaseModel

from common.file.file_repository import FilePurePath, ImapInfo, ImapPurePath


def _get_email_deduplication_fingerprint(raw_email: bytes) -> str:
    return hashlib.sha256(raw_email).hexdigest()


class IMAPServiceError(Exception):
    pass


class IMAPServiceErrorFolderNotSelectable(IMAPServiceError):
    pass


class IMAPServiceErrorNoSelectableFolderFound(IMAPServiceError):
    pass


class ImapFolderInfo(BaseModel):
    flags: list[bytes]
    delimiter: bytes
    name: ImapPurePath

    @property
    def is_selectable(self) -> bool:
        return IMAP_FLAG_NOSELECT not in self.flags


IMAP_FLAG_NOSELECT = b"\\Noselect"
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
        # We do create a new connection here because IMAPClient is not thread safe
        # We could probably be a bit smarter here, but we have to be very careful
        # Note that at the time of writing this class is instantiated in the
        # celery master process, which is then forked for the children.
        # See:
        # - https://imapclient.readthedocs.io/en/2.2.0/api.html#thread-safety
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
                    folders_to_count, self._iter_subfolder_names(client, imap_folder)
                )

            return sum(
                _count_messages_in_folder(imap_folder)
                for imap_folder in folders_to_count
            )

    def get_latest_email_date(
        self, folder: FilePurePath | ImapPurePath | None = None
    ) -> datetime | None:
        imap_folder = self.get_imap_folder(folder)

        with self._imap_context() as client, self._select_folder(
            client, imap_folder, readonly=True
        ):
            # Sort by ARRIVAL in reverse order (newest first), get just the first UID
            sorted_uids = client.sort(
                ["REVERSE", "ARRIVAL"], ["ALL"]
            )  # type: ignore[arg-type]

            if not sorted_uids:
                return None

            # Fetch the INTERNALDATE of the most recent email
            latest_uid = sorted_uids[0]
            fetch_result = client.fetch([latest_uid], ["INTERNALDATE"])

            if latest_uid not in fetch_result:
                return None

            internal_date = fetch_result[latest_uid][b"INTERNALDATE"]
            if not isinstance(internal_date, datetime):
                raise IMAPServiceError(
                    f"Unexpected INTERNALDATE type for UID {latest_uid}: {type(internal_date)}"
                )
            return internal_date

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
            # Unsubscribe from all subscribed folders
            for subscribed_imap_folder in self._iter_subscription_names(
                client=client, imap_folder=IMAP_DIRECTORY_BASE
            ):
                client.unsubscribe_folder(str(subscribed_imap_folder))

            # Get all folders
            imap_folders = list(
                self._iter_subfolder_names(
                    client=client, imap_folder=IMAP_DIRECTORY_BASE
                )
            )

            # Sort by depth so later on we delete subfolders before parents.
            imap_folders.sort(
                key=lambda n: n.parts,
                reverse=True,
            )

            # Empty all selectable folders
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

            # Delete folders (deepest-first)
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
    ) -> Generator[ImapFolderInfo, None, None]:
        try:
            subtree = client.list_folders(
                directory="", pattern=f"{imap_folder}{IMAP_FOLDER_DELIMITER}*"
            )
        except IMAPClientError as e:
            raise IMAPServiceError(
                f"Failed to list folder subtree for '{imap_folder}': {e}"
            ) from e

        for flags, delimiter, name in subtree:
            if isinstance(name, bytes):
                name = name.decode()

            yield ImapFolderInfo(
                flags=flags,
                delimiter=delimiter,
                name=ImapPurePath(name),
            )

    def _iter_subfolder_names(
        self, client: IMAPClient, imap_folder: ImapPurePath
    ) -> Generator[ImapPurePath, None, None]:
        yield from (
            folder.name for folder in self._iter_subfolders(client, imap_folder)
        )

    def _get_folder_info(
        self, client: IMAPClient, imap_folder: ImapPurePath
    ) -> ImapFolderInfo:
        """Get folder info for a specific folder."""
        try:
            folder_list = client.list_folders(directory="", pattern=str(imap_folder))
        except IMAPClientError as e:
            raise IMAPServiceError(
                f"Could not get folder info '{imap_folder}': {e}"
            ) from e

        if not folder_list:
            raise IMAPServiceError(
                f"Could not get folder info '{imap_folder}': Folder not found"
            )

        if len(folder_list) > 1:
            raise IMAPServiceError(
                f"Could not get folder info '{imap_folder}': Multiple folders found"
            )

        flags, delimiter, name = folder_list[0]
        if isinstance(name, bytes):
            name = name.decode()
        return ImapFolderInfo(flags=flags, delimiter=delimiter, name=ImapPurePath(name))

    def _iter_selectable_folder_names(
        self,
        client: IMAPClient,
        imap_folder: ImapPurePath,
        recurse: bool = False,
    ) -> Generator[ImapPurePath, None, None]:
        """Iterate selectable folder names.

        Yields the main folder if selectable, and if recurse=True, also yields all
        selectable subfolders.
        """
        selectable_folders: list[ImapPurePath] = []

        folder_info = self._get_folder_info(client, imap_folder)
        if folder_info is None or folder_info.is_selectable:
            selectable_folders.append(imap_folder)

        if recurse:
            for folder in self._iter_subfolders(client, imap_folder):
                if folder.is_selectable:
                    selectable_folders.append(folder.name)

        if not selectable_folders:
            raise IMAPServiceErrorNoSelectableFolderFound(
                f"Cannot iterate over folder '{imap_folder}': "
                "no selectable folders found"
            )

        yield from selectable_folders

    def _iter_subscriptions(
        self, client: IMAPClient, imap_folder: ImapPurePath
    ) -> Generator[ImapFolderInfo, None, None]:
        try:
            subtree = client.list_sub_folders(
                directory="", pattern=f"{imap_folder}{IMAP_FOLDER_DELIMITER}*"
            )
        except IMAPClientError as e:
            raise IMAPServiceError(
                f"Failed to list subscribed folder subtree for '{imap_folder}': {e}"
            ) from e

        for flags, delimiter, name in subtree:
            if isinstance(name, bytes):
                name = name.decode()

            yield ImapFolderInfo(
                flags=flags,
                delimiter=delimiter,
                name=ImapPurePath(name),
            )

    def _iter_subscription_names(
        self, client: IMAPClient, imap_folder: ImapPurePath
    ) -> Generator[ImapPurePath, None, None]:
        yield from (
            folder.name for folder in self._iter_subscriptions(client, imap_folder)
        )

    def get_emails(
        self,
        search_criteria: list[str] | None = None,
        folder: FilePurePath | ImapPurePath | None = None,
        recurse: bool = False,
    ) -> list[ImapInfo]:
        search_criteria = search_criteria if search_criteria else ["ALL"]
        infos: list[ImapInfo] = []
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client:
            for f in self._iter_selectable_folder_names(
                client, imap_folder, recurse=recurse
            ):
                with self._select_folder(client, f):
                    try:
                        searched_uids = client.search(search_criteria)  # type: ignore
                    except IMAPClientError as e:
                        raise IMAPServiceError(
                            f"Failed to search in folder '{f}' "
                            f"for emails with criteria {search_criteria}"
                        ) from e

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

    def subscribe_folder(
        self, folder: FilePurePath | ImapPurePath | None, recurse: bool = False
    ):
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client:
            for f in self._iter_selectable_folder_names(
                client, imap_folder, recurse=recurse
            ):
                try:
                    client.subscribe_folder(str(f))
                except IMAPClientError as e:
                    raise IMAPServiceError(
                        f"Failed to subscribe to folder '{f}': {e}"
                    ) from e

    def unsubscribe_folder(
        self, folder: FilePurePath | ImapPurePath | None, recurse: bool = False
    ):
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client:
            folders = chain([imap_folder])
            if recurse:
                folders = chain(
                    folders, self._iter_subfolder_names(client, imap_folder)
                )
            for f in folders:
                try:
                    client.unsubscribe_folder(str(f))
                except IMAPClientError as e:
                    raise IMAPServiceError(
                        f"Failed to unsubscribe from folder '{f}': {e}"
                    ) from e

    def list_subscribed_folders(
        self, folder: FilePurePath | ImapPurePath | None = None
    ) -> list[ImapPurePath]:
        imap_folder = self.get_imap_folder(folder)
        with self._imap_context() as client:
            return list(self._iter_subscription_names(client, imap_folder))
