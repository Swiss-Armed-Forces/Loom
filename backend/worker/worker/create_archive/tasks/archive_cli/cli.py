#!/usr/bin/env python3
"""Entry point for the Loom archive CLI.

Run directly from the extracted archive root::

    ./cli.py [command] [args]
    python cli.py [command] [args]
"""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import_module("archive_cli._parser").main()
