"""Unit tests for cicd/check_nix_inline_shell.py.

The two things worth testing are the two the check gets wrong if it is naive:
telling shell apart from the prose, markdown and nginx config that share the
`''...''` syntax, and counting only the lines that are actually a program.
"""

from pathlib import Path

import pytest

from check_nix_inline_shell import check, effective_lines, scan

REPO_ROOT = Path(__file__).resolve().parents[2]


def write(tmp_path: Path, body: str) -> Path:
    """Put a `.nix` fragment on disk for the scanner to read."""
    path = tmp_path / "module.nix"
    path.write_text(body)
    return path


def test_prologue_and_read_file_do_not_count(tmp_path: Path) -> None:
    """The idiom the check exists to encourage has to pass by construction."""
    path = write(
        tmp_path,
        """
{
  loom-thing = pkgs.writeShellApplication {
    name = "loom-thing";
    text = ''
      LOOM_STATE_DIR=${lib.escapeShellArg cfg.stateDir}
      LOOM_DEVICE=${lib.escapeShellArg cfg.device}

      ${builtins.readFile ./scripts/loom_thing.sh}'';
  };
}
""",
    )
    blocks = scan(path)
    assert len(blocks) == 1
    assert blocks[0].name == "text"
    assert blocks[0].effective == 0
    assert not check(path, max_lines=20)


def test_long_unit_script_fails(tmp_path: Path) -> None:
    """A unit `script` over the cap is the regression this exists to catch."""
    body = "\n".join(f"      echo line{n}" for n in range(25))
    path = write(
        tmp_path,
        "{\n  systemd.services.loom-thing = {\n    script = ''\n"
        + body
        + "\n    '';\n  };\n}\n",
    )
    findings = check(path, max_lines=20)
    assert len(findings) == 1
    assert findings[0].block.name == "script"
    assert "25 effective lines" in findings[0].message


def test_description_and_test_script_are_not_shell(tmp_path: Path) -> None:
    """Prose and the VM tests' Python share the syntax and must not be caught.

    `testScript` is the one that bites: the `*Script` rule that finds key-store.nix's
    `unlockScript` would otherwise claim every test node.
    """
    body = "\n".join(f"      prose line {n}" for n in range(40))
    path = write(
        tmp_path,
        "{\n  description = ''\n"
        + body
        + "\n  '';\n  testScript = ''\n"
        + body
        + "\n  '';\n}\n",
    )
    assert not scan(path)


def test_text_is_shell_only_under_a_shell_writer(tmp_path: Path) -> None:
    """`text` is a program under writeShellApplication and data under writeText.

    console.nix holds both: the 360-line assistant and a 180-line tmux configuration, as
    the same attribute name.
    """
    body = "\n".join(f"      line {n}" for n in range(30))
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    app = write(
        tmp_path / "a",
        "{\n  x = pkgs.writeShellApplication {\n    text = ''\n"
        + body
        + "\n    '';\n  };\n}\n",
    )
    conf = write(
        tmp_path / "b",
        "{\n  x = pkgs.writeText \"loom.tmux.conf\" ''\n" + body + "\n  '';\n}\n",
    )
    assert [block.name for block in scan(app)] == ["text"]
    assert not scan(conf)


def test_heredoc_prose_does_not_count(tmp_path: Path) -> None:
    """A page of prose in a quoted heredoc is data, not a long program.

    The failure reports in nixos/tests/ are forty lines of explanation around five lines
    of shell, and extracting those would make them worse.
    """
    prose = "\n".join(f"      explanation line {n}" for n in range(40))
    path = write(
        tmp_path,
        "{\n  x = pkgs.runCommand \"report\" { } ''\n"
        "      cat >&2 <<'EOF'\n" + prose + "\n      EOF\n      exit 1\n  '';\n}\n",
    )
    blocks = scan(path)
    assert len(blocks) == 1
    assert blocks[0].effective == 2
    assert not check(path, max_lines=20)


