import os

# Set to True by the --auto flag to skip all interactive prompts and run
# Claude in non-interactive (auto-accept) mode.
AUTO_MODE: bool = False

CI_SERVER_HOST = os.getenv("CI_SERVER_HOST", "gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN") or os.getenv("PROJECT_ACCESS_TOKEN")
CI_PROJECT_ID = os.getenv("CI_PROJECT_ID")
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "120"))
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "50000"))

# Pathspecs for files to exclude from diffs (lockfiles, generated files)
EXCLUDED_PATHSPECS = [
    ":(exclude)**/poetry.lock",
    ":(exclude)**/pnpm-lock.yaml",
    ":(exclude)Frontend/src/app/api/generated/**",
]
