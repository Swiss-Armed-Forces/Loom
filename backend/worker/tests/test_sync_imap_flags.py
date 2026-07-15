from typing import cast
from unittest.mock import MagicMock

from common.dependencies import get_file_scheduling_service
from common.file.file_repository import File, FilePurePath
from common.services.task_scheduling_service import UpdateFileRequest

from worker.periodic.tasks.sync_imap_flags import set_flags_for_file_task


def _make_file(*, flagged: bool = False, seen: bool = False) -> File:
    return File(
        full_name=FilePurePath("test_email.eml"),
        source="imap",
        sha256="abc123",
        size=42,
        flagged=flagged,
        seen=seen,
    )


class TestSetFlagsForFile:
    def test_calls_update_file_with_both_flags(self):
        file = _make_file()
        file_id = file.id_
        scheduling_service = cast(MagicMock, get_file_scheduling_service())

        set_flags_for_file_task([file_id], flagged=True, seen=True)

        scheduling_service.update_file.assert_called_once_with(
            file_id, UpdateFileRequest(flagged=True, seen=True)
        )

    def test_calls_update_file_with_flagged_only(self):
        file = _make_file()
        file_id = file.id_
        scheduling_service = cast(MagicMock, get_file_scheduling_service())

        set_flags_for_file_task([file_id], flagged=True, seen=False)

        scheduling_service.update_file.assert_called_once_with(
            file_id, UpdateFileRequest(flagged=True, seen=False)
        )
