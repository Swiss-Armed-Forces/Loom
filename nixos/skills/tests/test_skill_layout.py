"""The shape of the tree, which is dictated by how opencode scans it.

A `skills.paths` entry is globbed with `**/SKILL.md` -- not the wider pattern the newer
in-tree engine uses, which is not the one that reads this key. So a skill is
`<name>/SKILL.md` and nothing else is a skill, and a file in the wrong place is either
ignored or registered as something nobody meant.
"""

from skill_tree import MAX_REFERENCE_FILES, SKILLS_ROOT, all_skills


def test_there_are_skills_to_ship() -> None:
    """Cheap, and it is the test that fails if the tree is ever moved or renamed.

    Everything else in this suite passes vacuously over an empty list.
    """
    assert all_skills(), f"no <name>/SKILL.md found under {SKILLS_ROOT}"


def test_every_skill_md_is_at_the_top_of_its_skill() -> None:
    """`**/SKILL.md` is recursive, so a SKILL.md under reference/ registers too.

    It would come out as a second, unintended skill rather than as an error.
    """
    expected = {skill.path for skill in all_skills()}
    found = set(SKILLS_ROOT.rglob("SKILL.md"))
    unexpected = found - expected
    assert not unexpected, (
        f"SKILL.md below a skill's own directory: {sorted(map(str, unexpected))}. "
        f"opencode's glob is recursive and would register these as extra skills"
    )


def test_reference_files_live_in_reference() -> None:
    for skill in all_skills():
        for path in skill.directory.rglob("*.md"):
            if path == skill.path or path.name == "facts.md":
                continue
            assert (
                path.parent.name == "reference"
            ), f"{path}: supporting files belong in {skill.directory.name}/reference/"


def test_supporting_files_stay_within_the_listing() -> None:
    """The `<skill_files>` list the skill tool returns is capped at ten entries.

    Past that the model is told only about some of them, and the tool's own output says
    the list is sampled -- so a skill with more references than this cannot rely on any
    particular one being offered.
    """
    for skill in all_skills():
        supporting = [
            p for p in skill.directory.rglob("*") if p.is_file() and p != skill.path
        ]
        assert len(supporting) <= MAX_REFERENCE_FILES, (
            f"{skill.path}: {len(supporting)} supporting files; opencode lists at "
            f"most ten and samples beyond that, so keep it to {MAX_REFERENCE_FILES}"
        )


def test_skills_open_with_a_heading() -> None:
    """Markdownlint's MD041, which the repository's hooks enforce on every page.

    Worth asserting here too: the frontmatter is stripped before that rule runs,
    so the first body line is what it sees, and a skill that fails it fails the
    commit rather than the image.
    """
    for skill in all_skills():
        first = next(
            (line for line in skill.body.splitlines() if line.strip()),
            "",
        )
        assert first.startswith(
            "# "
        ), f"{skill.path}: the body has to open with a single `# ` heading, got {first!r}"
