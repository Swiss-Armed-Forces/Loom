import os

# Set to True by the --auto flag to skip aitools' own interactive prompts. The claude
# backend runs in auto permission mode either way; the opencode backend takes --auto.
AUTO_MODE: bool = False
BACKEND: str = "claude"
MODEL: str = "none"

CI_SERVER_HOST = os.getenv("CI_SERVER_HOST", "gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN") or os.getenv("PROJECT_ACCESS_TOKEN")
CI_JOB_TOKEN = os.getenv("CI_JOB_TOKEN")
CI_PROJECT_ID = os.getenv("CI_PROJECT_ID")
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "120"))
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "50000"))

# An agentic run is bounded by silence on its event stream rather than by wall clock: a
# wall-clock kill lands mid-edit, while an agent that has emitted nothing for ten minutes
# is hung. The total is a backstop against one that loops forever while still chattering.
AI_AGENT_TIMEOUT = int(os.getenv("AI_AGENT_TIMEOUT", "7200"))
AI_AGENT_IDLE_TIMEOUT = int(os.getenv("AI_AGENT_IDLE_TIMEOUT", "600"))

# Entering devenv in a fresh worktree is a nix build the first time.
DEVENV_BOOTSTRAP_TIMEOUT = int(os.getenv("DEVENV_BOOTSTRAP_TIMEOUT", "1800"))

# Where worktrees are added; empty means "<primary checkout>-worktrees" beside it.
WORKTREES_ROOT = os.getenv("LOOM_WORKTREES_ROOT", "")

# Set for images that bake the devenv environment in and carry no direnv.
SKIP_DEVENV = bool(os.getenv("AITOOLS_SKIP_DEVENV"))

# Transcripts and strand logs; empty means $XDG_STATE_HOME/loom or ~/.local/state/loom.
STATE_DIR = os.getenv("AITOOLS_STATE_DIR", "")

# Pathspecs for files to exclude from diffs (lockfiles, generated files)
EXCLUDED_PATHSPECS = [
    ":(exclude)**/poetry.lock",
    ":(exclude)**/pnpm-lock.yaml",
    ":(exclude)Frontend/src/app/api/generated/**",
]
