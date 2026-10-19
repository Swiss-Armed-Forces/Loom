"""Entry point: `loom-console-mouse -- tmux ...

attach-session ...`.
"""

import sys

from loom_console_mouse.relay import main

if __name__ == "__main__":
    sys.exit(main())
