"""Tests for `cicd/docker_image_backup_restore.py`.

A cache directory is named after the image ID the backup saw, and the daemon
restoring it is free to give the same archive a different one - the containerd
image store does exactly that for an archive the classic store wrote. Restore
has to tag what the daemon says it loaded.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import zstandard as zstd
from docker.errors import ImageNotFound

from docker_image_backup_restore import ImageMetadata, ImageTag, docker_restore_image

SAVED_ID = "sha256:3d6d0df7f7dc5210905317834d5e8f0e846b04c44bd7d5c943e2533f06bb5ba2"
LOADED_ID = "sha256:c209cb18f3bbef6b6e8c7eefd0f457e230b51ba9a381cf144bfa97ad9f3c5877"
TAG = "registry.example.com/loom/nix-dind:latest"


class StubImage:
    """An image that records what it was tagged as."""

    def __init__(self, image_id: str) -> None:
        self.id = image_id
        self.tagged_as: List[str] = []

    def tag(self, repository: str) -> None:
        self.tagged_as.append(repository)


class StubImages:
    """Holds nothing until an archive is loaded, then holds one image."""

    def __init__(self, loaded: StubImage) -> None:
        self.loaded = loaded
        self.archive_bytes = 0

    def get(self, name: str) -> StubImage:
        if name != self.loaded.id or not self.archive_bytes:
            raise ImageNotFound(f"No such image: {name}")
        return self.loaded

    def load(self, data: Any) -> List[StubImage]:
        self.archive_bytes = len(data.read())
        return [self.loaded]


def write_archive(backup_dir: Path, image_id: str) -> None:
    image_dir = backup_dir / image_id
    image_dir.mkdir(parents=True)
    (image_dir / "meta.json").write_text(
        ImageMetadata(id=image_id, tags=[ImageTag(TAG)]).model_dump_json()
    )
    (image_dir / "image.tar.zst").write_bytes(
        zstd.ZstdCompressor().compress(b"image archive")
    )


def test_tags_the_image_the_daemon_loaded(tmp_path: Path) -> None:
    """The loaded image is tagged even though its ID is not the archive's."""
    write_archive(tmp_path, SAVED_ID)
    images = StubImages(StubImage(LOADED_ID))
    client = SimpleNamespace(images=images)

    docker_restore_image(SAVED_ID, tmp_path, client=client)  # type: ignore[arg-type]

    assert images.archive_bytes > 0
    assert images.loaded.tagged_as == [TAG]
