"""The two parts of an install that are decided rather than executed.

Everything else `install.py` does needs a disk, and is covered by nixos/tests/appliance-
install.nix, which drives its steps against scratch devices in a VM.
"""

from loom_installer.install import (
    PASSPHRASE_ALPHABET,
    PASSPHRASE_GROUP_LENGTH,
    PASSPHRASE_GROUPS,
    default_entry,
    generate_passphrase,
)

LOADER_CONF = """timeout 30
default nixos-generation-1.conf
editor 0
console-mode keep
"""


def test_the_recovery_passphrase_is_transcribable() -> None:
    # It is read off a monitor and typed back in by somebody who has lost the stick,
    # so the shape matters as much as the entropy: no character in the alphabet can
    # be misread as another, and the groups are what make a 30-character string
    # copyable at all.
    passphrase = generate_passphrase()
    groups = passphrase.split("-")

    assert len(groups) == PASSPHRASE_GROUPS
    assert all(len(group) == PASSPHRASE_GROUP_LENGTH for group in groups)
    assert set(passphrase) <= set(PASSPHRASE_ALPHABET) | {"-"}
    assert not set(passphrase) & set("lo01")


def test_two_passphrases_are_not_the_same_passphrase() -> None:
    # Generated per box, on the box. A constant here would mean one key for every
    # appliance ever installed.
    assert generate_passphrase() != generate_passphrase()


def test_the_selected_boot_entry_is_read_rather_than_assumed() -> None:
    # The generation number comes from the file. It is 1 on a freshly mkfs'd root,
    # but nothing may depend on that.
    assert default_entry(LOADER_CONF) == "nixos-generation-1.conf"
    assert (
        default_entry(LOADER_CONF.replace("generation-1", "generation-7"))
        == "nixos-generation-7.conf"
    )


def test_a_loader_conf_without_a_default_says_so() -> None:
    # Which makes `select_setup_entry` warn and leave the entry to the operator,
    # rather than rewrite a line it did not understand.
    assert default_entry("timeout 30\neditor 0\n") is None
    assert default_entry("") is None
