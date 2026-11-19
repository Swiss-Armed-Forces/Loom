"""Tests for `cicd/setup_actions.py`.

These cover the things the generated shell they replace got wrong: quoting a path with a
space in it, writing a secret at the ambient umask, printing a token to the terminal
before asking, and truncating a file that holds somebody else's settings.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, List, Optional

from setup_devenv.actions import (
    AppendLine,
    Context,
    Machine,
    MakeDirectory,
    Outcome,
    Run,
    Runner,
    Session,
    StoreGitLabToken,
    UploadSshKey,
    WriteFile,
    escape_nix_string,
    fold,
    holds_only_a_token,
    render_token_file,
    token_in,
)
from setup_devenv.gitlab import Failure, GitLabError, GitLabUser, SshKey


class RecordingConsole:
    """Collects output and replays a scripted answer."""

    def __init__(self, secret: Optional[str] = None) -> None:
        self.secret = secret
        self.said: List[str] = []

    def say(self, line: str, /) -> None:
        """Record a line."""
        self.said.append(line)

    def ask_secret(self, _question: str, /) -> Optional[str]:
        """Hand back whatever this console was built with."""
        return self.secret


class StubGitLab:
    """A GitLab account that answers from memory, or raises."""

    def __init__(self, error: Optional[GitLabError] = None) -> None:
        self.error = error
        self.uploaded: List[str] = []

    def __call__(self, _token: str) -> "StubGitLab":
        """Stand in for the client factory."""
        return self

    def fetch_user(self) -> GitLabUser:
        """The account, or the scripted failure."""
        if self.error is not None:
            raise self.error
        return GitLabUser("Ada Lovelace", "ada", "ada@example.com")

    def upload_ssh_key(self, title: str, public_key: str) -> SshKey:
        """Record what was actually sent."""
        if self.error is not None:
            raise self.error
        self.uploaded.append(public_key)
        return SshKey(1, title, public_key)


def make_context(repo: Path, **overrides: object) -> Context:
    """A context rooted at a real temporary directory."""
    defaults = {
        "console": RecordingConsole(),
        "make_gitlab": StubGitLab(),
    }
    defaults.update(overrides)
    machine = Machine(
        is_nixos=False,
        has_systemd=True,
        home=repo,
        user="dev",
        shell="bash",
        tools=frozenset({"git"}),
    )
    return Context(repo=repo, machine=machine, **defaults)  # type: ignore[arg-type]


#
# Describing, which is what the operator consents to
#


def test_run_quotes_the_way_it_would_have_to_be_typed() -> None:
    """The command shown is the command that runs, copy-paste included."""
    action = Run(("git", "config", "user.name", "Ada Lovelace"))
    assert action.describe() == "git config user.name 'Ada Lovelace'"


def test_run_normalises_argv_to_a_tuple() -> None:
    """A list field would make equality depend on how the caller spelled it."""
    spelled_as_a_list: Any = ["a", "b"]
    assert Run(spelled_as_a_list) == Run(("a", "b"))


def test_storing_a_token_never_describes_the_token() -> None:
    """Describe() is printed before the prompt, so a secret in it is a leak."""
    described = StoreGitLabToken(Path("/repo/devenv.local.nix")).describe()
    assert "0600" in described
    assert "<the token you type>" in described


#
# Writing files
#


def test_write_file_creates_a_secret_at_the_mode_given(tmp_path: Path) -> None:
    """Opened at 0600 rather than chmod'ed afterwards, so there is no window."""
    target = tmp_path / "devenv.local.nix"
    assert Runner().write_file(target, "secret\n", 0o600)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_text() == "secret\n"


def test_write_file_survives_a_path_with_a_space(tmp_path: Path) -> None:
    """The generated shell redirect this replaces left the path unquoted."""
    target = tmp_path / "a dir with spaces" / "file.nix"
    assert Runner().write_file(target, "ok\n")
    assert target.read_text() == "ok\n"


def test_append_line_survives_a_path_with_a_space(tmp_path: Path) -> None:
    """A home directory with a space broke the generated redirect."""
    rc = tmp_path / "home dir" / ".bashrc"
    rc.parent.mkdir()
    rc.write_text("# existing\n")

    assert AppendLine(rc, 'eval "$(direnv hook bash)"').perform(
        make_context(tmp_path)
    ) == Outcome(ok=True)
    assert rc.read_text() == '# existing\neval "$(direnv hook bash)"\n'


def test_append_line_is_a_no_op_when_the_line_is_already_there(
    tmp_path: Path,
) -> None:
    """Re-checked at the moment it happens, not only when it was assessed."""
    rc = tmp_path / ".bashrc"
    rc.write_text('eval "$(direnv hook bash)"\n')
    AppendLine(rc, 'eval "$(direnv hook bash)"').perform(make_context(tmp_path))
    assert rc.read_text().count("direnv hook bash") == 1


def test_append_line_separates_from_a_file_with_no_trailing_newline(
    tmp_path: Path,
) -> None:
    """Otherwise the hook is glued onto whatever the profile ended with."""
    rc = tmp_path / ".bashrc"
    rc.write_text("export PS1='$ '")
    AppendLine(rc, "hooked").perform(make_context(tmp_path))
    assert rc.read_text() == "export PS1='$ '\nhooked\n"


