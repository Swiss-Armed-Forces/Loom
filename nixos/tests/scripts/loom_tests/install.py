"""What the installer lays down on the internal disks.

The installer image is deliberately not booted. It wants an NVMe the test framework
cannot supply -- `target_disks` accepts nothing else, on purpose -- and a whole box
closure to copy. What is worth testing is the layout, and the layout is reachable by
calling the installer's own steps one at a time, which is why they are module-level
functions taking a runner rather than methods on an object.

`volume_group`, `root_volume` and `root_device` are passed in from default.nix, taken
off the *appliance's* evaluated configuration rather than restated here. A test that
spelled the path itself could agree with neither side and still pass.
"""

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from loom_tests.driver import Machine, StartAll, Subtest


class Storage(NamedTuple):
    """The three names nixos/storage.nix gives the pool.

    One argument rather than three, because they are one fact -- where the box's stage 1
    will look for its root -- and because the .nix file that calls `run` interpolates
    all three from the same evaluated configuration.
    """

    volume_group: str
    root_volume: str
    root_device: str


# vda is the node's own root and is never named below.
DISKS = ["/dev/vdb", "/dev/vdc"]

# What a `--lock-key` stick's key container is opened as. Only this file cares:
# the box uses nixos/key-store.nix's `mapping` and the flash script uses a third
# name, because none of the three is ever open at the same time as another.
KEYSTORE_MAPPING = "loom-keystore"

# The passphrase over that container in this test. A fixed string rather than a
# generated one: what is being checked here is that a container works as a key
# file, and generating the passphrase is cicd/build_appliance_image.sh's job.
KEYSTORE_PASSPHRASE = "correct-horse-battery-staple-stick-key-phrase"


class Installer:
    """The installer package, driven one step at a time on the node.

    Each call is a `python3 -c` on the guest with the environment the wrapper in
    installer.nix would have set. The three storage names reach this test from the
    appliance's own configuration by way of default.nix, so a rename in
    nixos/storage.nix arrives here rather than leaving a literal somebody has to
    remember to update.
    """

    def __init__(self, machine: "Machine", storage: Storage) -> None:
        self.machine = machine
        self.environment = " ".join(
            [
                "LOOM_EFI_ARCH=x64",
                "LOOM_TAG=test",
                "LOOM_PLATFORM=test",
                "LOOM_AUTO_GRACE=1",
                "LOOM_INSTALLER_BIN=/run/current-system/sw/bin",
                f"LOOM_VG_NAME={storage.volume_group}",
                f"LOOM_LV_NAME={storage.root_volume}",
                f"LOOM_ROOT_DEVICE={storage.root_device}",
                # An ordinary stick, which is what every step below but the locked
                # subtest is about. `locked=True` overrides it for that one.
                "LOOM_KEY_LOCKED=false",
                f"LOOM_KEYSTORE_MAPPING={KEYSTORE_MAPPING}",
            ]
        )

    def step(self, statement: str, locked: bool = False) -> str:
        """Run one statement with the installer's modules imported."""
        program = (
            "from loom_installer import devices, install, keystore, storage, wipe;"
            "from loom_installer.commands import Subprocess;"
            "runner = Subprocess();"
            f"{statement}"
        )
        # Appended rather than substituted: `env` takes the last assignment of a
        # name, so this overrides the default above without rebuilding the string.
        environment = self.environment
        if locked:
            environment += " LOOM_KEY_LOCKED=true"
        return self.machine.succeed(f"env {environment} python3 -c {_quote(program)}")


def _quote(program: str) -> str:
    """Single-quote a Python program for the guest's shell."""
    return "'" + program.replace("'", "'\\''") + "'"


def run(
    installer: "Machine",
    *,
    start_all: "StartAll",
    subtest: "Subtest",
    storage: Storage,
) -> None:
    """The whole test, as the .nix file calls it."""
    start_all()
    installer.wait_for_unit("multi-user.target")

    steps = Installer(installer, storage)
    volume_group = storage.volume_group
    root_device = storage.root_device

    # The stick's key partition, as a plain file: the installer reads 4096 bytes of
    # it exactly as systemd-cryptsetup will in stage 1, and cryptsetup does not care
    # which kind of thing it was handed.
    installer.succeed("dd if=/dev/urandom of=/tmp/key bs=4096 count=1 status=none")
    installer.succeed(
        "dd if=/dev/urandom of=/tmp/other-key bs=4096 count=1 status=none"
    )

    with subtest("every eligible disk joins one volume group"):
        _pool_spans_every_disk(installer, steps, volume_group)

    with subtest("the ESP lands on the first disk and only the first"):
        _esp_is_on_the_first_disk(installer)

    with subtest("the container is exactly where the box will look for it"):
        _container_is_where_stage_one_looks(installer, steps, root_device)

    with subtest("the target ESP is private while the installer writes it"):
        _the_target_esp_is_not_world_readable(installer, steps)

    with subtest("the recovery passphrase opens the same container"):
        _recovery_passphrase_opens_the_container(
            installer, steps, volume_group, root_device
        )

    with subtest("a stick recognises the box it installed, and only that box"):
        _only_its_own_stick_claims_the_pool(installer, steps, root_device)

    with subtest("the wipe still reaches the key material"):
        _the_wipe_reaches_the_key_material(installer, steps, volume_group, root_device)

    with subtest("a single-disk box gets the same layout"):
        _one_disk_gets_the_same_layout(installer, steps, volume_group, root_device)

    with subtest("a passphrase-locked key container installs the same box"):
        _a_locked_key_container_is_just_another_key(
            installer, steps, volume_group, root_device
        )


