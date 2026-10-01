"""The frontmatter opencode reads, and the ways it can fail without saying so.

opencode's registration guard is, in full: the parsed frontmatter is an object,
`name` is a string, and `description` is absent or a string. A file that fails it
is skipped -- no warning, no error, nothing in the log. These tests are the only
thing standing between a mistyped `---` block and a skill that silently is not
there.
"""

from skill_tree import MAX_DESCRIPTION, RESERVED_NAMES, Skill, all_skills


def test_name_is_a_string() -> None:
    for skill in all_skills():
        assert isinstance(skill.name, str) and skill.name, (
            f"{skill.path}: `name` must be a non-empty string; opencode drops the "
            f"skill without a word if it is not. Got {skill.name!r}"
        )


def test_name_matches_its_directory() -> None:
    """A Loom convention, not opencode's -- it ignores the directory entirely.

    Which is the reason to check it here: nothing else would ever notice that the
    folder and the registered skill had drifted apart, and the name in the
    frontmatter is the one the model is told to ask for.
    """
    for skill in all_skills():
        assert skill.name == skill.directory.name, (
            f"{skill.path}: frontmatter name {skill.name!r} does not match its "
            f"directory {skill.directory.name!r}"
        )


def test_description_is_a_string() -> None:
    """The realistic failure: an unquoted value containing a colon.

    `description: Use for: the box` is valid YAML and parses to a mapping, which
    fails opencode's guard. Quoting is what makes it a string, so this is worth a
    test of its own rather than a style note.
    """
    for skill in all_skills():
        assert isinstance(skill.description, str) and skill.description, (
            f"{skill.path}: `description` must be a non-empty string. An unquoted "
            f"value containing ': ' parses as a mapping and the skill is dropped. "
            f"Got {type(skill.description).__name__}: {skill.description!r}"
        )


def test_description_is_affordable() -> None:
    """Every description is in the system prompt on every single request.

    A skill with no description at all is filtered out of `<available_skills>`
    entirely, so this is a budget rather than a style rule.
    """
    for skill in all_skills():
        description = skill.description
        assert isinstance(description, str), skill.path
        assert len(description) <= MAX_DESCRIPTION, (
            f"{skill.path}: description is {len(description)} characters; it is "
            f"sent on every request, so keep it under {MAX_DESCRIPTION}"
        )


def test_description_is_one_line() -> None:
    for skill in all_skills():
        description = skill.description
        assert isinstance(description, str), skill.path
        assert "\n" not in description, (
            f"{skill.path}: keep the description on one line, so the frontmatter "
            f"cannot be reflowed into something YAML reads differently"
        )


def test_names_are_unique_and_unreserved() -> None:
    """Registration overwrites by name, concurrently, with only a log line.

    So a duplicate is not an error on the box -- it is whichever of the two was
    scanned last, which is not reproducible.
    """
    seen: dict[object, Skill] = {}
    for skill in all_skills():
        assert skill.name not in RESERVED_NAMES, (
            f"{skill.path}: {skill.name!r} is one of opencode's built-in skills "
            f"and would silently replace it"
        )
        clash = seen.get(skill.name)
        assert clash is None, (
            f"{skill.path} and {clash.path if clash else '?'} both register "
            f"{skill.name!r}"
        )
        seen[skill.name] = skill