def test_make_directory_applies_the_mode_to_an_existing_one(tmp_path: Path) -> None:
    """An .ssh left at 0755 by something else is corrected, not accepted."""
    key_dir = tmp_path / ".ssh"
    key_dir.mkdir(mode=0o755)
    MakeDirectory(key_dir, 0o700).perform(make_context(tmp_path))
    assert stat.S_IMODE(key_dir.stat().st_mode) == 0o700


def test_write_file_reports_the_nix_conf_only_when_told(tmp_path: Path) -> None:
    """The daemon restart is offered because of this flag, not a path match."""
    plain = WriteFile(tmp_path / "a.conf", "x\n")
    marked = WriteFile(tmp_path / "b.conf", "x\n", is_nix_conf=True)
    ctx = make_context(tmp_path)

    assert not plain.perform(ctx).nix_conf_changed
    assert marked.perform(ctx).nix_conf_changed


#
# The token file
#


def test_render_token_file_round_trips_through_the_reader() -> None:
    """What the script writes is what the script later finds."""
    assert token_in(render_token_file("glpat-abc123")) == "glpat-abc123"


def test_escaping_a_token_that_would_break_the_nix_string() -> None:
    """A quote or a `${` in a token used to produce an unparsable file."""
    assert escape_nix_string('a"b') == 'a\\"b'
    assert escape_nix_string("a${b") == "a\\${b"
    assert escape_nix_string("a\\b") == "a\\\\b"


def test_a_devenv_local_with_other_settings_is_not_ours_to_rewrite() -> None:
    """`cicd-mode-enter` writes `{ env.cicd = true; }` into this same file."""
    assert not holds_only_a_token("{ env.cicd = true; }\n")
    assert holds_only_a_token("")
    assert holds_only_a_token('{ ... }: { env.GITLAB_TOKEN = "x"; }\n')


def test_storing_a_token_writes_it_at_0600(tmp_path: Path) -> None:
    """The whole reason this is an action and not an `echo >` redirect."""
    console = RecordingConsole(secret="glpat-typed")
    ctx = make_context(tmp_path, console=console)
    target = tmp_path / "devenv.local.nix"

    assert StoreGitLabToken(target).perform(ctx).ok
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert token_in(target.read_text()) == "glpat-typed"
    # Checked before it was written, and never echoed back.
    assert not any("glpat-typed" in line for line in console.said)


def test_storing_a_token_declines_cleanly_with_no_terminal(tmp_path: Path) -> None:
    """`--yes` on a closed stdin used to raise EOFError out of input()."""
    ctx = make_context(tmp_path, console=RecordingConsole(secret=None))
    assert not StoreGitLabToken(tmp_path / "devenv.local.nix").perform(ctx).ok
    assert not (tmp_path / "devenv.local.nix").exists()


def test_a_rejected_token_is_not_written(tmp_path: Path) -> None:
    """Validation comes before the write, so a bad token leaves no file."""
    gitlab = StubGitLab(error=GitLabError(Failure.AUTH, "rejected", 401))
    ctx = make_context(
        tmp_path, console=RecordingConsole(secret="glpat-bad"), make_gitlab=gitlab
    )
    assert not StoreGitLabToken(tmp_path / "devenv.local.nix").perform(ctx).ok
    assert not (tmp_path / "devenv.local.nix").exists()


#
# Uploading a key
#


def test_uploading_sends_the_key_itself(tmp_path: Path) -> None:
    """The shell this replaces built its JSON in single quotes, so GitLab was sent the
    literal string `$KEY_CONTENT` and the upload never once worked."""
    (tmp_path / "devenv.local.nix").write_text(
        '{ ... }: { env.GITLAB_TOKEN = "glpat-stored"; }\n'
    )
    public = tmp_path / "loom_gitlab.pub"
    public.write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbC loom-dev@box\n")

    gitlab = StubGitLab()
    ctx = make_context(tmp_path, make_gitlab=gitlab)
    assert UploadSshKey("loom-dev@box", public).perform(ctx).ok
    assert gitlab.uploaded == ["ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbC loom-dev@box"]


def test_uploading_without_a_stored_token_fails_with_a_pointer(
    tmp_path: Path,
) -> None:
    """--only ssh-key on a fresh checkout says which step to run first."""
    public = tmp_path / "loom_gitlab.pub"
    public.write_text("ssh-ed25519 AAAA x\n")
    console = RecordingConsole()
    ctx = make_context(tmp_path, console=console)

    assert not UploadSshKey("t", public).perform(ctx).ok
    assert any("gitlab-token" in line for line in console.said)


#
# Folding outcomes into the session
#


def test_fold_keeps_a_change_once_it_has_happened() -> None:
    """A later action that changed nothing must not clear an earlier flag."""
    session = fold(Session(), Outcome(ok=True, nix_conf_changed=True))
    assert fold(session, Outcome(ok=True)).nix_conf_changed


def test_fold_preserves_the_options_the_run_started_with() -> None:
    """The session carries both; only the "what changed" half may move."""
    session = Session(dry_run=True, skip_gitlab_token=True)
    folded = fold(session, Outcome(ok=True, nix_now_on_path=True))
    assert folded.dry_run and folded.skip_gitlab_token and folded.nix_on_path
