"""What installer.nix baked into this stick.

Every value here is set by the wrapper in nixos/installer.nix. Missing means the program
was started outside a stick, and that is fatal rather than defaulted: the three storage
names below decide where the box's stage 1 will look for its root, and guessing one
produces a box that installs perfectly and then never boots again.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


class SettingsError(RuntimeError):
    """A variable installer.nix should have set is missing."""


@dataclass(frozen=True)
class StorageNames:
    """The three names from nixos/storage.nix, kept together because they are one
    fact: where the box's stage 1 will look for its root."""

    volume_group: str
    root_volume: str
    root_device: str


@dataclass(frozen=True)
class KeyStoreNames:
    """What nixos/key-store.nix decided about this stick's key partition.

    Two values rather than one because they are only useful together: `mapping` is
    meaningless unless `locked`, and `locked` without somewhere to open the container
    is a fact nothing can act on. Kept beside `StorageNames` for the same reason that
    one exists -- the box and the stick have to agree, and the agreement is the point.
    """

    # Whether the partition holds a LUKS2 container rather than the key bytes.
    locked: bool
    # The device-mapper name the installer opens that container under.
    mapping: str


@dataclass(frozen=True)
class Settings:
    """The stick's own configuration, read once."""

    # "aa64" or "x64", from config.nixpkgs.hostPlatform.efiArch -- the same value
    # that names the loader installer.nix puts on the stick's ESP. Hardcoding either
    # spelling is how the installer and the image it came from drift apart without
    # anything failing loudly.
    efi_arch: str

    # Named on the menu's header, because two sticks on a desk are otherwise
    # indistinguishable.
    tag: str
    platform: str

    # How long the box waits before installing on its own. installer.nix is also
    # where the length is argued for.
    auto_grace: int

    # From nixos/storage.nix, by way of installer.nix.
    storage: StorageNames

    # From nixos/key-store.nix, by way of installer.nix. See keystore.py.
    key_store: KeyStoreNames

    # Where the three programs live, for the menu's rescue shell and for the menu
    # handing over to `loom-install`.
    bin_dir: str


def _require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise SettingsError(
            f"{name} is not set. The installer is configured by nixos/installer.nix;"
            " run it from a Loom stick, or set the variable by hand."
        )
    return value


def _require_bool(name: str) -> bool:
    """A flag, spelled the way Nix spells one.

    installer.nix sets these with `lib.boolToString`, so the two legal values are
    exactly `true` and `false` -- and anything else is a mistake worth refusing rather
    than coercing. Falling back to False on a typo would silently build the box the
    other way round, which for `LOOM_KEY_LOCKED` means an installer that reads a LUKS
    header and calls it a key.
    """
    value = _require(name)
    if value not in ("true", "false"):
        raise SettingsError(
            f"{name} is {value!r}, which is neither 'true' nor 'false'."
            " nixos/installer.nix sets it with lib.boolToString."
        )
    return value == "true"


@lru_cache(maxsize=1)
def settings() -> Settings:
    """The stick's configuration, resolved on first use.

    Lazy rather than read at import: nixos/tests/appliance-install.nix imports single
    steps out of this package, and an import that reads the environment would make
    every one of them depend on the whole of it.
    """
    return Settings(
        efi_arch=_require("LOOM_EFI_ARCH"),
        tag=_require("LOOM_TAG"),
        platform=_require("LOOM_PLATFORM"),
        auto_grace=int(_require("LOOM_AUTO_GRACE")),
        storage=StorageNames(
            volume_group=_require("LOOM_VG_NAME"),
            root_volume=_require("LOOM_LV_NAME"),
            root_device=_require("LOOM_ROOT_DEVICE"),
        ),
        key_store=KeyStoreNames(
            locked=_require_bool("LOOM_KEY_LOCKED"),
            mapping=_require("LOOM_KEYSTORE_MAPPING"),
        ),
        bin_dir=_require("LOOM_INSTALLER_BIN"),
    )
