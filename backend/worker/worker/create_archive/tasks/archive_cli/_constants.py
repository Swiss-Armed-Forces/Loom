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
## Interactive shell

`archive_cli` is bundled into every archive and requires only the Python stdlib. Run
without arguments (or `shell`) for an interactive shell with prompt `loom:/>`, or pass a
subcommand directly for one-shot scripting. On Unix/macOS the shell uses GNU readline:
persistent history (`.loom_history`), `Tab` completion for commands and paths (including
quoted paths), `Ctrl+R` reverse-search, and `!N` / `!!` history expansion. On Windows,
install `pyreadline3` to enable these features. Type `help` for the full reference.
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