def test_opt_out_needs_a_reason(tmp_path: Path) -> None:
    """An opt-out is a decision, so it has to say what the decision was."""
    body = "\n".join(f"      echo line{n}" for n in range(25))
    head = "{\n  systemd.services.loom-thing = {\n"
    tail = "\n    '';\n  };\n}\n"

    given = write(
        tmp_path,
        head + "    # nix-inline-shell: allow stage 1 has no store path to call\n"
        "    script = ''\n" + body + tail,
    )
    assert not check(given, max_lines=20)

    (tmp_path / "bare").mkdir()
    bare = write(
        tmp_path / "bare",
        head + "    # nix-inline-shell: allow\n    script = ''\n" + body + tail,
    )
    findings = check(bare, max_lines=20)
    assert len(findings) == 1
    assert "no reason" in findings[0].message


@pytest.mark.parametrize(
    ("opener", "closer"),
    [
        ("  script =\n    let\n      tmp = \"/x.tmp\";\n    in\n    ''", "\n    '';"),
        ("  script = lib.mkAfter ''", "\n  '';"),
        ("  bodyScript = lib.optionalString cond ''", "\n  '';"),
    ],
)
def test_wrapped_bindings_are_still_found(
    tmp_path: Path, opener: str, closer: str
) -> None:
    """A unit script does not stop being one for being wrapped.

    `script = let ... in ''` is how nixos/repo.nix writes its seed unit, and
    requiring `=` to be the last token on the line missed every form like it.
    """
    body = "\n".join(f"      echo line{n}" for n in range(25))
    path = write(tmp_path, "{\n" + opener + "\n" + body + closer + "\n}\n")
    findings = check(path, max_lines=20)
    assert len(findings) == 1
    assert "25 effective lines" in findings[0].message


def test_nested_string_in_an_interpolation_does_not_end_the_block(
    tmp_path: Path,
) -> None:
    """`lib.optionalString c ''...''` inside a body is not the closer.

    This is the whole reason the closer is found character by character. A line scan
    stops at the inner `''` and reads a 30-line program as two.
    """
    path = write(
        tmp_path,
        "{\n  x = pkgs.writeShellApplication {\n    text = ''\n"
        "      echo one\n"
        "      ${lib.optionalString cond ''\n"
        "        echo spliced\n"
        "      ''}\n" + "\n".join(f"      echo line{n}" for n in range(25)) + "\n"
        "    '';\n  };\n}\n",
    )
    blocks = scan(path)
    assert len(blocks) == 1
    assert blocks[0].effective > 20


def test_a_shift_is_not_a_heredoc() -> None:
    """`<<` in arithmetic must not swallow the rest of the block.

    Mistaking one for a heredoc opener fails in the undercount direction, which for a
    size cap is the dangerous way round.
    """
    body = ["x=$((1 << SHIFT))"] + [f"echo line{n}" for n in range(25)]
    assert effective_lines(body) == 26


@pytest.mark.parametrize(
    "name", ["network.nix", "console.nix", "key-store.nix", "repo.nix"]
)
def test_repository_passes_its_own_check(name: str) -> None:
    """The tree this ships with has to be under the cap it introduces."""
    assert not check(REPO_ROOT / "nixos" / name, max_lines=20)


def test_the_unit_script_in_repo_nix_is_seen() -> None:
    """A check that finds nothing passes every file, so anchor one.

    `repo.nix` is the `let ... in` form, and it went undetected until the name rule was
    fixed -- the kind of blindness the test above cannot tell apart from compliance.
    """
    names = [block.name for block in scan(REPO_ROOT / "nixos" / "repo.nix")]
    assert "script" in names


def test_effective_lines_drops_comments_and_blanks() -> None:
    """The counting rule on its own, without a file around it."""
    assert effective_lines(["  # a comment", "", "  echo one", "  echo two"]) == 2
