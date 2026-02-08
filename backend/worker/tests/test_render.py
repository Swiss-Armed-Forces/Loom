"""Test render image PNG task."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from common.services.lazybytes_service import LazyBytes, LazyBytesService
from wand.exceptions import MissingDelegateError, WandException

from worker.index_file.tasks.render import render_image_png_task

# pylint: disable=redefined-outer-name

TEST_ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Provide sample PNG bytes from test assets."""
    png_path = TEST_ASSETS_DIR / "python.png"
    return png_path.read_bytes()


class TestRenderImagePngTask:
    """Test suite for render_image_png_task."""

    def test_returns_none_when_file_content_is_none(self) -> None:
        """Test that None is returned when file_content is None."""
        result = render_image_png_task(None)
        assert result is None

    def test_creates_rendered_image_for_simple_image(
        self, lazybytes_service_inmemory: LazyBytesService, sample_png_bytes: bytes
    ) -> None:
        """Test successful rendered image creation for a simple image."""
        # Setup
        lazy_bytes = lazybytes_service_inmemory.from_bytes(sample_png_bytes)

        # Execute
        result = render_image_png_task(lazy_bytes)

        # Assert
        assert result is not None
        assert isinstance(result, LazyBytes)

    def test_returns_lazybytes_from_blob(
        self, lazybytes_service_inmemory: LazyBytesService, sample_png_bytes: bytes
    ) -> None:
        """Test that result is properly converted to LazyBytes."""
        # Setup
        lazy_bytes = lazybytes_service_inmemory.from_bytes(sample_png_bytes)

        # Execute
        result = render_image_png_task(lazy_bytes)

        # Assert
        assert result is not None
        assert isinstance(result, LazyBytes)

    @pytest.mark.parametrize(
        "exception_class",
        [WandException, MissingDelegateError],
    )
    @patch("worker.index_file.tasks.render.Image")
    def test_returns_none_on_image_exception(
        self,
        mock_image_class: MagicMock,
        exception_class: type[Exception],
        lazybytes_service_inmemory: LazyBytesService,
        sample_png_bytes: bytes,
    ) -> None:
        """Test that None is returned when Image raises an exception."""
        # Setup
        lazy_bytes = lazybytes_service_inmemory.from_bytes(sample_png_bytes)

        # Mock Image to raise the exception
        mock_image_class.return_value.__enter__.side_effect = exception_class(
            "Test error"
        )

        # Execute
        result = render_image_png_task(lazy_bytes)

        # Assert
        assert result is None

    @patch("worker.index_file.tasks.render.Image")
    def test_returns_none_when_blob_is_not_bytes(
        self,
        mock_image_class: MagicMock,
        lazybytes_service_inmemory: LazyBytesService,
        sample_png_bytes: bytes,
    ) -> None:
        """Test that None is returned when make_blob returns non-bytes."""
        # Setup
        lazy_bytes = lazybytes_service_inmemory.from_bytes(sample_png_bytes)

        # Mock Image with non-bytes blob
        mock_image = MagicMock()
        mock_image.width = 500
        mock_image.make_blob.return_value = "not bytes"  # Invalid return type
        mock_image_class.return_value.__enter__.return_value = mock_image
        mock_image_class.return_value.__exit__.return_value = None

        # Execute
        result = render_image_png_task(lazy_bytes)

        # Assert
        assert result is None

    @patch("worker.index_file.tasks.render.Image")
    def test_returns_none_when_blob_is_none(
        self,
        mock_image_class: MagicMock,
        lazybytes_service_inmemory: LazyBytesService,
        sample_png_bytes: bytes,
    ) -> None:
        """Test that None is returned when make_blob returns None."""
        # Setup
        lazy_bytes = lazybytes_service_inmemory.from_bytes(sample_png_bytes)

        # Mock Image with None blob
        mock_image = MagicMock()
        mock_image.width = 500
        mock_image.make_blob.return_value = None
        mock_image_class.return_value.__enter__.return_value = mock_image
        mock_image_class.return_value.__exit__.return_value = None

        # Execute
        result = render_image_png_task(lazy_bytes)

        # Assert
        assert result is None
