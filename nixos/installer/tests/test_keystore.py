"""Getting at the key on a stick that keeps it behind a passphrase.

Two properties matter here and neither is visible from anywhere else:

  * An ordinary stick must be *untouched* by this. The whole design rests on
    `unlocked_key` yielding the key partition and issuing no command at all when
    `--lock-key` was not used, because that is what lets `install.encrypt` and
    `enroll_recovery_passphrase` stay identical in both modes.
  * A locked stick must close what it opened, on the way out of a failed install as
    well as a successful one -- an install that raises with the mapping still open
    leaves a plaintext route to the key sitting on the box.

The passphrase itself goes in on a pipe, which is the property `FakeCall` records.
"""

from collections.abc import Iterator

import pytest
from fakes import INSTALLER_ENVIRONMENT, FakeRunner, scripted_ui

from loom_installer import constants, keystore
from loom_installer.settings import settings

MAPPING = "loom-keystore"
MAPPING_PATH = f"/dev/mapper/{MAPPING}"

IS_CONTAINER = ["cryptsetup", "isLuks", "--type", "luks2", constants.KEY_DEVICE]
OPEN = [
    "cryptsetup",
    "open",
    "--type",
    "luks2",
    "--key-file",
    "-",
    constants.KEY_DEVICE,
    MAPPING,
]
CLOSE = ["cryptsetup", "close", MAPPING]


@pytest.fixture(name="locked")
def _locked(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A stick flashed with --lock-key.

    The environment is how nixos/installer.nix configures this program, so setting it is
    using the real interface rather than reaching past one. `cache_clear` is needed
    because `settings()` is deliberately read once per process.
    """
    for name, value in INSTALLER_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("LOOM_KEY_LOCKED", "true")
    monkeypatch.setenv("LOOM_KEYSTORE_MAPPING", MAPPING)
    settings.cache_clear()
    yield
    settings.cache_clear()


@pytest.fixture(name="unlocked")
def _unlocked(monkeypatch: pytest.MonkeyPatch, locked: None) -> None:
    del locked
    monkeypatch.setenv("LOOM_KEY_LOCKED", "false")
    settings.cache_clear()


@pytest.mark.usefixtures("unlocked")
def test_an_ordinary_stick_is_not_touched_at_all() -> None:
    # The property the whole design rests on. If this ever starts issuing a command,
    # every unlocked install has acquired a new way to fail.
    runner = FakeRunner()
    with keystore.unlocked_key(runner, scripted_ui([])) as key_device:
        assert key_device == constants.KEY_DEVICE

    assert not runner.calls


@pytest.mark.usefixtures("locked")
def test_a_locked_stick_opens_the_container_and_yields_the_mapping() -> None:
    runner = FakeRunner()
    runner.succeeds(IS_CONTAINER)
    runner.succeeds(OPEN)
    runner.succeeds(CLOSE)

    with keystore.unlocked_key(runner, scripted_ui(["correct horse"])) as key_device:
        assert key_device == MAPPING_PATH

    # The leading CLOSE clears a mapping left behind by an install that was killed
    # rather than returned from. Without it `cryptsetup open` fails with "device
    # already exists" every time, and an operator holding the correct passphrase is
    # told it is wrong.
    assert runner.calls == [IS_CONTAINER, CLOSE, OPEN, CLOSE]


@pytest.mark.usefixtures("locked")
def test_the_passphrase_goes_in_on_a_pipe() -> None:
    # Never an argument and never a file: either would put it somewhere another
    # process on the box can read it. Same rule `enroll_recovery_passphrase` follows.
    runner = FakeRunner()
    runner.succeeds(IS_CONTAINER)
    runner.succeeds(OPEN)
    runner.succeeds(CLOSE)

    with keystore.unlocked_key(runner, scripted_ui(["correct horse"])):
        pass

    piped = [call for call in runner.piped if call.argv == OPEN]
    assert [call.stdin for call in piped] == ["correct horse"]
    assert not any("correct horse" in argument for argument in sum(runner.calls, []))


@pytest.mark.usefixtures("locked")
def test_a_mistyped_passphrase_can_be_retyped() -> None:
    runner = FakeRunner()
    runner.succeeds(IS_CONTAINER)
    runner.succeeds(CLOSE)
    runner.fails_then_succeeds(OPEN, failures=2)

    with keystore.unlocked_key(runner, scripted_ui(["wrong", "also wrong", "right"])):
        pass

    attempts = [call.stdin for call in runner.piped if call.argv == OPEN]
    assert attempts == ["wrong", "also wrong", "right"]


@pytest.mark.usefixtures("locked")
def test_giving_up_raises_rather_than_installing_with_no_key() -> None:
    # The alternative is worse than a failed install: encrypting the pool against
    # bytes nobody could read back would produce a box that never boots again.
    runner = FakeRunner()
    runner.succeeds(IS_CONTAINER)

    with pytest.raises(keystore.KeystoreError):
        with keystore.unlocked_key(runner, scripted_ui(["a", "b", "c"])):
            pytest.fail("the body must not run when the container stayed shut")

    assert sum(1 for call in runner.calls if call == OPEN) == 3


@pytest.mark.usefixtures("locked")
def test_the_mapping_is_closed_when_the_install_raises() -> None:
    # A raise leaves the box at the menu with the operator still standing there. An
    # open mapping there is a plaintext route to the key that outlives the failure.
    runner = FakeRunner()
    runner.succeeds(IS_CONTAINER)
    runner.succeeds(OPEN)
    runner.succeeds(CLOSE)

    with pytest.raises(RuntimeError, match="partitioning blew up"):
        with keystore.unlocked_key(runner, scripted_ui(["correct horse"])):
            raise RuntimeError("partitioning blew up")

    assert runner.calls[-1] == CLOSE


@pytest.mark.usefixtures("locked")
def test_a_locked_build_on_a_stick_with_no_container_says_so() -> None:
    # The mismatch that cannot be diagnosed later: a --lock-key image flashed by
    # something that wrote raw key bytes. Stage 1 would ask for a passphrase no
    # container has, and there would be nothing on screen to say why.
    runner = FakeRunner()

    with pytest.raises(keystore.KeystoreError, match="no LUKS2 container"):
        with keystore.unlocked_key(runner, scripted_ui([])):
            pytest.fail("the body must not run without a container")
