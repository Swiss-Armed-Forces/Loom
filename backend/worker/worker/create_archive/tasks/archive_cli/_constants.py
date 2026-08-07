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
## Getting started

Run `python cli.py` (or `./cli.py` on Unix/macOS) from inside the extracted folder.
Only a standard Python installation is required — no extra packages needed.

```
python cli.py                                       # open the interactive shell
python cli.py ls                                    # list all files
python cli.py tree                                  # show the archive directory structure
python cli.py find -name "*.pdf"                    # find files by name pattern
python cli.py find -attr summary                    # find files that have an AI summary
python cli.py find -attr summary -attr tags         # must have both (AND)
python cli.py cat report.pdf                        # print the text content of a file
python cli.py info report.pdf                       # show all metadata for a file
python cli.py info report.pdf content               # print a specific metadata field
python cli.py translate report.pdf                  # list available translations
python cli.py translate report.pdf en               # print the English translation
python cli.py grep "search term"                    # search across all file metadata
python cli.py grep "alice" -f tika_meta.dc_creator  # search only one field
python cli.py grep "secret" -f content -f summary   # search two fields (OR)
python cli.py extract report.pdf                    # extract a file to the current directory
python cli.py --help                                # show all available commands
```

The interactive shell supports tab completion for commands and file paths, persistent
command history saved between sessions, `Ctrl+R` to search history, and `!N` / `!!`
to repeat a previous command. Type `help` inside the shell for the full reference.
"""

# ---------------------------------------------------------------------------
# Path constants — resolved relative to the archive root.
# __file__ is archive_cli/_constants.py; .parent.parent is the archive root.
# ---------------------------------------------------------------------------

ARCHIVE_ROOT = Path(__file__).parent.parent
FILES_INDEX = ARCHIVE_ROOT / FILES_INDEX_DIR
FILES = ARCHIVE_ROOT / FILES_DIR
SHELL_HISTORY_FILE = ARCHIVE_ROOT / ".loom_history"
SHELL_CRASH_LOG_FILE = ARCHIVE_ROOT / ".loom_crash.log"
SHELL_INDEX = ARCHIVE_ROOT / SHELL_INDEX_FILENAME
