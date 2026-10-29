"""Unit tests for charts/files/ollama/copy-models.sh.

The script stages the preloaded Ollama model store onto the runtime's volume, and the
failure it exists to prevent is silent: a copy killed partway leaves a short GGUF blob
that every probe in the chart reports as healthy, that `ollama list` names, and that
only fails when somebody asks for a completion. The cases below therefore assert what
happens to a destination that is *already wrong* -- shorter than its source, and newer,
which is what a half-written file always is.
"""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "charts" / "files" / "ollama" / "copy-models.sh"

BLOB_NAME = "sha256-f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d"
MANIFEST_PATH = "manifests/registry.ollama.ai/library/qwen3.8/27b"


def run_script(source: Path, destination: Path) -> subprocess.CompletedProcess[str]:
    """Run the copy script over one pair of directories."""
    return subprocess.run(
        [
            "sh",
            str(SCRIPT),
            "--source",
            str(source),
            "--destination",
            str(destination),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def write(path: Path, content: bytes) -> Path:
    """Write content to path, creating the directories above it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


@pytest.fixture(name="store")
def fixture_store(tmp_path: Path) -> Path:
    """A source model store shaped like the one the models image carries."""
    source = tmp_path / "source"
    write(source / "blobs" / BLOB_NAME, b"weights" * 4096)
    write(source / "blobs" / "sha256-config", b'{"model_family":"qwen35"}')
    write(source / MANIFEST_PATH, b'{"schemaVersion":2}')
    return source


@pytest.fixture(name="destination")
def fixture_destination(tmp_path: Path) -> Path:
    """An empty destination, as the volume is mounted before anything runs."""
    destination = tmp_path / "destination"
    destination.mkdir()
    return destination


def test_copies_the_whole_tree(store: Path, destination: Path) -> None:
    """Every file arrives, with the directories below the source reproduced."""
    result = run_script(store, destination)

    assert result.returncode == 0, result.stderr
    for relative in (f"blobs/{BLOB_NAME}", "blobs/sha256-config", MANIFEST_PATH):
        assert (destination / relative).read_bytes() == (store / relative).read_bytes()


def test_replaces_a_truncated_destination(store: Path, destination: Path) -> None:
    """A short blob is copied again even though it is newer than its source.

    `cp --update` compares modification times, and a file left half-written carries the
    time it was written -- so the one file that has to be copied again is exactly the
    one an mtime comparison skips.
    """
    source_blob = store / "blobs" / BLOB_NAME
    truncated = write(
        destination / "blobs" / BLOB_NAME, source_blob.read_bytes()[:1024]
    )
    future = source_blob.stat().st_mtime + 3600
    os.utime(truncated, (future, future))

    result = run_script(store, destination)

    assert result.returncode == 0, result.stderr
    assert truncated.read_bytes() == source_blob.read_bytes()


def test_leaves_an_identical_destination_alone(store: Path, destination: Path) -> None:
    """A blob already there at the source's size is not copied again.

    Without this the models are rewritten on every pod start, which for the production
    image is some sixteen gigabytes per boot.
    """
    run_script(store, destination)
    copied = destination / "blobs" / BLOB_NAME
    first_inode = copied.stat().st_ino

    result = run_script(store, destination)

    assert result.returncode == 0, result.stderr
    assert copied.stat().st_ino == first_inode
    assert "up to date" in result.stdout


def test_discards_a_partial_file_left_behind(store: Path, destination: Path) -> None:
    """The remains of an interrupted copy are removed rather than accumulated."""
    stale = write(destination / "blobs" / f"{BLOB_NAME}.partial", b"half a blob")

    result = run_script(store, destination)

    assert result.returncode == 0, result.stderr
    assert not stale.exists()
    assert not list(destination.rglob("*.partial"))


def test_a_failed_copy_fails_the_run(store: Path, destination: Path) -> None:
    """An unreadable source stops the script instead of being reported as success.

    A non-zero exit is what gets the initContainer retried; swallowing the failure turns
    a killed copy into a completed one.
    """
    unreadable = store / "blobs" / BLOB_NAME
    unreadable.chmod(0o000)
    try:
        result = run_script(store, destination)
    finally:
        unreadable.chmod(0o644)

    assert result.returncode != 0


def test_a_failed_copy_leaves_nothing_under_the_final_name(
    store: Path, destination: Path
) -> None:
    """A copy that cannot finish never publishes a short file.

    The staged name is what makes the next run able to repair things: whatever is
    under the final name is either absent or whole.
    """
    unreadable = store / "blobs" / BLOB_NAME
    unreadable.chmod(0o000)
    try:
        run_script(store, destination)
    finally:
        unreadable.chmod(0o644)

    assert not (destination / "blobs" / BLOB_NAME).exists()


@pytest.mark.parametrize(
    "arguments",
    [
        pytest.param(["--source"], id="source-without-destination"),
        pytest.param(["--destination"], id="destination-without-source"),
    ],
)
def test_requires_both_directories(
    tmp_path: Path, arguments: list[str], destination: Path
) -> None:
    """A missing option fails the run rather than defaulting to somewhere."""
    result = subprocess.run(
        ["sh", str(SCRIPT), *arguments, str(destination)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "are required" in result.stderr


def test_rejects_a_source_that_is_not_there(tmp_path: Path, destination: Path) -> None:
    """A source the template got wrong is named, not silently copied as nothing."""
    result = run_script(tmp_path / "absent", destination)

    assert result.returncode != 0
    assert "not a directory" in result.stderr
