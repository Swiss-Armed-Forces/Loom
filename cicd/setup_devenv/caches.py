"""The binary caches, and the managed block that puts them in `nix.conf`.

Nix refuses a substituter a *client* asks for unless the caller is in `trusted-users`
-- which the nix manual calls "essentially equivalent to giving that user root access
to the system". A daemon that names the caches in its own `/etc/nix/nix.conf` serves
them to everybody without granting anybody anything, so that is what gets written.
`extra-` because the plain spelling replaces the list rather than adding to it, and a
block that forgot `cache.nixos.org` would silently remove it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Sequence, Tuple


class Cache(NamedTuple):
    """A binary cache and the key its paths are signed with."""

    url: str
    public_key: str


# Keep in step with `cachixPublicKeys` and `cachix.pull` in devenv.nix, which
# stay the source of truth. Every cache devenv pulls from has to be here: one
# left out is one the daemon does not know, and an untrusted caller then gets a
# two-line warning about it on every single nix invocation.
CACHES: Tuple[Cache, ...] = (
    Cache(
        "https://devenv.cachix.org",
        "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=",
    ),
    Cache(
        "https://loom.cachix.org",
        "loom.cachix.org-1:qK4ugmN5g4Pvhv45OLcXTwG53ZnSauwrHLVA0A7Y0rs=",
    ),
    Cache(
        "https://nixpkgs-python.cachix.org",
        "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU=",
    ),
)

NIX_CONF = Path("/etc/nix/nix.conf")

# The block this script owns inside nix.conf. Everything between the markers is
# rewritten on each run and everything outside them is left exactly as it was,
# which is what makes a second run a no-op rather than a second copy.
BLOCK_BEGIN = "# >>> loom devenv setup >>>"
BLOCK_END = "# <<< loom devenv setup <<<"


def render_block(caches: Sequence[Cache] = CACHES) -> str:
    """The managed block, markers included, without a trailing newline."""
    urls = " ".join(cache.url for cache in caches)
    keys = " ".join(cache.public_key for cache in caches)
    return "\n".join(
        [
            BLOCK_BEGIN,
            "# Written by cicd/setup-devenv. Edits between the markers are",
            "# overwritten; edits outside them are kept.",
            f"extra-substituters = {urls}",
            f"extra-trusted-public-keys = {keys}",
            BLOCK_END,
        ]
    )


def apply_block(current: str, block: str) -> str:
    """Return `current` with `block` replacing any previous one, else appended.

    Idempotent by construction: feeding the result back in returns it unchanged.
    """
    begin = current.find(BLOCK_BEGIN)
    end = current.find(BLOCK_END, begin + 1) if begin != -1 else -1
    if begin != -1 and end != -1:
        head = current[:begin]
        tail = current[end + len(BLOCK_END) :]
        return f"{head}{block}{tail}"

    if current and not current.endswith("\n"):
        current += "\n"
    separator = "\n" if current else ""
    return f"{current}{separator}{block}\n"


def nixos_snippet(caches: Sequence[Cache] = CACHES) -> str:
    """The same settings as a NixOS `configuration.nix` fragment."""
    urls = "\n".join(f'    "{cache.url}"' for cache in caches)
    keys = "\n".join(f'    "{cache.public_key}"' for cache in caches)
    return "\n".join(
        [
            "nix.settings = {",
            "  extra-substituters = [",
            urls,
            "  ];",
            "  extra-trusted-public-keys = [",
            keys,
            "  ];",
            "};",
        ]
    )
