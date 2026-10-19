"""The file the publisher and the three readers meet in.

Everything here is about a reader that is not the writer: a tmux status line refreshing
every five seconds, a banner generator that can start at any moment, an operator typing
the command. None of them can ask the publisher a question, so the file has to answer
every one of them on its own -- including "is this still true?", which is the whole
reason a published record carries a timestamp.
"""

import json
import os
from dataclasses import replace

from loom_ready.state import (
    STALE_AFTER_S,
    Blocker,
    Counts,
    Readiness,
    Stage,
    Workload,
    publish,
    read,
    state_path,
    summary_path,
)
from loom_ready.text import summary

BASE = Readiness(
    stage=Stage.ROLLING_OUT,
    counts=Counts(ready=12, total=18),
    workloads=[Workload(kind="Deployment", name="api", desired=1, ready=0)],
    blockers=[Blocker(pod="loom-ollama-0", reason="ImagePullBackOff")],
    updated=1000.0,
    changed=900.0,
)


def record(**overrides) -> Readiness:
    return replace(BASE, **overrides)


def test_a_published_record_comes_back_whole(tmp_path):
    """Including the lists, which are what the pane draws under the bar."""
    original = record()
    publish(str(tmp_path), original, summary(original))
    assert read(str(tmp_path), now=1000.0) == original


def test_the_banner_gets_a_line_rather_than_a_document(tmp_path):
    """box.nix reads this with `cat`.

    Handing the banner JSON would mean putting `jq` in its closure to render a line it
    could have been given -- and the banner is a shell script assembling an agetty issue
    file, where every dependency is one more thing that can fail before a login prompt.
    """
    original = record()
    publish(str(tmp_path), original, summary(original))
    with open(summary_path(str(tmp_path)), encoding="utf-8") as handle:
        content = handle.read()
    assert content == summary(original) + "\n"
    assert content.count("\n") == 1


def test_a_stale_record_is_no_record(tmp_path):
    """ "ready" that stopped being recomputed an hour ago is the worst claim here.

    It is also the likely one: the publisher is a unit, and units die. A reader that kept
    believing the last thing it was told would leave a box saying it is up long after it
    stopped being.
    """
    publish(str(tmp_path), record(updated=1000.0), "Loom: ready.")
    assert read(str(tmp_path), now=1000.0 + STALE_AFTER_S - 1) is not None
    assert read(str(tmp_path), now=1000.0 + STALE_AFTER_S + 1) is None


def test_no_file_at_all_is_not_an_error(tmp_path):
    """The first seconds of a boot, and every second of a setup-mode box."""
    assert read(str(tmp_path)) is None


def test_a_record_from_another_version_is_dropped_not_raised(tmp_path):
    """The publisher and the readers are upgraded together, but /run outlives neither.

    Dropping one record costs a refresh. Raising would take out the status line -- or the
    banner -- of a box that is otherwise fine.
    """
    original = record()
    publish(str(tmp_path), original, summary(original))
    with open(state_path(str(tmp_path)), encoding="utf-8") as handle:
        raw = json.load(handle)
    del raw["counts"]
    with open(state_path(str(tmp_path)), "w", encoding="utf-8") as handle:
        json.dump(raw, handle)

    assert read(str(tmp_path), now=1000.0) is None


def test_junk_in_the_file_is_dropped_too(tmp_path):
    with open(state_path(str(tmp_path)), "w", encoding="utf-8") as handle:
        handle.write("{ this is not json")
    assert read(str(tmp_path)) is None


def test_both_files_are_readable_by_the_operator(tmp_path):
    """The readers run as the operator; only the writer is root.

    Two of the three are spawned by the operator's tmux server, and the third is a shell
    script in the banner's closure. None of them can be given a root-only file.
    """
    original = record()
    publish(str(tmp_path), original, summary(original))
    for path in (state_path(str(tmp_path)), summary_path(str(tmp_path))):
        assert os.stat(path).st_mode & 0o044 == 0o044, path


def test_publishing_leaves_no_temporary_files_behind(tmp_path):
    """The reader lists nothing, but /run is small and this runs every five seconds."""
    for tick in range(5):
        original = record(updated=1000.0 + tick)
        publish(str(tmp_path), original, summary(original))
    assert sorted(os.listdir(str(tmp_path))) == ["state.json", "summary"]


def test_a_record_is_never_half_written(tmp_path):
    """The status line reads this on a timer; it must not be able to catch a partial
    one.

    Asserted through the mechanism rather than by racing it: the write lands through a
    temporary file in the same directory and an `os.replace`, which is atomic, so no
    reader can observe an intermediate state. What this checks is that the destination is
    only ever the finished document -- a rewrite with different content leaves no trace
    of the old one and no trace of the new one's assembly.
    """
    publish(str(tmp_path), record(counts=Counts(1, 18)), "Loom: starting.")
    publish(str(tmp_path), record(counts=Counts(18, 18)), "Loom: ready.")
    with open(state_path(str(tmp_path)), encoding="utf-8") as handle:
        raw = json.load(handle)
    assert raw["counts"] == {"ready": 18, "total": 18}


def test_a_directory_that_does_not_exist_yet_is_made(tmp_path):
    """Tmpfiles creates it on the box; a test box and a debug run have neither."""
    target = os.path.join(str(tmp_path), "ready")
    publish(target, record(), "Loom: starting.")
    assert read(target, now=1000.0) is not None
