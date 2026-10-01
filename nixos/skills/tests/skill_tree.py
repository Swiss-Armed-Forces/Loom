"""Shared parsing for the skill-tree suites.

Named `skill_tree` rather than `conftest` on purpose. `appliance-pytest` runs all
of the appliance's suites in one session with pytest's default import mode, so
every module basename has to be unique across them -- and `conftest` is the one
name five of them already have.


These tests read the sources under `nixos/skills/`, not an assembled image. What
they are for is the class of mistake opencode does not report: a skill whose
frontmatter does not satisfy its registration guard is dropped with no log line
and no error, and the only symptom is an assistant that has never heard of Loom.

The image-build-time half of the checking lives in `nixos/tests/appliance-skills.nix`,
which can see the evaluated configuration and the assembled output. This half can
see `Documentation/`, which that one cannot -- hence two places.
"""

import re
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

# nixos/skills/tests/conftest.py -> the repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = REPO_ROOT / "nixos" / "skills"

# The path the skills tell the agent to read, which is where repo.nix seeds this
# very checkout on the box. Rewritten to the repository root to check a citation.
ON_BOX_REPO = "/home/loom/loom"

# opencode puts every skill's description in the system prompt on every request,
# so this is a context budget rather than a style rule. The built-in
# `customize-opencode` description is a little under 400 characters.
MAX_DESCRIPTION = 500

# `Skill.state` seeds the built-in before scanning, and registration overwrites
# by name without complaint, so a skill called this would silently replace it.
RESERVED_NAMES = frozenset({"customize-opencode"})

# The `<skill_files>` listing the skill tool returns alongside a loaded skill is
# capped at ten, and the tool tells the model the list is sampled. Eight leaves
# room for the generated facts.md without reaching that edge.
MAX_REFERENCE_FILES = 8

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_DOC_PATH = re.compile(rf"{re.escape(ON_BOX_REPO)}/([\w/.-]+\.md)")
_QUOTED_HEADING = re.compile(r"`(#{1,6} [^`]+)`")


class Skill(NamedTuple):
    """One `<name>/SKILL.md`, parsed.

    `name` and `description` are deliberately untyped: what these tests exist to
    catch is frontmatter that is the wrong *type*, so they have to be able to
    hold a mapping or a None and let a test say so.
    """

    name: object
    description: object
    directory: Path
    path: Path
    body: str


class DocReference(NamedTuple):
    """A citation of one of Loom's own documentation files from a skill."""

    source: Path
    repo_path: Path
    as_written: str


def _parse(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER.match(text)
    if match is None:
        pytest.fail(f"{path}: no YAML frontmatter at the top of the file")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        pytest.fail(f"{path}: frontmatter is not a mapping")
    return Skill(
        name=data.get("name"),
        description=data.get("description"),
        directory=path.parent,
        path=path,
        body=text[match.end() :],
    )


def all_skills() -> list[Skill]:
    """Every skill in the tree, in a stable order."""
    return [_parse(p) for p in sorted(SKILLS_ROOT.glob("*/SKILL.md"))]


def all_markdown() -> list[Path]:
    """Every markdown file in the tree -- skills and their reference files."""
    return sorted(SKILLS_ROOT.rglob("*.md"))


def doc_references(path: Path) -> list[DocReference]:
    """The Loom documentation files a skill file points the agent at."""
    text = path.read_text(encoding="utf-8")
    return [
        DocReference(
            source=path,
            repo_path=REPO_ROOT / relative,
            as_written=f"{ON_BOX_REPO}/{relative}",
        )
        for relative in dict.fromkeys(_DOC_PATH.findall(text))
    ]


def quoted_headings(path: Path) -> list[str]:
    """Markdown headings a skill file quotes, e.g. `## Troubleshooting`."""
    return _QUOTED_HEADING.findall(path.read_text(encoding="utf-8"))


def headings_in(path: Path) -> set[str]:
    """Every ATX heading in a markdown file, as written."""
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    }
