"""Tests for `cicd/setup_devenv/caches.py`.

Pure functions over text, plus the three places the cache list is spelled: this module's
copy, `devenv.nix` and `nix-dind/Dockerfile`. Nothing here needs a fake -- anything that
would belongs with the steps instead.
"""

from __future__ import annotations

from pathlib import Path

from setup_devenv.caches import (
    BLOCK_BEGIN,
    BLOCK_END,
    CACHES,
    apply_block,
    nixos_snippet,
    render_block,
)

#
# The managed block
#


def test_apply_block_appends_to_a_file_without_one() -> None:
    """A nix.conf that has never been touched gains the block at the end."""
    result = apply_block("sandbox = true\n", render_block())
    assert result.startswith("sandbox = true\n")
    assert BLOCK_BEGIN in result
    assert result.endswith("\n")


def test_apply_block_is_idempotent() -> None:
    """Re-running never produces a second copy -- the whole point of markers."""
    once = apply_block("sandbox = true\n", render_block())
    twice = apply_block(once, render_block())
    assert once == twice
    assert once.count(BLOCK_BEGIN) == 1


def test_apply_block_replaces_a_stale_block_in_place() -> None:
    """An outdated block is rewritten, not appended beside."""
    stale = "\n".join([BLOCK_BEGIN, "extra-substituters = https://old", BLOCK_END])
    current = f"sandbox = true\n{stale}\nkeep-going = true\n"
    result = apply_block(current, render_block())

    assert "https://old" not in result
    assert result.count(BLOCK_BEGIN) == 1
    # Everything outside the markers survives, on both sides.
    assert "sandbox = true" in result
    assert "keep-going = true" in result


def test_apply_block_preserves_content_after_the_block() -> None:
    """The tail is kept verbatim, so a hand-edited setting below is not lost."""
    current = f"{BLOCK_BEGIN}\nold = 1\n{BLOCK_END}\ncores = 4\n"
    assert apply_block(current, render_block()).endswith("cores = 4\n")


def test_apply_block_handles_a_file_with_no_trailing_newline() -> None:
    """A nix.conf not ending in a newline does not get the block glued on."""
    result = apply_block("sandbox = true", render_block())
    assert "sandbox = true\n" in result
    assert f"sandbox = true{BLOCK_BEGIN}" not in result


def test_apply_block_on_empty_file() -> None:
    """An absent nix.conf reads as empty and gets just the block."""
    result = apply_block("", render_block())
    assert result.startswith(BLOCK_BEGIN)
    assert result.endswith("\n")


def test_render_block_uses_the_extra_prefixed_spelling() -> None:
    """Plain `substituters` would replace the list and drop cache.nixos.org."""
    block = render_block()
    assert "extra-substituters =" in block
    assert "extra-trusted-public-keys =" in block
    assert "\nsubstituters =" not in block


def test_render_block_names_every_cache_and_key() -> None:
    """A cache left out warns on every nix invocation for an untrusted user."""
    block = render_block()
    for cache in CACHES:
        assert cache.url in block
        assert cache.public_key in block


def test_nixos_snippet_names_every_cache_and_key() -> None:
    """The NixOS path has to configure exactly what the nix.conf path does."""
    snippet = nixos_snippet()
    for cache in CACHES:
        assert f'"{cache.url}"' in snippet
        assert f'"{cache.public_key}"' in snippet


#
# The cache list lives in three places and they have to agree
#


def repo_root() -> Path:
    """The checkout holding this test."""
    return Path(__file__).resolve().parent.parent.parent


def test_devenv_nix_declares_every_cache_key() -> None:
    """`cachixPublicKeys` in devenv.nix is where these keys come from.

    The script carries its own copy because it runs before devenv exists, so nothing but
    this test stops the two drifting apart.
    """
    source = (repo_root() / "devenv.nix").read_text(encoding="utf-8")
    for cache in CACHES:
        assert cache.public_key in source, f"devenv.nix is missing {cache.url}'s key"


def test_nix_dind_names_every_cache_and_key() -> None:
    """The CI image configures its daemon the same way a workstation does.

    A cache missing there is one the job's untrusted user cannot reach, which shows up
    as an hours-long rebuild rather than as an error.
    """
    dockerfile = (repo_root() / "nix-dind" / "Dockerfile").read_text(encoding="utf-8")
    for cache in CACHES:
        assert cache.url in dockerfile, f"nix-dind/Dockerfile is missing {cache.url}"
        assert cache.public_key in dockerfile, f"...and {cache.url}'s key"


def test_nix_dind_does_not_grant_trusted_users() -> None:
    """The point of naming the caches there is that nobody has to be trusted.

    `min-free` has to be in that file for the same reason -- it is restricted with no
    allow-list, so the CI command line cannot set it.
    """
    dockerfile = (repo_root() / "nix-dind" / "Dockerfile").read_text(encoding="utf-8")
    directives = [
        line.split('"')[1]
        for line in dockerfile.splitlines()
        if "/etc/nix/nix.conf" in line and 'echo "' in line
    ]
    assert not any(d.startswith("trusted-users") for d in directives), directives
    assert any(d.startswith("min-free") for d in directives), directives
