from loom_usb_ingest.naming import (
    MAX_COMPONENT,
    derive_identity,
    object_key,
    sanitize_component,
    volume_component,
)


def test_a_clean_label_is_left_alone():
    assert sanitize_component("KINGSTON") == "KINGSTON"


def test_spaces_and_punctuation_collapse_and_gain_a_digest():
    result = sanitize_component("My Stick (1)")

    assert result.startswith("My-Stick-1")
    assert len(result.split("-")[-1]) == 8


def test_labels_that_would_collide_stay_distinct():
    """The whole reason the digest suffix exists.

    Two different sticks whose labels sanitize identically must not share a
    prefix -- that would silently merge two pieces of evidence into one folder.
    """
    assert sanitize_component("My Stick (1)") != sanitize_component("My Stick [1]")


def test_an_empty_label_falls_back():
    assert sanitize_component("") == "usb"


def test_a_label_of_only_punctuation_falls_back_with_a_digest():
    result = sanitize_component("///")

    assert result.startswith("usb-")


def test_a_long_label_is_truncated_and_suffixed():
    result = sanitize_component("A" * 200)

    assert len(result) == MAX_COMPONENT + 9
    assert result.startswith("A" * MAX_COMPONENT)


def test_separators_never_survive():
    assert "/" not in sanitize_component("a/b/c")
    assert ".." not in sanitize_component("..")


def test_identity_prefers_the_filesystem_label_and_short_serial():
    identity = derive_identity(
        {
            "ID_FS_LABEL": "EVIDENCE",
            "ID_SERIAL_SHORT": "4C530001234567",
            "ID_VENDOR": "Kingston",
        },
        size_bytes=64_000_000_000,
    )

    assert identity.prefix_component == "EVIDENCE-4C530001234567"


def test_identity_falls_back_to_vendor_and_model():
    identity = derive_identity(
        {"ID_VENDOR": "SanDisk", "ID_MODEL": "Ultra Fit", "ID_FS_UUID": "ABCD-1234"},
        size_bytes=1,
    )

    assert identity.name.startswith("SanDisk-Ultra-Fit")
    assert identity.identifier == "ABCD-1234"


def test_identity_of_a_nameless_stick_is_stable_across_reinsertions():
    """Cheap sticks report no serial and no label, and must still be recognisable."""
    properties = {"ID_VENDOR": "Generic", "ID_PATH": "pci-0000:00:14.0-usb-0:2:1.0"}

    first = derive_identity(properties, size_bytes=8_000_000_000)
    second = derive_identity(dict(properties), size_bytes=8_000_000_000)

    assert first.identifier == second.identifier


def test_two_identical_nameless_sticks_do_not_share_a_prefix():
    """The case the fallback exists for, and the one that costs documents.

    Same vendor, same model, same capacity -- everything a no-name stick reports.
    Sharing an identifier means sharing a prefix, and `mc mirror` would then overwrite
    one stick's DCIM/IMG_0001.JPG with the other's, silently.
    """
    properties = {"ID_VENDOR": "Generic", "ID_MODEL": "Flash Disk"}

    first = derive_identity(
        dict(properties, ID_PATH="pci-0000:00:14.0-usb-0:2:1.0"),
        size_bytes=8_000_000_000,
    )
    second = derive_identity(
        dict(properties, ID_PATH="pci-0000:00:14.0-usb-0:3:1.0"),
        size_bytes=8_000_000_000,
    )

    assert first.identifier != second.identifier
    assert first.prefix_component != second.prefix_component


def test_sticks_of_different_capacities_are_told_apart():
    first = derive_identity({"ID_VENDOR": "Generic"}, size_bytes=8_000_000_000)
    second = derive_identity({"ID_VENDOR": "Generic"}, size_bytes=16_000_000_000)

    assert first.identifier != second.identifier


def test_volume_component_with_and_without_a_label():
    assert volume_component(2, None) == "p2"
    assert volume_component(2, "DATA") == "p2-DATA"


def test_object_key_preserves_the_on_stick_path():
    assert (
        object_key("usb-crawled/EVIDENCE-4C53", "reports/2026/q1.pdf")
        == "usb-crawled/EVIDENCE-4C53/reports/2026/q1.pdf"
    )


def test_object_key_translates_windows_separators():
    """NTFS and FAT media authored on Windows use backslashes.

    Left alone they would render as one flat filename rather than a tree.
    """
    assert object_key("p", "Users\\alice\\notes.txt") == "p/Users/alice/notes.txt"


def test_object_key_cannot_escape_its_prefix():
    assert object_key("p", "../../etc/shadow") == "p/etc/shadow"
    assert object_key("p", "/absolute/path") == "p/absolute/path"
