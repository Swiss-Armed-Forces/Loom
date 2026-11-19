"""Tests for `cicd/setup_devenv/steps.py`.

The script installs things, so what is tested here is everything it decides *before* it
does: how the managed nix.conf block is written and rewritten, what each step concludes
from a given machine, and that --only/--skip select what they say.

Every collaborator is injected -- the runner, the console, the GitLab client and the set
of executables on PATH -- so nothing below needs nix, docker, a terminal or a network,
and no test has to skip itself when the machine happens to lack a tool. A step that
silently skipped is a step that stopped guarding anything.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence

import pytest

from git_cleanup_common import CommandResult
from setup_devenv.actions import (
    AppendLine,
    Context,
    Machine,
    Run,
    Session,
    StoreGitLabToken,
    WriteFile,
)
from setup_devenv.caches import BLOCK_BEGIN, CACHES, apply_block, render_block
from setup_devenv.gitlab import Failure, GitLabError, GitLabUser, SshKey
from setup_devenv.steps import (
    PROBED_TOOLS,
    STEPS,
    State,
    Step,
    assess_allow,
    assess_caches,
    assess_daemon,
    assess_devenv,
    assess_direnv,
    assess_docker,
    assess_git_identity,
    assess_gitlab_token,
    assess_nix,
    assess_selinux,
    disable_selinux,
    effective_gaps,
    select,
)


class Invocation(NamedTuple):
    """One command the script tried to run, and how."""

    argv: Sequence[str]
    cwd: Optional[Path]
    env: Optional[dict]


class Written(NamedTuple):
    """One file the script tried to write, and how."""

    path: Path
    content: str
    mode: int
    sudo: bool


class FakeRunner:
    """Records what would have run and replays canned results."""

    def __init__(self, results: Optional[Dict[str, CommandResult]] = None) -> None:
        self.results = results or {}
        self.ran: List[Invocation] = []
        self.written: List[Written] = []

    def run(
        self,
        argv: Sequence[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
    ) -> CommandResult:
        """Return the canned result for this command, or a success."""
        self.ran.append(Invocation(argv, cwd, env))
        return self.results.get(" ".join(argv), CommandResult(0, "", ""))

    def run_visible(self, argv: Sequence[str], cwd: Optional[Path] = None) -> int:
        """Record and succeed."""
        self.ran.append(Invocation(argv, cwd, None))
        return 0

    def write_file(self, path: Path, content: str, mode: int = 0o644) -> bool:
        """Record and succeed."""
        self.written.append(Written(path, content, mode, sudo=False))
        return True

    def write_root_file(self, path: Path, content: str, mode: int = 0o644) -> bool:
        """Record and succeed."""
        self.written.append(Written(path, content, mode, sudo=True))
        return True


class FakeConsole:
    """Collects output and replays a scripted answer."""

    def __init__(self, secret: Optional[str] = None) -> None:
        self.secret = secret
        self.said: List[str] = []

    def say(self, line: str, /) -> None:
        """Record a line."""
        self.said.append(line)

    def ask_secret(self, question: str, /) -> Optional[str]:
        """Hand back whatever this console was built with."""
        self.said.append(question)
        return self.secret


class FakeGitLab:
    """A GitLab account that answers from memory, or raises."""

    def __init__(
        self,
        user: Optional[GitLabUser] = None,
        keys: Optional[List[SshKey]] = None,
        error: Optional[GitLabError] = None,
    ) -> None:
        self.user = user or GitLabUser("Ada Lovelace", "ada", "ada@example.com")
        self.keys = keys or []
        self.error = error
        self.uploaded: List[SshKey] = []
        self.tokens: List[str] = []

    def __call__(self, token: str) -> "FakeGitLab":
        """Stand in for the client factory, remembering the token it was given."""
        self.tokens.append(token)
        return self

    def fetch_user(self) -> GitLabUser:
        """The account, or the scripted failure."""
        if self.error is not None:
            raise self.error
        return self.user

    def list_ssh_keys(self) -> List[SshKey]:
        """The registered keys, or the scripted failure."""
        if self.error is not None:
            raise self.error
        return self.keys

    def upload_ssh_key(self, title: str, public_key: str) -> SshKey:
        """Register a key, or raise the scripted failure."""
        if self.error is not None:
            raise self.error
        key = SshKey(len(self.keys) + 1, title, public_key)
        self.keys.append(key)
        self.uploaded.append(key)
        return key


def make_machine(**overrides: object) -> Machine:
    """A machine with every fact stated, including what is on PATH."""
    fields: Dict[str, object] = {
        "is_nixos": False,
        "has_systemd": True,
        "home": Path("/home/dev"),
        "user": "dev",
        "shell": "bash",
        "tools": frozenset(PROBED_TOOLS),
    }
    fields.update(overrides)
    return Machine(**fields)  # type: ignore[arg-type]


def make_context(**overrides: object) -> Context:
    """A context with every collaborator faked, overridable per test."""
    machine_keys = ("is_nixos", "has_systemd", "home", "user", "shell", "tools")
    machine_fields = {
        key: overrides.pop(key) for key in list(overrides) if key in machine_keys
    }
    defaults: Dict[str, object] = {
        "repo": Path("/repo"),
        "runner": FakeRunner(),
        "console": FakeConsole(),
        "make_gitlab": FakeGitLab(),
    }
    defaults.update(overrides)
    return Context(machine=make_machine(**machine_fields), **defaults)  # type: ignore[arg-type]


#
# Steps
#


def test_caches_on_nixos_is_manual_and_does_nothing() -> None:
    """/etc/nix/nix.conf there is generated; writing it would be undone."""
    assessment = assess_caches(make_context(is_nixos=True), Session())

    assert assessment.state is State.MANUAL
    assert not assessment.actions
    assert assessment.instructions is not None
    assert "nix.settings" in assessment.instructions


def test_caches_writes_the_block_as_root_when_nix_conf_lacks_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A nix.conf without the managed block is told exactly what will change."""
    conf = tmp_path / "nix.conf"
    conf.write_text("sandbox = true\n")
    monkeypatch.setattr("setup_devenv.steps.NIX_CONF", conf)

    assessment = assess_caches(make_context(), Session())
    assert assessment.state is State.NEEDED

    (action,) = assessment.actions
    assert isinstance(action, WriteFile)
    assert action.path == conf
    assert "sandbox = true" in action.content
    assert BLOCK_BEGIN in action.content
    # Root-owned and world-readable: the daemon reads it, so it has to be both.
    assert action.sudo
    assert action.mode == 0o644
    # And it is the write that makes the daemon restart worth offering.
    assert action.is_nix_conf


