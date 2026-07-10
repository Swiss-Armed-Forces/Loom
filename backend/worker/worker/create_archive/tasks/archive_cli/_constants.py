from pathlib import Path

MANIFEST_FILENAME = "MANIFEST.json"
README_FILENAME = "README.md"
CLI_FILENAME = "archive_cli"
FILES_DIR = "files"
FILES_INDEX_DIR = "files_index"
JSON_SUFFIX = ".json"
ZIP_EXTENSION = ".zip"
JSON_INDENT = 2
SHELL_PROMPT = "loom:"
CLI_DESCRIPTION = "Loom archive CLI"
ERR_NO_FILE_FOUND = "no file found matching"
SHELL_INDEX_FILENAME = "SHELL_INDEX.db"
CLI_ENTRYPOINT_FILENAME = "cli.py"

CLI_DOC = """\
Archive format constants and standalone CLI for Loom archives.

``archive_cli`` is bundled into every archive; requires only the Python stdlib. Run without
arguments for an interactive shell (prompt ``loom:/>``, TAB autocomplete, history
navigation), or pass a subcommand directly for scripting. Shell-only commands: ``cd``,
``pwd``, ``clear``. Type ``help`` inside the shell for a full command list. Exit codes:
0 success, 1 no results, 2 usage error.
"""

# ---------------------------------------------------------------------------
# Path constants — resolved relative to the archive root.
# __file__ is archive_cli/_constants.py; .parent.parent is the archive root.
# ---------------------------------------------------------------------------

ARCHIVE_ROOT = Path(__file__).parent.parent
FILES_INDEX = ARCHIVE_ROOT / FILES_INDEX_DIR
FILES = ARCHIVE_ROOT / FILES_DIR
SHELL_HISTORY_FILE = ARCHIVE_ROOT / ".loom_history"
SHELL_INDEX = ARCHIVE_ROOT / SHELL_INDEX_FILENAME
