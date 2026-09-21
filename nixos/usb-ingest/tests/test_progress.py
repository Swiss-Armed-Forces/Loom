"""What the console pane says, and what it is told.

The records are the whole interface between the ingest running as root and the pane
drawn by the operator's tmux server, so what matters here is that one side writes what
the other can read -- including when the two are different versions of this program,
which is what happens to a box mid-upgrade.
"""

import json
import os

from loom_usb_ingest.progress import (
    Counts,
    DeviceProgress,
    Reporter,
    Stage,
    VolumeProgress,
    read_all,
    volume_bytes,
    withdraw,
)
from loom_usb_ingest.watch import render


def test_a_record_survives_the_round_trip(tmp_path) -> None:
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.start_volume("/dev/sdb1", 1, 2, 4096)
    reporter.advance(3, 2048)
    reporter.update(force=True)

    records = read_all(str(tmp_path))
    assert len(records) == 1
    assert records[0].device == "/dev/sdb"
    assert records[0].stage is Stage.COPYING
    assert records[0].counts.copied == 2048
    assert records[0].counts.objects == 3


def test_a_finished_device_says_so(tmp_path) -> None:
    # The line the operator waits for: until it appears, pulling the stick is
    # pulling it mid-copy.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.start_volume("/dev/sdb1", 1, 1, 4096)
    reporter.finish(12, 0)

    record = read_all(str(tmp_path))[0]
    assert record.stage is Stage.DONE
    assert record.finished


def test_failures_are_a_stage_of_their_own(tmp_path) -> None:
    # Still safe to remove, but not "done" -- and the pane colours them apart.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.finish(10, 2)

    record = read_all(str(tmp_path))[0]
    assert record.stage is Stage.FAILED
    assert record.finished


def test_an_unreadable_record_costs_one_line_and_no_more(tmp_path) -> None:
    # A record written by another version of this program, which is what a box
    # halfway through an upgrade has. Dropping it costs one line in the pane;
    # refusing to read any would cost the whole display.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.update(force=True)
    (tmp_path / "sdc.json").write_text(json.dumps({"device": "/dev/sdc"}))
    (tmp_path / "sdd.json").write_text("not json at all")
    (tmp_path / "notes.txt").write_text("ignored")

    assert [record.device for record in read_all(str(tmp_path))] == ["/dev/sdb"]


def test_withdrawing_a_device_that_was_never_there_is_not_an_error(tmp_path) -> None:
    # ExecStopPost fires on every stop, including for a device that never got as
    # far as publishing anything.
    withdraw(str(tmp_path), "sdz")
    assert not read_all(str(tmp_path))


def test_a_missing_directory_reads_as_no_devices(tmp_path) -> None:
    # Which is what ends the watcher, so it must not raise.
    assert not read_all(str(tmp_path / "nothing-here"))


def test_the_pane_is_readable_by_the_operator(tmp_path) -> None:
    # It is drawn by a process the operator's tmux server spawns, so a 0600 record
    # would leave an empty pane on every box.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.update(force=True)

    mode = os.stat(tmp_path / "sdb.json").st_mode
    assert mode & 0o044


def test_a_volume_nothing_can_measure_reads_as_no_total() -> None:
    # Which makes the bar a pulse rather than a bar stuck at 100%.
    assert volume_bytes("/definitely/not/mounted") == 0


def _record(
    stage: Stage = Stage.COPYING, counts: Counts | None = None
) -> DeviceProgress:
    return DeviceProgress(
        device="/dev/sdb",
        name="kingston-a1b2",
        stage=stage,
        volume=VolumeProgress(path="/dev/sdb1", index=1, count=1),
        counts=counts if counts is not None else Counts(1000, 500, 7, 0),
    )


def test_every_stage_renders() -> None:
    # The pane is the only place a stage is ever shown, so a stage added without a
    # rendering would be an empty cell on a console in the field.
    for stage in Stage:
        assert render([_record(stage=stage)]) is not None


def test_a_volume_with_no_total_still_renders() -> None:
    assert render([_record(counts=Counts(total=0))]) is not None