def test_caches_is_satisfied_once_the_block_is_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second run asks nothing."""
    conf = tmp_path / "nix.conf"
    conf.write_text(apply_block("sandbox = true\n", render_block()))
    monkeypatch.setattr("setup_devenv.steps.NIX_CONF", conf)

    assert assess_caches(make_context(), Session()).state is State.SATISFIED


def test_nix_is_satisfied_on_nixos() -> None:
    """NixOS always has nix; offering to install it would be nonsense."""
    assert assess_nix(make_context(is_nixos=True), Session()).state is State.SATISFIED


def test_daemon_is_satisfied_when_nothing_changed() -> None:
    """No restart is offered when the configuration was not touched."""
    assert assess_daemon(make_context(), Session()).state is State.SATISFIED


def test_daemon_is_needed_after_a_cache_write() -> None:
    """The daemon reads nix.conf at startup, so the restart is the payoff."""
    assessment = assess_daemon(make_context(), Session(nix_conf_changed=True))

    assert assessment.state is State.NEEDED
    assert Run(("sudo", "systemctl", "restart", "nix-daemon.service")) in list(
        assessment.actions
    )


def test_daemon_shows_its_sudo_command_under_dry_run() -> None:
    """--dry-run exists to reveal the privileged commands, not to hide them."""
    session = Session(dry_run=True, nix_conf_changed=True)
    assert assess_daemon(make_context(), session).state is State.NEEDED


def test_daemon_without_systemd_is_manual() -> None:
    """A non-systemd machine is told rather than handed a command that fails."""
    ctx = make_context(tools=frozenset())
    assert assess_daemon(ctx, Session(nix_conf_changed=True)).state is State.MANUAL


def test_docker_permission_denied_offers_the_group_change() -> None:
    """The common case: docker installed, account not in the group."""
    runner = FakeRunner(
        {
            "docker info": CommandResult(
                1, "", "permission denied on /var/run/docker.sock"
            )
        }
    )
    assessment = assess_docker(make_context(runner=runner), Session())

    assert assessment.state is State.NEEDED
    assert Run(("sudo", "gpasswd", "--add", "dev", "docker")) in list(
        assessment.actions
    )


def test_docker_absent_is_manual_rather_than_fatal() -> None:
    """A box that will get docker later can still have its caches fixed."""
    ctx = make_context(tools=frozenset(PROBED_TOOLS) - {"docker"})
    assert assess_docker(ctx, Session()).state is State.MANUAL


def test_direnv_with_unknown_shell_is_manual() -> None:
    """Guessing an rc file for an unknown shell would edit the wrong file."""
    assessment = assess_direnv(make_context(shell="nushell"), Session())
    assert assessment.state is State.MANUAL


def test_direnv_appends_the_hook_to_the_right_rc_file(tmp_path: Path) -> None:
    """The exact line and the exact file are shown before anything is written."""
    assessment = assess_direnv(make_context(home=tmp_path), Session())

    assert assessment.state is State.NEEDED
    (action,) = assessment.actions
    assert isinstance(action, AppendLine)
    assert action.path == tmp_path / ".bashrc"
    assert action.line == 'eval "$(direnv hook bash)"'


def test_verify_reports_every_missing_cache() -> None:
    """The gap list is what tells an operator which half of the fix is missing."""
    runner = FakeRunner(
        {
            "nix config show substituters": CommandResult(
                0, "https://cache.nixos.org\n", ""
            ),
            "nix config show trusted-public-keys": CommandResult(0, "", ""),
        }
    )
    gaps = effective_gaps(make_context(runner=runner))

    assert gaps is not None
    assert set(gaps) == {cache.url for cache in CACHES}


def test_verify_flags_a_cache_present_without_its_key() -> None:
    """A substituter whose key is missing yields unusable, unsigned paths."""
    urls = " ".join(cache.url for cache in CACHES)
    runner = FakeRunner(
        {
            "nix config show substituters": CommandResult(0, urls, ""),
            "nix config show trusted-public-keys": CommandResult(
                0, CACHES[0].public_key, ""
            ),
        }
    )
    gaps = effective_gaps(make_context(runner=runner))

    assert gaps == [f"{cache.url} (key)" for cache in CACHES[1:]]


def test_verify_asks_the_daemon_with_nix_config_cleared() -> None:
    """Inside the devenv shell NIX_CONFIG already names every cache.

    Leaving it set would make this report success whatever /etc/nix/nix.conf says -- it
    would measure the thing being verified.
    """
    runner = FakeRunner()
    effective_gaps(make_context(runner=runner))

    assert runner.ran
    assert all(call.env == {"NIX_CONFIG": ""} for call in runner.ran)


def test_verify_returns_none_when_nix_cannot_be_read() -> None:
    """An unreadable configuration is reported as unknown, not as success."""
    runner = FakeRunner({"nix config show substituters": CommandResult(1, "", "boom")})
    assert effective_gaps(make_context(runner=runner)) is None


def test_allow_is_satisfied_when_direnv_already_trusts_the_repo() -> None:
    """Re-running does not re-ask for a checkout that is already allowed."""
    runner = FakeRunner(
        {"direnv status": CommandResult(0, "Found RC allowed true\n", "")}
    )
    assessment = assess_allow(make_context(runner=runner), Session())
    assert assessment.state is State.SATISFIED


def test_devenv_step_takes_no_machine_facts_but_path() -> None:
    """It reads the tool set alone, so NixOS makes no difference to it.

    Comparing two assessments is also the only check that `Assessment` and every
    `Action` under it stay comparable values rather than growing a closure.
    """
    assert assess_devenv(make_context(), Session()) == assess_devenv(
        make_context(is_nixos=True), Session()
    )


#
# SELinux
#


def test_selinux_absent_is_satisfied_not_a_demand_for_sudo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Debian, Ubuntu and Arch have no /etc/selinux/config at all.

    Treating "no such file" as "not disabled" asked for sudo to edit a file that is not
    there, and made declining fatal on every one of those machines.
    """
    monkeypatch.setattr("setup_devenv.steps.SELINUX_CONF", tmp_path / "nothing-here")
    assert assess_selinux(make_context(), Session()).state is State.SATISFIED