def _pool_spans_every_disk(
    installer: "Machine", steps: Installer, volume_group: str
) -> None:
    steps.step(f"install.partition(runner, {DISKS!r})")
    steps.step(f"install.create_pool(runner, {len(DISKS)})")

    # Both members, not just the first. A pool that silently forms over one disk and
    # leaves the second unused looks, from the console, exactly like a working
    # install.
    pv_count = installer.succeed(f"vgs --noheadings -o pv_count {volume_group}").strip()
    assert pv_count == str(len(DISKS)), f"volume group spans {pv_count} PVs"

    pvs = installer.succeed("pvs --noheadings -o pv_name,vg_name")
    for disk in DISKS:
        assert disk in pvs, f"{disk} is not a physical volume:\n{pvs}"

    # And the volume takes the whole group. Extents left behind would cost the
    # operator disk space that nothing would ever report as missing.
    free = installer.succeed(
        f"vgs --noheadings --nosuffix --units b -o vg_free {volume_group}"
    ).strip()
    assert free == "0", f"{free} bytes left unallocated"


def _esp_is_on_the_first_disk(installer: "Machine") -> None:
    installer.succeed("test -b /dev/disk/by-partlabel/loom-esp")
    esp_parent = installer.succeed(
        "lsblk --noheadings --raw --paths --output PKNAME "
        "/dev/disk/by-partlabel/loom-esp | head -1"
    ).strip()
    assert esp_parent == DISKS[0], f"ESP is on {esp_parent}, not {DISKS[0]}"


def _container_is_where_stage_one_looks(
    installer: "Machine", steps: Installer, root_device: str
) -> None:
    # The assertion this file exists for. `root_device` comes off the appliance's own
    # configuration, so this is box-hardware.nix's stage-1 device and the key guard's
    # device, not a string chosen here.
    installer.succeed(f"test -b {root_device}")
    steps.step("install.encrypt(runner, '/tmp/key')")
    installer.succeed(f"cryptsetup isLuks {root_device}")
    installer.succeed("test -b /dev/mapper/cryptroot")

    # The filesystem goes on the mapping, not on a partition.
    steps.step("install.make_filesystems(runner)")
    fstype = installer.succeed(
        "lsblk --noheadings --raw --output FSTYPE /dev/mapper/cryptroot"
    ).strip()
    assert fstype == "ext4", f"root filesystem is {fstype}"


def _the_target_esp_is_not_world_readable(
    installer: "Machine", steps: Installer
) -> None:
    # vfat has no permissions on disk: every mode comes from the mount options, so the
    # ESP is only as private as whoever mounted it. nixos-install writes
    # /boot/loader/random-seed through this mount, and bootctl warns that the seed is
    # world accessible when it is not 0077 -- the last thing an operator sees at the
    # end of an install. Asserted against a real vfat mount rather than the argv,
    # because it is the resulting mode that the warning is about.
    #
    # This is also the mount the two subtests below use. It is left in place for them.
    steps.step("install.mount_target(runner)")

    # `umask` is an argument to the driver rather than a stored option: vfat splits it
    # into the file and directory masks and reports only those back, so this is what
    # `umask=0077` looks like once it has been accepted.
    options = installer.succeed(
        "findmnt --noheadings --output OPTIONS --target /mnt/boot"
    ).strip()
    for mask in ("fmask=0077", "dmask=0077"):
        assert mask in options, f"/mnt/boot is mounted {options}"

    installer.succeed("touch /mnt/boot/seed-probe")
    mode = installer.succeed("stat -c %a /mnt/boot/seed-probe").strip()
    installer.succeed("rm /mnt/boot/seed-probe")
    assert mode == "700", f"a file on the target ESP is mode {mode}"


