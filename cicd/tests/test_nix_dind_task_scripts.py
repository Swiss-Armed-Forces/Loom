"""Every devenv task script a shell entry runs must exist in the nix-dind image.

The image build enters the devenv shell to realise the package set, which runs the
repository's own tasks. A task whose `exec` points into `cicd/` fails the build unless
the Dockerfile copies that script in, and the failure only shows up on `main` and on
tags, where `buildenv_nix-dind` is the one job that runs.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEVENV_NIX = REPO_ROOT / "devenv.nix"
DOCKERFILE = REPO_ROOT / "nix-dind" / "Dockerfile"

TASK_SCRIPT_PATTERN = re.compile(
    r"\$\{config\.devenv\.root\}/(cicd/[\w./-]+\.sh)",
)


def test_task_scripts_are_copied_into_the_image() -> None:
    scripts = set(TASK_SCRIPT_PATTERN.findall(DEVENV_NIX.read_text()))
    assert scripts, "no devenv task scripts found in devenv.nix"

    dockerfile = DOCKERFILE.read_text()
    missing = sorted(script for script in scripts if script not in dockerfile)

    assert not missing, (
        f"{DOCKERFILE.relative_to(REPO_ROOT)} does not copy "
        f"{', '.join(missing)}, which devenv runs on entering the shell"
    )
