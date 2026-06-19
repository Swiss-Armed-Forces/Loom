from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from common.dependencies import get_file_repository
from common.file.file_repository import File, FilePurePath

from worker.periodic.tasks.sync_flagged_emails_from_imap import (
    process_email_to_flag,
)


def _make_file(*, flagged: bool = False) -> File:
    return File(
        full_name=FilePurePath("test_email.eml"),
        source="imap",
        sha256="abc123",
        size=42,
        flagged=flagged,
    )


class TestProcessEmailToFlag:
    def test_returns_file_id_when_not_yet_flagged(self):
        file = _make_file(flagged=False)
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file

        result = process_email_to_flag(file.id_)

        assert result == file.id_

    def test_returns_none_when_already_flagged(self):
        file = _make_file(flagged=True)
        cast(MagicMock, get_file_repository()).get_by_id.return_value = file

        result = process_email_to_flag(file.id_)

        assert result is None

    def test_raises_when_file_not_found(self):
        cast(MagicMock, get_file_repository()).get_by_id.return_value = None
        missing_id = uuid4()

        with pytest.raises(ValueError, match=str(missing_id)):
            process_email_to_flag(missing_id)