def _recovery_passphrase_opens_the_container(
    installer: "Machine", steps: Installer, volume_group: str, root_device: str
) -> None:
    # Losing the stick must not mean losing the box. The keyslot is enrolled against
    # the pooled container now, so one added to the wrong device would leave the
    # passphrase on the login banner useless -- and nothing would say so until
    # somebody needed it.
    passphrase = steps.step(
        "print(install.enroll_recovery_passphrase(runner, '/tmp/key'))"
    ).strip()
    assert len(passphrase.split("-")) == 6, passphrase
    installer.succeed("test -s /mnt/var/lib/loom/recovery-passphrase")
    steps.step("install.unmount_target(runner)")

    # `unmount_target` also deactivates the group, so the container has to be brought
    # back before it can be opened -- which is itself worth asserting: an installer
    # that left the pool active would leave the partition tables busy for whatever
    # the operator picks next.
    installer.fail(f"test -b {root_device}")
    installer.succeed(f"vgchange --activate y {volume_group}")
    installer.succeed(f"printf %s {passphrase} >/tmp/pass")
    installer.succeed(
        f"cryptsetup luksOpen --test-passphrase --key-file /tmp/pass {root_device}"
    )


def _only_its_own_stick_claims_the_pool(
    installer: "Machine", steps: Installer, root_device: str
) -> None:
    # The guard that replaces the typed INSTALL word. It has to answer yes to the key
    # that built this pool and no to any other, or an unattended install either
    # destroys a working box or refuses to provision a new one.
    claimed = steps.step(
        "print(storage.pool_claimed_by_key(runner, '/tmp/key'))"
    ).strip()
    assert claimed == "True", claimed

    foreign = steps.step(
        "print(storage.pool_claimed_by_key(runner, '/tmp/other-key'))"
    ).strip()
    assert foreign == "False", foreign

    # Looking must not leave the box changed.
    installer.fail(f"test -b {root_device}")


def _the_wipe_reaches_the_key_material(
    installer: "Machine", steps: Installer, volume_group: str, root_device: str
) -> None:
    # The regression this guards: the container moved onto a logical volume, so
    # `wipe_disk`'s per-partition sweep no longer finds it. With layer 1 skipped the
    # wipe says nothing and falls through to layers that are slower and weaker -- a
    # silent downgrade of the only step that matters.
    steps.step("wipe.erase_pool_keys(runner)")
    installer.fail(f"vgs {volume_group}")
    installer.succeed(f"vgchange --activate y {volume_group} || true")
    installer.fail(f"test -b {root_device}")


def _one_disk_gets_the_same_layout(
    installer: "Machine", steps: Installer, volume_group: str, root_device: str
) -> None:
    # One closure serves both, which is why the disks are pooled rather than a second
    # image built for boxes with two slots. The device path must not depend on how
    # many disks were found.
    installer.succeed(f"sgdisk --zap-all {DISKS[1]}")
    steps.step(f"install.partition(runner, [{DISKS[0]!r}])")
    steps.step("install.create_pool(runner, 1)")

    installer.succeed(f"test -b {root_device}")
    pv_count = installer.succeed(f"vgs --noheadings -o pv_count {volume_group}").strip()
    assert pv_count == "1", pv_count


