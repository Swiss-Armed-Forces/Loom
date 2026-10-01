"""Every path and heading a skill sends the agent to, checked against the real thing.

The skills deliberately do not retell what `Documentation/` already says; they
name a file and a heading and tell the agent to read it. That only works for as
long as the file and the heading are still there, and `Documentation/appliance.md`
is edited constantly. Without these tests the failure is an assistant confidently
directing an operator to a section that no longer exists.
"""

from skill_tree import (
    ON_BOX_REPO,
    REPO_ROOT,
    all_markdown,
    all_skills,
    doc_references,
    headings_in,
    quoted_headings,
)


def test_cited_documentation_exists() -> None:
    for path in all_markdown():
        for reference in doc_references(path):
            assert reference.repo_path.is_file(), (
                f"{path}: cites {reference.as_written}, which is not in this "
                f"repository at {reference.repo_path.relative_to(REPO_ROOT)}"
            )


def test_cited_headings_exist() -> None:
    """A quoted `## Heading` has to be in one of the docs that file points at.

    Heading level is part of it: `## Hostnames and the self-signed certificate`
    and `### Hostnames and the self-signed certificate` are different anchors,
    and getting that wrong is the easiest mistake to make here.
    """
    for path in all_markdown():
        available: set[str] = set()
        for reference in doc_references(path):
            if reference.repo_path.is_file():
                available |= headings_in(reference.repo_path)
        for heading in quoted_headings(path):
            assert heading in available, (
                f"{path}: quotes the heading {heading!r}, which is not in any "
                f"documentation file this skill points at. Check the heading "
                f"level as well as the words"
            )


def test_reference_files_named_by_a_skill_exist() -> None:
    for skill in all_skills():
        for line in skill.body.splitlines():
            for token in line.split("`"):
                if token.startswith("reference/") and token.endswith(".md"):
                    assert (
                        skill.directory / token
                    ).is_file(), f"{skill.path}: names {token}, which does not exist"


def test_every_reference_file_is_named_by_its_skill() -> None:
    """An orphan is dead weight the model will never be told to read.

    The `<skill_files>` listing the skill tool returns is capped at ten entries
    and is explicitly described to the model as sampled, so a file that the
    SKILL.md does not name may never be seen at all.
    """
    for skill in all_skills():
        for reference in sorted(skill.directory.glob("reference/*.md")):
            named = f"reference/{reference.name}"
            assert (
                named in skill.body
            ), f"{skill.path}: does not mention {named}, so nothing routes to it"


def test_no_relative_paths_in_skill_prose() -> None:
    """`loom-chat` has a different working directory in the pane and at a prompt.

    The pane starts in the checkout; typed at an `Alt-F2` console it starts in
    the operator's home. Anything the agent is told to open has to be absolute,
    or it resolves to two different things depending on how it was started.
    """
    relative = [
        f"{path}:{number}: `{token}` -- write it as {ON_BOX_REPO}/{token}"
        for path in all_markdown()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        for token in line.split("`")
        if token.startswith("Documentation/")
    ]
    assert not relative, "relative paths in skill prose:\n" + "\n".join(relative)
