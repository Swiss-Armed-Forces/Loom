"""What the installer is allowed to tear down before it repartitions a box.

`release_storage` closes every device-mapper node it can find, which is right: the disks
have to be let go of, and a box that has been installed twice -- or interrupted halfway
-- can be holding them through a mapping this code never made. The rule is exercised
here rather than in a VM because the cost of it being wrong is paid after the partition
table has already been rewritten.

The one exception is the `--lock-key` key store, and it is the exception a reader would
delete as redundant: the mapping is over the USB stick and holds nothing on the internal
disks, so closing it looks harmless. It is not. `install.run` opens it before the first
destructive step and hands it to `encrypt` afterwards, so a sweep that closes it takes
the key away between the two -- and the install dies with "Failed to open key file" on a
box whose disks have just been wiped.
"""

from loom_installer.storage import mappings_to_close

KEY_STORE = "loom-keystore"


def test_everything_holding_the_disks_is_closed() -> None:
    # Including names this installer never created. A previous install, a manual
    # `cryptsetup open`, a different distribution's layout -- all of them keep the
    # partition table busy, and sgdisk fails on a busy device.
    present = ["control", "cryptroot", "loom-root", "somebody-elses-mapping"]

    assert mappings_to_close(present, KEY_STORE) == [
        "cryptroot",
        "loom-root",
        "somebody-elses-mapping",
    ]


def test_the_key_store_survives_the_sweep() -> None:
    # The regression. Found on hardware: the passphrase was accepted, the disks
    # were repartitioned, and then `encrypt` could not open the key it had been
    # given -- because this sweep had closed it three steps earlier.
    present = ["control", "cryptroot", KEY_STORE]

    assert mappings_to_close(present, KEY_STORE) == ["cryptroot"]


def test_an_unlocked_build_closes_everything_it_finds() -> None:
    # `mapping` is set on every stick, locked or not, so sparing it unconditionally
    # would leave a hole in the sweep on every ordinary one: a leftover mapping that
    # happened to carry the name would keep a disk busy with nothing to say why.
    # None is what `release_storage` passes when the build is not locked.
    present = ["control", "cryptroot", KEY_STORE]

    assert mappings_to_close(present, None) == ["cryptroot", KEY_STORE]