def _a_locked_key_container_is_just_another_key(
    installer: "Machine", steps: Installer, volume_group: str, root_device: str
) -> None:
    """`--lock-key`, end to end below the prompt.

    The claim the whole feature rests on is that nothing downstream of the key can
    tell the two kinds of stick apart -- both are a path holding 4096 plaintext bytes
    at offset 0, and `install.encrypt` and `enroll_recovery_passphrase` are handed
    one without being told which. This builds the locked kind for real, with real
    cryptsetup, and runs the same two steps against it.

    The *order* below matters as much as the steps, and is the order `install.run`
    uses: the container is opened first, and `partition` runs after it. That is
    what caught the one bug this feature shipped with -- `release_storage` swept
    every /dev/mapper node before repartitioning and closed the key store along
    with them, so `encrypt` was handed a key that had stopped existing two steps
    earlier. An earlier version of this subtest partitioned first and saw nothing.

    Not covered here: the prompt that gets the container open on a real stick
    (installer/tests/test_keystore.py) and the initrd unit that does the same job in
    stage 1 (nixos/key-store.nix), which no VM test in this repository can reach.
    """
    # Start from a pool this subtest owns. The one above left a single-disk group.
    installer.succeed(f"vgremove --force {volume_group}")
    installer.succeed("pvscan --cache")

    # The stick's key partition as it comes off `build-appliance-image --flash
    # --lock-key`: 32M, a LUKS2 container, 4096 random bytes written inside it.
    # 32M because a LUKS2 header puts the payload at 16M -- which is the whole
    # reason nixos/installer.nix sizes the partition the way it does.
    installer.succeed("truncate --size=32M /tmp/locked-key.img")
    key_loop = installer.succeed("losetup --find --show /tmp/locked-key.img").strip()
    installer.succeed(f"printf %s {KEYSTORE_PASSPHRASE} >/tmp/keystore-pass")
    # The same KDF the flash script pins, so this also fails if that changes to
    # something the box cannot afford.
    installer.succeed(
        "cryptsetup luksFormat --type luks2 --batch-mode --pbkdf argon2id"
        " --pbkdf-force-iterations 4 --pbkdf-memory 1048576 --pbkdf-parallel 4"
        f" --key-file /tmp/keystore-pass {key_loop}"
    )

    # A container is what a locked build calls PRESENT.
    state = steps.step(
        f"print(devices.key_state(runner, {key_loop!r}, True))", locked=True
    ).strip()
    assert state == "present", state

    # And raw key bytes are what it calls EMPTY -- the case that matters, because a
    # locked image flashed by something that wrote the key raw boots to a stage 1
    # prompt no container can answer, with nothing on screen to say why. `EMPTY`
    # rather than `MISSING` is deliberate: it is the word that sends an operator to
    # --flash instead of hunting for a stick that is already plugged in.
    installer.succeed("truncate --size=32M /tmp/raw-key.img")
    installer.succeed(
        "dd if=/dev/urandom of=/tmp/raw-key.img bs=4096 count=1"
        " conv=notrunc status=none"
    )
    raw_loop = installer.succeed("losetup --find --show /tmp/raw-key.img").strip()
    raw_state = steps.step(
        f"print(devices.key_state(runner, {raw_loop!r}, True))", locked=True
    ).strip()
    assert raw_state == "empty", raw_state
    # The same partition is PRESENT to an ordinary build, so this is the flag
    # deciding, not the bytes.
    unlocked_state = steps.step(
        f"print(devices.key_state(runner, {raw_loop!r}, False))"
    ).strip()
    assert unlocked_state == "present", unlocked_state
    installer.succeed(f"losetup --detach {raw_loop}")

    installer.succeed(
        f"cryptsetup open --type luks2 --key-file /tmp/keystore-pass {key_loop}"
        f" {KEYSTORE_MAPPING}"
    )
    mapping = f"/dev/mapper/{KEYSTORE_MAPPING}"
    installer.succeed(f"dd if=/dev/urandom of={mapping} bs=4096 count=1 status=none")

    # Now partition, with the key store already open -- `install.run`'s order. The
    # sweep inside `partition` closes every other /dev/mapper node before it
    # touches a table, and this one has to come out the far side of it.
    steps.step(f"install.partition(runner, [{DISKS[0]!r}])", locked=True)
    installer.succeed(f"test -b {mapping}")
    steps.step("install.create_pool(runner, 1)", locked=True)

    # From here on it is the ordinary install, handed the mapping instead of a
    # partition. Nothing in these three calls knows the difference.
    steps.step(f"install.encrypt(runner, {mapping!r})", locked=True)
    installer.succeed(f"cryptsetup isLuks {root_device}")
    installer.succeed("test -b /dev/mapper/cryptroot")

    steps.step("install.make_filesystems(runner)", locked=True)
    steps.step("install.mount_target(runner)", locked=True)
    passphrase = steps.step(
        f"print(install.enroll_recovery_passphrase(runner, {mapping!r}))", locked=True
    ).strip()
    assert len(passphrase.split("-")) == 6, passphrase
    steps.step("install.unmount_target(runner)", locked=True)

    # The box's half: stage 1 reads 4096 bytes out of the unlocked container and
    # they have to open the root. Asserted through cryptsetup directly, which is
    # what systemd-cryptsetup will do with box-hardware.nix's keyFile.
    installer.succeed(f"vgchange --activate y {volume_group}")
    installer.succeed(
        "cryptsetup luksOpen --test-passphrase --keyfile-size 4096"
        f" --key-file {mapping} {root_device}"
    )

    # And the recovery passphrase still works beside it, which is the promise that
    # a lost stick passphrase is not a lost box.
    installer.succeed(f"printf %s {passphrase} >/tmp/locked-recovery")
    installer.succeed(
        "cryptsetup luksOpen --test-passphrase"
        f" --key-file /tmp/locked-recovery {root_device}"
    )

    installer.succeed(f"cryptsetup close {KEYSTORE_MAPPING}")
    installer.succeed(f"losetup --detach {key_loop}")
