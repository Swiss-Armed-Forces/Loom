#!/usr/bin/env python3
"""Cap how much shell may be inlined into a `.nix` file.

The repository runs `shellcheck -x -o all` over every `.sh` file in the tree and has no
way at all to see shell written as a Nix string. That is the same gap CLAUDE.md records
for shell inlined into a Helm template, and it is closed the same way: the body goes in
a file, and the `.nix` file keeps only the values it needs to hand over.

This is a size cap rather than a ban, because short inline shell is right. A prologue of
`LOOM_FOO=${lib.escapeShellArg ...}` assignments above a `builtins.readFile`, a one-line
`exec`, a `mkdir -p` before a daemon starts -- none of those are better off in a file of
their own.

Effective lines are what is counted, and the subtractions are the whole design: blank
lines, comments, prologue assignments, the `readFile` line itself and heredoc bodies all
drop out. So the idiom this check exists to encourage passes by construction, and a long
block of *prose* in a heredoc -- the failure reports in nixos/tests/ are mostly that --
is not mistaken for a long program.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# How many effective lines of shell may sit in one inline block.
DEFAULT_MAX_LINES = 20

# Attributes whose indented string is shell wherever it appears.
SHELL_ATTRIBUTES = frozenset(
    {
        "script",
        "reload",
        "preStart",
        "postStart",
        "preStop",
        "postStop",
        "enterShell",
        "exec",
        "loginShellInit",
        "interactiveShellInit",
        "shellHook",
        "extraInit",
        "checkPhase",
        "buildPhase",
        "installPhase",
        "buildCommand",
        "postInstall",
        "preBuild",
    }
)

# Attributes that are never shell however they are spelled, checked before
# anything else. Without `testScript` here the `*Script` rule below would claim
# the Python every nixos/tests/ node is driven by.
NOT_SHELL_ATTRIBUTES = frozenset(
    {
        "description",
        "testScript",
        "extraConfig",
        "appendHttpConfig",
        "extraRules",
        "extraModprobeConfig",
        "longDescription",
        "message",
    }
)

# Calls whose `text` argument, or whose trailing string argument, is shell.
SHELL_WRITERS = ("writeShellApplication", "writeShellScriptBin", "writeShellScript")
BUILDER_CALLS = ("runCommand", "runCommandLocal", "runCommandWith")

# nixfmt guarantees an indented string opens as the last token on its line, so
# an opener is simply a line ending in `''`. Keeping line numbers is what lets
# the message point at the block.
OPENER = re.compile(r"^(?P<indent>\s*)(?P<head>.*?)''$")
# The attribute a string is bound to: the first `name =` on the line, not an
# `=` that has to be the last token. Requiring it terminal misses every
# wrapped form -- `script = let tmp = ...; in ''`,
# `script = lib.mkAfter ''`, `x = lib.optionalString cond ''` -- and a missed
# name means the block is never classified at all.
#
# `(?!=)` keeps `==` out of it, so the `if a == b then ''` branches of a
# runCommand report are still reached by the window scan below.
NAMED = re.compile(
    r"(?:[A-Za-z0-9_.\"'-]+\.)?(?P<name>[A-Za-z_][A-Za-z0-9_'-]*)\s*=(?!=)"
)
# Nix comments, stripped before the head is searched for a writer call: a
# comment that merely mentions `writeShellApplication` above a `writeText`
# block would otherwise make that block shell.
COMMENT = re.compile(r"(?<!')#.*$")
# Inside an indented string a literal `''` only ever appears as `''$`, `'''`
# or `''\`, so any other `''` closes it. Matching on that rather than on a
# line of its own is what finds the closer in
# `${builtins.readFile ./x.sh}'';` -- the shape this check exists to reward.
CLOSER = re.compile(r"''(?![$'\\])")

PROLOGUE = re.compile(
    r"^\s*(readonly\s+|export\s+|local\s+)?[A-Za-z_][A-Za-z0-9_]*=\$\{"
)
READ_FILE = re.compile(r"^\s*\$\{builtins\.readFile\b")
# A heredoc opener. Anchored on a redirection rather than on `<<` alone,
# because the bare form also matches the left-shift in `$(( 1 << SHIFT ))` and
# the literal in `echo "a << b"` -- both of which would swallow the rest of
# the block as a heredoc body that never ends, and undercount a long program
# as one line. A redirection's `<<` is preceded by whitespace, a `|`, a `&` or
# the start of the line, and is not inside `$((`.
HEREDOC = re.compile(
    r"(?:^|[\s|&;])<<-?\s*(?P<quote>['\"]?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)"
)
# `$(( ... ))`, dropped before looking for a heredoc: `<<` inside it is a
# shift, and the names on either side look exactly like a tag.
ARITHMETIC = re.compile(r"\$\(\(.*?\)\)")
# The reason is captured rather than required by the pattern, so that a bare
# `allow` is reported as a malformed opt-out instead of quietly falling
# through to the size check and failing for the wrong reason.
OPT_OUT = re.compile(r"#\s*nix-inline-shell:\s*allow\b(?P<reason>.*)$")


@dataclass(frozen=True)
class Block:
    """One inline shell block found in a `.nix` file."""

    path: Path
    name: str
    open_line: int
    close_line: int
    effective: int


@dataclass(frozen=True)
class Finding:
    """A block that is over the cap, or an opt-out with nothing said."""

    block: Block
    message: str


def _head(lines: list[str], open_index: int) -> list[str]:
    """The expression the opener belongs to, read backwards from it.

    Stops at the end of the previous statement, which under nixfmt is a line
    ending in `;` or a `''` closer. That window is what connects a bare `''`
    to the `pkgs.runCommand "x" { }` two lines above it, and a `text = ''` to
    the `pkgs.writeShellApplication {` that gives it its meaning, without ever
    reaching into the binding before.
    """
    head = [lines[open_index]]
    depth = 0
    # True once an `in` has been passed going backwards, until its `let`. The
    # bindings between them end in `;` and are not the end of the statement:
    # `script = let tmp = "..."; in ''` is one binding, and stopping at that
    # semicolon never reaches the `script =` that names it.
    in_let = False
    for index in range(open_index - 1, max(open_index - 40, -1), -1):
        line = lines[index]
        stripped = COMMENT.sub("", line).strip()
        if not stripped:
            continue
        if stripped == "in" or stripped.endswith(" in"):
            in_let = True
        elif stripped == "let" or stripped.endswith("let"):
            in_let = False
        # A `''` here closes the *other* branch of the same expression, not a
        # previous statement -- `if c then ''...'' else ''...''`, which both
        # the runCommand reports in nixos/tests/ are written as.
        sibling_branch = head[-1].strip() in ("else", "then", "in")
        # Depth counted backwards, so a `}` opens a group and a `{` closes it.
        # Only at depth zero does a `;` end the previous statement: the
        # attribute set handed to `pkgs.runCommand "x" { ... } ''` is full of
        # them, and stopping at the first would never reach the call.
        ends_statement = stripped.endswith((";", "''")) or stripped.startswith("''")
        if depth == 0 and ends_statement and not in_let and not sibling_branch:
            break
        head.append(line)
        depth += line.count("}") - line.count("{")
        if depth == 0 and not in_let and NAMED.search(stripped):
            # An assignment opens the expression; nothing above it belongs.
            # `NAMED` rather than a bare `"=" in stripped`, which stops on
            # the `==` of `if a == b then ''` and so never reaches the
            # `runCommand` above it. Suspended inside a `let`, whose bindings
            # are assignments the string sits under rather than the one that
            # names it.
            break
    return head


def _enclosing_attrset(lines: list[str], open_index: int) -> str:
    """The line opening the attribute set this binding sits in.

    `text = ''` is only shell because of the `pkgs.writeShellApplication {`
    several attributes above it, which no backwards window stopping at the
    previous statement can reach.
    """
    depth = 0
    for index in range(open_index - 1, max(open_index - 400, -1), -1):
        line = lines[index]
        depth += line.count("}") - line.count("{")
        if depth < 0:
            return line
    return ""


def _attribute_name(head: list[str]) -> str:
    """The attribute this string is bound to, '' when it is a bare argument.

    The opener's own line answers it whenever the binding is written there --
    `text = ''`, `script = ''`. When it is not, the owner is an *enclosing*
    binding, so only lines indented less than the opener are considered:
    `script =` above a `let ... in ''`, and never the `tmp =` of that `let`
    or the `nativeBuildInputs =` of the attribute set a `runCommand` is
    given, both of which the string sits inside rather than belongs to.
    """

    def name_on(line: str) -> str:
        stripped = COMMENT.sub("", line).strip()
        stripped = stripped[: -len("''")] if stripped.endswith("''") else stripped
        found = NAMED.search(stripped.rstrip())
        return found.group("name") if found else ""

    if not head:
        return ""
    own = name_on(head[0])
    if own:
        return own
    opener_indent = len(head[0]) - len(head[0].lstrip())
    for line in head[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("}", ")")):
            # A closed group: the string is a positional argument to whatever
            # that group belongs to, not a value bound to the attribute above
            # it. `runCommand "x" { ... } ''` is the shape, and without this
            # the last attribute inside the braces is reported as the name.
            return ""
        if len(line) - len(line.lstrip()) >= opener_indent:
            continue
        enclosing = name_on(line)
        if enclosing:
            return enclosing
    return ""


def _is_shell(head: list[str], name: str) -> bool:
    """Decide whether this block holds shell rather than prose or config.

    The name decides where it can. Where it cannot -- `text`, which is a
    program under `writeShellApplication` and markdown, tmux config or an
    nginx snippet under `writeText`, and the bare `''` argument of a builder
    -- the enclosing call does.

    The gap this leaves is a `let` binding whose name says nothing, holding
    shell that reaches a unit by another name. `*Script` is the convention
    that closes it (nixos/key-store.nix's `unlockScript`), and the rule above
    honours it; a binding holding shell and called something else is not
    detected. Naming it is cheaper than teaching this to follow a reference.
    """
    if name in NOT_SHELL_ATTRIBUTES:
        return False
    if name in SHELL_ATTRIBUTES or name.endswith("Script"):
        return True
    text = "\n".join(COMMENT.sub("", line) for line in head)
    return any(call in text for call in SHELL_WRITERS + BUILDER_CALLS)


def effective_lines(body: list[str]) -> int:
    """Count the lines that are actually program text.

    Drops blanks, comments, the prologue assignments that hand Nix values over, the
    `builtins.readFile` line, and anything inside a heredoc -- a heredoc body is data,
    and in this tree it is usually a page of prose.
    """
    count = 0
    heredoc_tag: str | None = None
    for line in body:
        if heredoc_tag is not None:
            if line.strip() == heredoc_tag:
                heredoc_tag = None
            continue
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if PROLOGUE.match(line) or READ_FILE.match(line):
            continue
        count += 1
        found = HEREDOC.search(ARITHMETIC.sub("", line))
        if found:
            heredoc_tag = found.group("tag")
    return count


@dataclass(frozen=True)
class Close:
    """Where an indented string ends."""

    # Index into `lines` of the line carrying the closing `''`.
    index: int
    # Whatever of the body shares that line, before the `''`.
    last: str


def _find_close(lines: list[str], open_index: int) -> Close | None:
    """Where the string opened on `open_index` ends, and its last part-line.

    Character-level because a `''` is not always a closer. Inside the body it can be the
    `''$` / `'''` / `''\\` escapes, and inside a `${...}` interpolation it can open a
    whole nested string -- which is how `lib.optionalString aiEnabled ''...''` splices
    shell into loom-console. A regex over lines reads the first of those as the end of
    the block and silently undercounts everything after it.
    """
    interpolation = 0
    nested = 0
    for probe in range(open_index + 1, len(lines)):
        line = lines[probe]
        column = 0
        while column < len(line):
            rest = line[column:]
            if rest.startswith("''"):
                if rest[2:3] in ("$", "'", "\\"):
                    column += 3
                    continue
                if interpolation and nested == 0:
                    nested = 1  # a nested string opens inside the splice
                elif interpolation:
                    nested = 0
                else:
                    return Close(index=probe, last=line[:column])
                column += 2
                continue
            if rest.startswith("${") and nested == 0:
                interpolation += 1
                column += 2
                continue
            if rest.startswith("}") and interpolation and nested == 0:
                interpolation -= 1
            column += 1
    return None


def scan(path: Path) -> list[Block]:
    """Every inline shell block in one `.nix` file."""
    lines = path.read_text().split("\n")
    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = OPENER.match(line)
        if not match or line.rstrip().endswith("'''"):
            index += 1
            continue
        window = _head(lines, index)
        # The name comes from the window alone. The enclosing attribute set
        # only ever answers the second question -- what kind of writer this
        # string was handed to -- and its own binding name is not this
        # string's.
        name = _attribute_name(window)
        if not _is_shell(window + [_enclosing_attrset(lines, index)], name):
            index += 1
            continue
        closed = _find_close(lines, index)
        if closed is None:
            # An unterminated string is a Nix syntax error, which nixfmt will
            # report far better than this can. Stop looking rather than
            # rescanning the rest of the file as if it were the body.
            break
        body = lines[index + 1 : closed.index] + (
            [closed.last] if closed.last.strip() else []
        )
        blocks.append(
            Block(
                path=path,
                name=name or "<builder>",
                open_line=index + 1,
                close_line=closed.index + 1,
                effective=effective_lines(body),
            )
        )
        index = closed.index + 1
    return blocks


def check(path: Path, max_lines: int) -> list[Finding]:
    """Findings for one file: blocks over the cap, and empty opt-outs."""
    lines = path.read_text().split("\n")
    findings: list[Finding] = []
    for block in scan(path):
        above = lines[block.open_line - 2] if block.open_line >= 2 else ""
        opt_out = OPT_OUT.search(above)
        if opt_out:
            if not opt_out.group("reason").strip():
                findings.append(Finding(block, "opt-out with no reason given"))
            continue
        if block.effective > max_lines:
            findings.append(
                Finding(
                    block,
                    f"{block.effective} effective lines of shell inlined "
                    f"(the cap is {max_lines})",
                )
            )
    return findings


def main() -> int:
    """Check the paths given, or nixos/, and report what is over the cap."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="*", type=Path, help="files or directories to check"
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument(
        "--list",
        action="store_true",
        help="report every block found and its size, rather than only the failures",
    )
    args = parser.parse_args()

    targets: list[Path] = []
    for path in args.paths or [Path("nixos")]:
        targets.extend(sorted(path.rglob("*.nix")) if path.is_dir() else [path])

    if args.list:
        for target in targets:
            for block in scan(target):
                where = f"{target}:{block.open_line}-{block.close_line}"
                print(f"{where} {block.name} {block.effective}")
        return 0

    findings = [
        finding for target in targets for finding in check(target, args.max_lines)
    ]
    for finding in findings:
        block = finding.block
        print(
            f"[!] {block.path}:{block.open_line}: `{block.name}` {finding.message}",
            file=sys.stderr,
        )
    if findings:
        print(
            "\n    Move the body to a .sh file beside the module and read it back with\n"
            "    `${builtins.readFile ./scripts/<name>.sh}`, so `shellcheck -x -o all`\n"
            "    covers it. See the shell section in CLAUDE.md and nixos/README.md.\n"
            "    A block that genuinely has to stay inline takes\n"
            "    `# nix-inline-shell: allow <reason>` on the line above it.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
