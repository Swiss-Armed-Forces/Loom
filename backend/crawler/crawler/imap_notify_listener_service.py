import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, NamedTuple

from common.file.file_repository import (
    FileRepository,
    ImapInfo,
    ImapPurePath,
)
from common.file.file_scheduling_service import FileSchedulingService
from common.services.task_scheduling_service import UpdateFileRequest
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError

logger = logging.getLogger(__name__)

IMAP_FLAG_SEEN = r"\Seen"
IMAP_FLAG_FLAGGED = r"\Flagged"

# imapclient returns idle_check() responses as plain tuples of variable length
# and heterogeneous element types depending on the server message type.
ImapIdleResponse = tuple[Any, ...]


class FolderModseqResult(NamedTuple):
    folder: str
    modseq: int | None


class ExtendedIMAPClient(IMAPClient):
    """IMAPClient subclass that exposes the underlying imaplib xatom command."""

    def xatom(self, name: str, *args: str) -> Any:
        return self._imap.xatom(name, *args)


class IMAPNotifyListenerService:  # pylint: disable=too-many-instance-attributes
    """Holds a single persistent IMAP connection, registers for NOTIFY flag-change
    events, and updates Loom file flags for each incoming notification."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        file_repository: FileRepository,
        file_scheduling_service: FileSchedulingService,
        keepalive_interval_s: int = 60,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._file_repository = file_repository
        self._file_scheduling_service = file_scheduling_service
        self._keepalive_interval_s = keepalive_interval_s
        # Tracks the highest MODSEQ seen per folder for CONDSTORE incremental fetches.
        self._folder_modseq: dict[str, int] = {}

    def run(self) -> None:
        logger.info("Connecting to IMAP server %s:%s", self._host, self._port)
        with ExtendedIMAPClient(
            host=self._host,
            port=self._port,
            ssl=False,
        ) as client:
            client.login(self._user, self._password)
            logger.info("Logged in as %s", self._user)

            capabilities = client.capabilities()
            logger.debug("IMAP capabilities: %r", capabilities)
            if b"CONDSTORE" not in capabilities:
                logger.error(
                    "IMAP server does not support CONDSTORE — NOTIFY listener disabled"
                )
                raise SystemExit(1)
            if b"NOTIFY" not in capabilities:
                logger.error(
                    "IMAP server does not support NOTIFY — NOTIFY listener disabled"
                )
                raise SystemExit(1)

            client.xatom("ENABLE", "CONDSTORE")
            # RFC 5465 §5: notify-list is a space-separated sequence of mailbox-filter
            # specs; each spec is parenthesised. The correct form is:
            # NOTIFY SET (PERSONAL (FlagChange))
            client.xatom("NOTIFY", "SET", "(PERSONAL (FlagChange))")
            logger.info("NOTIFY subscription registered, entering idle loop")

            self._initialize_folder_modseqs(client)

            # Dovecot sends STATUS responses (not FETCH) for non-selected mailboxes.
            # On each STATUS we exit IDLE, SELECT the folder, CONDSTORE-fetch changed
            # message flags, then re-enter IDLE. _in_idle tracks whether the IDLE
            # command is currently active so the finally can avoid a double idle_done().
            _in_idle = True
            client.idle()
            try:
                while True:
                    responses = client.idle_check(timeout=self._keepalive_interval_s)
                    changed_folders: set[str] = set()
                    for response in responses:
                        folder = self.parse_status_folder(response)
                        if folder is not None:
                            changed_folders.add(folder)
                        else:
                            self.handle_fetch_response(response)
                    if changed_folders:
                        client.idle_done()
                        _in_idle = False
                        for folder in sorted(changed_folders):
                            self._sync_folder_flags(client, folder)
                        client.idle()
                        _in_idle = True
            finally:
                if _in_idle:
                    client.idle_done()
                logger.info("Idle loop exited, session closing")

    @staticmethod
    def parse_status_folder(response: ImapIdleResponse) -> str | None:
        """Extract the mailbox name from a STATUS idle response, or None if not STATUS.

        Dovecot emits STATUS notifications for non-selected mailboxes:
            (b'STATUS', b'INBOX/folder', (b'HIGHESTMODSEQ', 47))
        """
        if len(response) < 2 or response[0] != b"STATUS":
            return None
        mailbox = response[1]
        return mailbox.decode() if isinstance(mailbox, bytes) else str(mailbox)

    def _fetch_folder_modseq(self, folder_name: str) -> FolderModseqResult:
        """Open a dedicated IMAP connection and return the folder's HIGHESTMODSEQ."""
        with ExtendedIMAPClient(host=self._host, port=self._port, ssl=False) as c:
            c.login(self._user, self._password)
            status = c.folder_status(folder_name, [b"HIGHESTMODSEQ"])
            modseq = status.get(b"HIGHESTMODSEQ")
            return FolderModseqResult(
                folder=folder_name,
                modseq=modseq if isinstance(modseq, int) else None,
            )

    def _initialize_folder_modseqs(self, client: IMAPClient) -> None:
        """Pre-populate HIGHESTMODSEQ for all folders before entering the idle loop.

        Prevents a bulk fetch of all messages on the first STATUS notification for any
        existing folder, while still capturing flag changes that arrive after startup.
        Uses a thread pool so each folder opens its own connection and the STATUS calls
        run in parallel.
        """
        folder_names = [name for _, _, name in client.list_folders()]
        logger.info(
            "Initializing MODSEQ watermarks for %d folder(s)", len(folder_names)
        )
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._fetch_folder_modseq, name): name
                for name in folder_names
            }
            for future in as_completed(futures):
                folder_name = futures[future]
                try:
                    result = future.result()
                    if result.modseq is not None:
                        self._folder_modseq[folder_name] = result.modseq
                        logger.debug(
                            "Initialized MODSEQ %d for folder %s",
                            result.modseq,
                            folder_name,
                        )
                except (IMAPClientError, OSError):
                    logger.warning(
                        "Could not initialize MODSEQ for folder %s",
                        folder_name,
                        exc_info=True,
                    )

    def _sync_folder_flags(self, client: IMAPClient, folder: str) -> None:
        """SELECT folder and fetch flags for all messages changed since last sync."""
        logger.info("Syncing flags for folder %s", folder)
        select_data = client.select_folder(folder, readonly=True)
        try:
            # CONDSTORE: only fetch messages with MODSEQ > last known value.
            # Starting from 1 on first sync covers all messages.
            search_modseq = self._folder_modseq.get(folder, 0) + 1
            changed_uids = client.search(  # type: ignore[arg-type]
                ["MODSEQ", str(search_modseq)]
            )
            logger.debug(
                "Folder %s: %d message(s) changed since MODSEQ %d",
                folder,
                len(changed_uids),
                search_modseq,
            )
            if changed_uids:
                fetch_data = client.fetch(changed_uids, ["FLAGS"])
                for uid, data in fetch_data.items():
                    raw_flags = data.get(b"FLAGS", ())
                    flags = [
                        f.decode() if isinstance(f, bytes) else str(f)
                        for f in raw_flags
                    ]
                    self._handle_flag_change(folder, uid, flags)
            new_modseq = select_data.get(b"HIGHESTMODSEQ")
            if isinstance(new_modseq, int):
                self._folder_modseq[folder] = new_modseq
        finally:
            client.unselect_folder()

    def handle_fetch_response(self, response: ImapIdleResponse) -> None:
        """Handle an unsolicited FETCH response (RFC 5465-compliant servers).

        Dovecot sends STATUS instead; see parse_status_folder/_sync_folder_flags.
        Unknown response types are silently ignored.

        Expected format: (seq, b'FETCH',
            (b'UID', uid, b'MAILBOX', folder, b'FLAGS', flags, ...))
        """
        if len(response) < 3 or response[1] != b"FETCH":
            return

        items = response[2]
        if not isinstance(items, (tuple, list)):
            return

        uid: int | None = None
        folder: str | None = None
        raw_flags: tuple | list | None = None

        # items is a flat sequence of alternating key, value pairs
        for i in range(0, len(items) - 1, 2):
            key = items[i]
            value = items[i + 1]
            if key == b"UID":
                uid = int(value)
            elif key == b"MAILBOX":
                folder = value.decode() if isinstance(value, bytes) else str(value)
            elif key == b"FLAGS":
                raw_flags = value

        if uid is None or folder is None or raw_flags is None:
            logger.debug(
                "NOTIFY FETCH response missing UID/MAILBOX/FLAGS, skipping: %r",
                response,
            )
            return

        flags = [f.decode() if isinstance(f, bytes) else str(f) for f in raw_flags]
        logger.debug("Flag change: folder=%s uid=%s flags=%s", folder, uid, flags)
        self._handle_flag_change(folder, uid, flags)

    def _handle_flag_change(self, folder: str, uid: int, flags: list[str]) -> None:
        imap_info = ImapInfo(uid=uid, folder=ImapPurePath(folder))
        file_ids = self._file_repository.get_emails_from_imap_info(imap_info)
        update = UpdateFileRequest(
            flagged=IMAP_FLAG_FLAGGED in flags,
            seen=IMAP_FLAG_SEEN in flags,
        )
        for file_id in file_ids:
            logger.info(
                "Updating flags for file %s (folder=%s uid=%s): flagged=%s seen=%s",
                file_id,
                folder,
                uid,
                update.flagged,
                update.seen,
            )
            self._file_scheduling_service.update_file(file_id, update)
