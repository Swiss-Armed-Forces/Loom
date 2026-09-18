"""Turning a USB device into a stable, safe S3 prefix.

The object key produced here *is* the path an operator sees in the frontend:
`S3Crawler._download_object` builds the file's full name as
`//{bucket}/{object key}`. So this is user-facing text, an Elasticsearch field
and an S3 key all at once, and it has to survive being all three.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass

# Everything outside this collapses to a single dash. Deliberately narrow: the
# result travels through an S3 key, a JSON document, an Elasticsearch field and
# a terminal, and the set below is the one that means the same thing in all four.
_ALLOWED = re.compile(r"[^A-Za-z0-9._-]+")
_EDGES = re.compile(r"^[-.]+|[-.]+$")

# Long enough to stay recognisable on a console, short enough that a nested path
# underneath it does not run into S3's 1024-byte key limit.
MAX_COMPONENT = 48
_DIGEST_LENGTH = 8

UNKNOWN_NAME = "usb"


@dataclass(frozen=True)
class StickIdentity:
    """What a stick is called, and the prefix its contents land under."""

    name: str
    identifier: str

    @property
    def prefix_component(self) -> str:
        """The single path component under `usb-crawled/`."""
        return f"{self.name}-{self.identifier}"


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8", "surrogateescape")).hexdigest()[
        :_DIGEST_LENGTH
    ]


def sanitize_component(raw: str, fallback: str = UNKNOWN_NAME) -> str:
    """Reduce arbitrary device text to one safe path component.

    A suffix of the original's hash is appended whenever anything was changed or
    truncated. Without it two different sticks -- `My Stick (1)` and
    `My Stick [1]` -- would sanitize to the same component and silently share a
    prefix, mixing two pieces of evidence into one folder.
    """
    normalised = unicodedata.normalize("NFC", raw).strip()
    cleaned = _EDGES.sub("", _ALLOWED.sub("-", normalised))

    if not cleaned:
        return f"{fallback}-{_digest(raw)}" if raw else fallback

    if cleaned != normalised or len(cleaned) > MAX_COMPONENT:
        return f"{cleaned[:MAX_COMPONENT]}-{_digest(raw)}"

    return cleaned


def derive_identity(properties: dict[str, str], size_bytes: int) -> StickIdentity:
    """Name and identify a stick from its udev properties.

    The identifier falls through four sources because cheap sticks routinely
    omit or duplicate a serial, and two unlabelled no-name sticks must not land
    in the same prefix. The last resort hashes what little the device does
    report, which is at least stable across re-insertions of the same one.
    """
    raw_name = (
        properties.get("ID_FS_LABEL")
        or " ".join(
            part
            for part in (properties.get("ID_VENDOR"), properties.get("ID_MODEL"))
            if part
        )
        or UNKNOWN_NAME
    )

    raw_identifier = (
        properties.get("ID_SERIAL_SHORT")
        or properties.get("ID_SERIAL")
        or properties.get("ID_FS_UUID")
        or _digest(
            "|".join(
                [
                    properties.get("ID_VENDOR", ""),
                    properties.get("ID_MODEL", ""),
                    str(size_bytes),
                ]
            )
        )
    )

    return StickIdentity(
        name=sanitize_component(raw_name),
        identifier=sanitize_component(raw_identifier, fallback="unknown"),
    )


def volume_component(index: int, label: str | None) -> str:
    """The per-partition path component, for a stick carrying more than one."""
    if label:
        return f"p{index}-{sanitize_component(label)}"
    return f"p{index}"


def object_key(prefix: str, relative_path: str) -> str:
    """Join an S3 prefix and an on-stick relative path.

    Backslashes become separators because NTFS and FAT volumes authored on
    Windows use them, and a key containing one would otherwise render as a single
    flat filename in the frontend rather than as the directory tree it is.
    """
    cleaned = relative_path.replace("\\", "/").lstrip("/")
    parts = [part for part in cleaned.split("/") if part not in ("", ".", "..")]
    return "/".join([prefix.rstrip("/"), *parts])