def test_selinux_enforcing_is_rewritten_without_losing_the_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file explains the other modes; only the setting line may change."""
    conf = tmp_path / "config"
    conf.write_text(
        "# enforcing - SELinux security policy is enforced.\n"
        "SELINUX=enforcing\n"
        "SELINUXTYPE=targeted\n"
    )
    monkeypatch.setattr("setup_devenv.steps.SELINUX_CONF", conf)

    assessment = assess_selinux(make_context(), Session())
    assert assessment.state is State.NEEDED
    assert assessment.required

    write = assessment.actions[0]
    assert isinstance(write, WriteFile)
    assert "SELINUX=disabled" in write.content
    assert "SELINUXTYPE=targeted" in write.content
    assert "# enforcing - SELinux security policy is enforced." in write.content
    assert Run(("sudo", "setenforce", "0")) in list(assessment.actions)


def test_selinux_already_disabled_is_satisfied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second run asks nothing."""
    conf = tmp_path / "config"
    conf.write_text("SELINUX=disabled\n")
    monkeypatch.setattr("setup_devenv.steps.SELINUX_CONF", conf)

    assert assess_selinux(make_context(), Session()).state is State.SATISFIED


def test_disable_selinux_rewrites_every_setting_line() -> None:
    """Both spellings a config can carry end up disabled."""
    assert "SELINUX=disabled" in disable_selinux("SELINUX=permissive\n")
    assert "SELINUX=disabled" in disable_selinux("SELINUX=enforcing")


