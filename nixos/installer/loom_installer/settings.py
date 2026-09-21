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
        bin_dir=_require("LOOM_INSTALLER_BIN"),
    )
