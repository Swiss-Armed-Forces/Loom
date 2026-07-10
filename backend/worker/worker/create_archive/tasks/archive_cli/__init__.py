"""archive_cli — Loom archive format constants and standalone CLI.

Re-exports the public symbols needed by the worker and other production code. Tests may
import internal symbols directly from the sub-modules.
"""

from ._commands import build_parser
from ._constants import (
    CLI_DESCRIPTION,
    CLI_DOC,
    CLI_ENTRYPOINT_FILENAME,
    CLI_FILENAME,
    ERR_NO_FILE_FOUND,
    FILES_DIR,
    FILES_INDEX_DIR,
    JSON_INDENT,
    JSON_SUFFIX,
    MANIFEST_FILENAME,
    README_FILENAME,
    SHELL_INDEX_FILENAME,
    SHELL_PROMPT,
    ZIP_EXTENSION,
)
from ._shell import cmd_shell

__all__ = [
    # _commands
    "build_parser",
    # _constants
    "CLI_DESCRIPTION",
    "CLI_DOC",
    "CLI_ENTRYPOINT_FILENAME",
    "CLI_FILENAME",
    "ERR_NO_FILE_FOUND",
    "FILES_DIR",
    "FILES_INDEX_DIR",
    "JSON_INDENT",
    "JSON_SUFFIX",
    "MANIFEST_FILENAME",
    "README_FILENAME",
    "SHELL_INDEX_FILENAME",
    "SHELL_PROMPT",
    "ZIP_EXTENSION",
    # _shell
    "cmd_shell",
]