#
# The GitLab token
#


def test_gitlab_token_is_satisfied_when_one_is_already_stored(tmp_path: Path) -> None:
    """Re-running does not ask for a token the checkout already has."""
    (tmp_path / "devenv.local.nix").write_text(
        '{ ... }: { env.GITLAB_TOKEN = "glpat-stored"; }\n'
    )
    ctx = make_context(repo=tmp_path)
    assert assess_gitlab_token(ctx, Session()).state is State.SATISFIED


def test_gitlab_token_refuses_to_overwrite_other_local_settings(
    tmp_path: Path,
) -> None:
    """`cicd-mode-enter` and CI both write this file.

    Rewriting one that holds anything else would throw their settings away, so the step
    hands the edit back instead.
    """
    local = tmp_path / "devenv.local.nix"
    local.write_text("{ env.cicd = true; }\n")
    assessment = assess_gitlab_token(make_context(repo=tmp_path), Session())

    assert assessment.state is State.MANUAL
    assert local.read_text() == "{ env.cicd = true; }\n"
    assert assessment.instructions


def test_gitlab_token_writes_it_at_0600_and_never_shows_it(tmp_path: Path) -> None:
    """A token at the ambient umask is world-readable, and so is a printed one."""
    assessment = assess_gitlab_token(make_context(repo=tmp_path), Session())
    assert assessment.state is State.NEEDED
    assert assessment.required

    (action,) = assessment.actions
    assert isinstance(action, StoreGitLabToken)
    assert action.path == tmp_path / "devenv.local.nix"
    # Nothing a token could hide in: it does not exist yet at describe() time.
    assert "0600" in action.describe()


