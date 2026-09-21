"""What the console pane says, what it is told, and how long it says it for.

The records are the whole interface between the ingest running as root and the pane
drawn by the operator's tmux server, so what matters here is that one side writes what
the other can read -- including when the two are different versions of this program,
which is what happens to a box mid-upgrade.

The other half of this file is about *when* a row leaves the pane, which is the whole
reason the pane exists. It is the device going away, not the copy ending.
"""

import json
import os

from loom_usb_ingest.__main__ import parse_args, release
from loom_usb_ingest.progress import (
    Counts,
    DeviceProgress,
    Reporter,
    Stage,
    VolumeProgress,
    device_present,
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
    reporter.finish(12, 8192, 0)

    record = read_all(str(tmp_path))[0]
    assert record.stage is Stage.DONE
    assert record.finished


def test_what_a_finished_device_reports_is_the_whole_device(tmp_path) -> None:
    # `advance` resets per volume, so the figure left behind on a two-partition
    # stick used to be the second partition's alone -- on a row nobody had time to
    # read. Now that the row stays until the stick comes out, it is read.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.start_volume("/dev/sdb1", 1, 2, 4096)
    reporter.advance(3, 4096)
    reporter.start_volume("/dev/sdb2", 2, 2, 2048)
    reporter.advance(1, 2048)
    reporter.finish(4, 6144, 0)

    record = read_all(str(tmp_path))[0]
    assert record.counts.copied == 6144
    assert record.counts.objects == 4


def test_failures_are_a_stage_of_their_own(tmp_path) -> None:
    # Still safe to remove, but not "done" -- and the pane colours them apart.
    reporter = Reporter(str(tmp_path), "sdb", "/dev/sdb", "kingston-a1b2")
    reporter.finish(10, 4096, 2)

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
        kernel_name="sdb",
        name="kingston-a1b2",
        stage=stage,
        volume=VolumeProgress(path="/dev/sdb1", index=1, count=1),
        counts=counts if counts is not None else Counts(1000, 500, 7, 0),
    )


class _Box:
    """A progress directory and some device nodes to plug and unplug.

    The nodes are ordinary files: `device_present` asks the filesystem whether the
    path is there, which is exactly the question udev answers by deleting /dev/sdb
    when a stick is pulled.
    """

    def __init__(self, tmp_path) -> None:
        self.progress_dir = tmp_path / "progress"
        self.progress_dir.mkdir()
        self.dev = tmp_path / "dev"
        self.dev.mkdir()

    def plug(self, kernel_name: str) -> Reporter:
        node = self.dev / kernel_name
        node.write_text("")
        return Reporter(
            str(self.progress_dir), kernel_name, str(node), f"stick-{kernel_name}"
        )

    def unplug(self, kernel_name: str) -> None:
        (self.dev / kernel_name).unlink()

    def release(self, kernel_name: str | None = None) -> None:
        """The sweep, with or without the device whose ingest has just ended."""
        argv = [
            "--release",
            "--progress-dir",
            str(self.progress_dir),
            # No server listens here, which is the ordinary case on a box where
            # nobody has opened a session: every tmux call is best-effort.
            "--console-socket",
            str(self.dev / "tmux.sock"),
        ]
        if kernel_name is not None:
            argv.append(str(self.dev / kernel_name))
        assert release(parse_args(argv)) == 0

    def stages(self) -> dict[str, Stage]:
        return {
            record.kernel_name: record.stage
            for record in read_all(str(self.progress_dir))
        }


def test_a_finished_stick_stays_in_the_pane_until_it_is_pulled(tmp_path) -> None:
    # The whole point of the pane, and what it did not do: the ingest unit is a
    # oneshot, so its ExecStopPost fires when the COPY ends -- about a second after
    # the row says "done", and with the stick still in the operator's box. Releasing
    # on that event took the screen away before anyone could read it.
    box = _Box(tmp_path)
    box.plug("sdb").finish(12, 4096, 0)

    box.release("sdb")
    assert box.stages() == {"sdb": Stage.DONE}

    box.unplug("sdb")
    box.release()
    assert box.stages() == {}


def test_a_copy_that_never_finished_stops_claiming_to_be_copying(tmp_path) -> None:
    # The unit was stopped, or it died, while the stick stayed in. Without this the
    # row is a lie that persists for exactly as long as the operator leaves it there.
    box = _Box(tmp_path)
    box.plug("sdb").start_volume("/dev/sdb1", 1, 1, 4096)

    box.release("sdb")
    assert box.stages() == {"sdb": Stage.INTERRUPTED}


def test_a_release_judges_only_the_device_it_was_given(tmp_path) -> None:
    # A stick pulled while another one is still copying. The sweep sees both, and
    # the copy in flight must come through it untouched -- it has its own unit,
    # which has not stopped.
    box = _Box(tmp_path)
    box.plug("sdb").start_volume("/dev/sdb1", 1, 1, 4096)
    box.plug("sdc").finish(3, 2048, 0)
    box.unplug("sdc")

    box.release("sdc")
    assert box.stages() == {"sdb": Stage.COPYING}


def test_an_unplugged_device_is_swept_up_by_any_release(tmp_path) -> None:
    # The remove rule starts one unit for every device rather than one per device,
    # so the sweep is told nothing about who went away and has to work it out.
    box = _Box(tmp_path)
    box.plug("sdb").finish(1, 1024, 0)
    box.plug("sdc").finish(2, 2048, 0)
    box.unplug("sdb")

    box.release()
    assert box.stages() == {"sdc": Stage.DONE}


def test_the_pane_drops_a_device_that_is_gone_without_being_withdrawn(
    tmp_path,
) -> None:
    # The backstop under the remove rule: a missed udev event would otherwise leave
    # the split pane on screen for the rest of the boot.
    box = _Box(tmp_path)
    box.plug("sdb").finish(1, 1024, 0)
    record = read_all(str(box.progress_dir))[0]
    assert device_present(record)

    box.unplug("sdb")
    assert not device_present(record)


def test_every_stage_renders() -> None:
    # The pane is the only place a stage is ever shown, so a stage added without a
    # rendering would be an empty cell on a console in the field.
    for stage in Stage:
        assert render([_record(stage=stage)]) is not None


def test_a_volume_with_no_total_still_renders() -> None:
    assert render([_record(counts=Counts(total=0))]) is not None
