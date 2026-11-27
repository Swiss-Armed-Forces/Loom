"""Tests for resolving a milestone reference to a milestone."""

from unittest.mock import MagicMock

from aitools.gitlab_api import find_milestone_by_iid, parse_milestone_url_or_id


def _project(milestones: list[MagicMock]) -> MagicMock:
    project = MagicMock()
    project.milestones.list.return_value = milestones
    return project


def test_url_number_is_the_iid() -> None:
    ref = parse_milestone_url_or_id(
        "https://gitlab.com/group/sub/loom/-/milestones/11#tab-issues"
    )
    assert ref.project_path == "group/sub/loom"
    assert ref.milestone_iid == 11


def test_lookup_matches_iid_not_global_id() -> None:
    sova = MagicMock(id=7765424, iid=11, title="1.7.0")
    other = MagicMock(id=11, iid=2, title="other")

    project = _project([other, sova])

    assert find_milestone_by_iid(project, 11) is sova
    assert find_milestone_by_iid(project, 99) is None
