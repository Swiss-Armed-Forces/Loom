"""The manifest filename exists in two places, on purpose.

Keep them equal. `common.archive.archive_detection` cannot import the archive CLI's
constants: `compress_files._cli_entries` copies every .py file under
`worker/create_archive/tasks/archive_cli/` verbatim into each archive, where it runs
from an extracted folder with nothing but a standard Python installation. An import of
`common` there would break every archive the moment it is extracted.

So the constant is restated, and this is what stops the two copies drifting -- the same
approach `nixos/tests/appliance.nix` takes for the values `box.nix` restates from
`up.sh`.
"""

from common.archive.archive_detection import MANIFEST_FILENAME

from worker.create_archive.tasks.archive_cli import (
    MANIFEST_FILENAME as CLI_MANIFEST_FILENAME,
)


def test_manifest_filename_agrees_with_the_vendored_cli():
    assert MANIFEST_FILENAME == CLI_MANIFEST_FILENAME
