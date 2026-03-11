from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from worker.periodic.tasks.unsubscribe_old_imap_folders import (
    unsubscribe_old_imap_folders_task,
)

from common.dependencies import get_imap_service


@freeze_time("2024-01-15 12:00:00")
class TestUnsubscribeOldImapFoldersTask:
    """Unit tests for unsubscribe_old_imap_folders_task."""

    @pytest.fixture
    def mock_imap(self) -> MagicMock:
        """Get the IMAP service mock."""
        return get_imap_service()

    def test_does_nothing_when_days_before_unsubscribe_is_none(
        self, mock_imap: MagicMock
    ):
        """Task should return early if days_before_unsubscribe is None."""
        # Call with None
        unsubscribe_old_imap_folders_task(days_before_unsubscribe=None)

        # Should not call any IMAP methods
        mock_imap.list_subscribed_folders.assert_not_called()
        mock_imap.get_latest_email_date.assert_not_called()
        mock_imap.unsubscribe_folder.assert_not_called()

    def test_unsubscribes_folders_with_old_emails(self, mock_imap: MagicMock):
        """Task should unsubscribe from folders with emails older than cutoff."""
        # Setup: 3 folders
        mock_imap.list_subscribed_folders.return_value = [
            "old_folder",
            "recent_folder",
            "empty_folder",
        ]

        # Current time: 2024-01-15
        # Cutoff: 30 days ago = 2023-12-16
        # old_folder: 2023-10-01 (100 days ago, should unsubscribe)
        old_date = datetime(2023, 10, 1)
        # recent_folder: 2024-01-10 (5 days ago, should keep)
        recent_date = datetime(2024, 1, 10)
        # empty_folder: no emails (None, should unsubscribe)

        def get_latest_email_date_side_effect(folder):
            if folder == "old_folder":
                return old_date
            if folder == "recent_folder":
                return recent_date
            if folder == "empty_folder":
                return None
            return None

        mock_imap.get_latest_email_date.side_effect = get_latest_email_date_side_effect

        # Run task with 30 days cutoff
        unsubscribe_old_imap_folders_task(days_before_unsubscribe=30)

        # Should check all folders
        assert mock_imap.get_latest_email_date.call_count == 3

        # Should unsubscribe from old_folder (100 days old) and empty_folder (None)
        assert mock_imap.unsubscribe_folder.call_count == 2
        mock_imap.unsubscribe_folder.assert_any_call("old_folder")
        mock_imap.unsubscribe_folder.assert_any_call("empty_folder")

    def test_handles_no_subscribed_folders(self, mock_imap: MagicMock):
        """Task should handle case with no subscribed folders."""
        # Setup: no folders
        mock_imap.list_subscribed_folders.return_value = []

        # Run task
        unsubscribe_old_imap_folders_task(days_before_unsubscribe=30)

        # Should not call get_latest_email_date or unsubscribe
        mock_imap.get_latest_email_date.assert_not_called()
        mock_imap.unsubscribe_folder.assert_not_called()

    def test_cutoff_date_boundary_keeps_newer_email(self, mock_imap: MagicMock):
        """Task should keep folder when email is exactly 1 second after cutoff."""
        mock_imap.list_subscribed_folders.return_value = ["test_folder"]

        # Current time: 2024-01-15 12:00:00
        # Cutoff: 30 days ago = 2023-12-16 12:00:00
        # Email: 2023-12-16 12:00:01 (just after cutoff, should keep)
        cutoff_date = datetime(2023, 12, 16, 12, 0, 0)
        email_date = cutoff_date + timedelta(seconds=1)
        mock_imap.get_latest_email_date.return_value = email_date

        # Run task with 30 days
        unsubscribe_old_imap_folders_task(days_before_unsubscribe=30)

        # Should NOT unsubscribe (email is newer than cutoff)
        mock_imap.unsubscribe_folder.assert_not_called()

    def test_cutoff_date_boundary_unsubscribes_older_email(self, mock_imap: MagicMock):
        """Task should unsubscribe when email is exactly 1 second before cutoff."""
        mock_imap.list_subscribed_folders.return_value = ["test_folder"]

        # Current time: 2024-01-15 12:00:00
        # Cutoff: 30 days ago = 2023-12-16 12:00:00
        # Email: 2023-12-16 11:59:59 (just before cutoff, should unsubscribe)
        cutoff_date = datetime(2023, 12, 16, 12, 0, 0)
        email_date = cutoff_date - timedelta(seconds=1)
        mock_imap.get_latest_email_date.return_value = email_date

        # Run task with 30 days
        unsubscribe_old_imap_folders_task(days_before_unsubscribe=30)

        # Should unsubscribe (email is older than cutoff)
        mock_imap.unsubscribe_folder.assert_called_once_with("test_folder")

    def test_handles_naive_datetime_from_imap(self, mock_imap: MagicMock):
        """Task should handle offset-naive datetimes returned from IMAP service.

        This reproduces the production bug where get_latest_email_date() returns a naive
        datetime, causing TypeError when comparing with offset-aware cutoff_date.
        """
        mock_imap.list_subscribed_folders.return_value = ["naive_folder"]

        # IMAP service returns naive datetime (no timezone info)
        naive_date = datetime(2024, 1, 10, 12, 0, 0)  # No tzinfo
        mock_imap.get_latest_email_date.return_value = naive_date

        unsubscribe_old_imap_folders_task(days_before_unsubscribe=30)