def test_gitlab_token_can_be_skipped() -> None:
    """--skip-gitlab-token is the documented way past a required step."""
    session = Session(skip_gitlab_token=True)
    assert assess_gitlab_token(make_context(), session).state is State.SATISFIED


#
# The git identity
#


def test_git_identity_shows_the_literal_commands(tmp_path: Path) -> None:
    """The name and email are known before the prompt, so both are previewable."""
    (tmp_path / "devenv.local.nix").write_text(
        '{ ... }: { env.GITLAB_TOKEN = "glpat-stored"; }\n'
    )
    gitlab = FakeGitLab(GitLabUser("Ada Lovelace", "ada", "ada@example.com"))
    ctx = make_context(repo=tmp_path, make_gitlab=gitlab)

    assessment = assess_git_identity(ctx, Session())
    assert assessment.state is State.NEEDED
    assert Run(("git", "config", "--global", "user.name", "Ada Lovelace")) in list(
        assessment.actions
    )
    assert gitlab.tokens == ["glpat-stored"]


def test_git_identity_asks_nothing_under_dry_run(tmp_path: Path) -> None:
    """A dry run opens no socket, so it cannot know the account's name."""
    (tmp_path / "devenv.local.nix").write_text(
        '{ ... }: { env.GITLAB_TOKEN = "glpat-stored"; }\n'
    )
    gitlab = FakeGitLab()
    ctx = make_context(repo=tmp_path, make_gitlab=gitlab)

    assessment = assess_git_identity(ctx, Session(dry_run=True))
    assert assessment.state is State.MANUAL
    assert not gitlab.tokens


def test_git_identity_reports_a_rejected_token_as_such(tmp_path: Path) -> None:
    """A 401 used to be reported as a GitLab profile missing its name."""
    (tmp_path / "devenv.local.nix").write_text(
        '{ ... }: { env.GITLAB_TOKEN = "glpat-stale"; }\n'
    )
    gitlab = FakeGitLab(
        error=GitLabError(Failure.AUTH, "GitLab rejected the token: 401", 401)
    )
    ctx = make_context(repo=tmp_path, make_gitlab=gitlab)

    assessment = assess_git_identity(ctx, Session())
    assert assessment.state is State.MANUAL
    assert "rejected the token" in assessment.detail


def test_git_identity_without_a_token_points_at_the_token_step() -> None:
    """--only git-identity on a fresh checkout says which step to run first."""
    assessment = assess_git_identity(make_context(), Session())
    assert assessment.state is State.MANUAL
    assert assessment.instructions is not None
    assert "gitlab-token" in assessment.instructions


#
# Step selection
#


def test_select_defaults_to_every_step_in_order() -> None:
    """No flags means the documented order, unchanged."""
    names = [step.name for step in STEPS]
    assert [step.name for step in select(STEPS, [], [])] == names


def test_select_only_keeps_just_that_step() -> None:
    """--only nix-caches is how somebody applies just the fix."""
    assert [step.name for step in select(STEPS, ["nix-caches"], [])] == ["nix-caches"]


def test_select_skip_removes_it() -> None:
    """--skip verify, for a machine that already passed checks."""
    assert "verify" not in [step.name for step in select(STEPS, [], ["verify"])]


def test_select_rejects_an_unknown_step() -> None:
    """A typo names a step that silently does nothing otherwise."""
    with pytest.raises(SystemExit) as excinfo:
        select(STEPS, ["cashes"], [])
    assert "cashes" in str(excinfo.value)


def test_every_step_has_a_why() -> None:
    """The prompt prints it, so an empty one leaves a bare command on screen."""
    for step in STEPS:
        assert isinstance(step, Step)
        assert step.why
