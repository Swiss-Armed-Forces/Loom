"""Tests for `cicd/setup_devenv.py`.

The script installs things, so what is tested here is everything it decides *before* it
does: how the managed nix.conf block is written and rewritten, what each step concludes
from a given machine, and that --only/--skip select what they say. Commands run through
an injected fake runner, so nothing below needs nix, docker or a terminal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

import pytest

from git_cleanup_common import CommandResult
from setup_devenv import (
    BLOCK_BEGIN,
    BLOCK_END,
    CACHES,
    STEPS,
    Context,
    Machine,
    State,
    Step,
    apply_block,
    assess_allow,
    assess_caches,
    assess_daemon,
    assess_devenv,
    assess_direnv,
    assess_docker,
    assess_nix,
    effective_gaps,
    nixos_snippet,
    render_block,
    select,
)


class Invocation(NamedTuple):
    """One command the script tried to run, and how."""

    argv: Sequence[str]
    cwd: Optional[Path]
    env: Optional[dict]


class FakeRunner:
    """Records what would have run and replays canned results."""

    def __init__(self, results: Optional[Dict[str, CommandResult]] = None) -> None:
        self.results = results or {}
        self.ran: List[Invocation] = []
        self.written: List[Tuple[Path, str]] = []

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

    def write_root_file(self, path: Path, content: str) -> int:
        """Record and succeed."""
        self.written.append((path, content))
        return 0


def make_context(**overrides: object) -> Context:
    """A context with every machine fact stated, overridable per test."""
    machine_fields = {
        "is_nixos": False,
        "has_systemd": True,
        "home": Path("/home/dev"),
        "user": "dev",
        "shell": "bash",
    }
    machine_fields.update(
        {key: overrides.pop(key) for key in list(overrides) if key in machine_fields}
    )
    defaults: Dict[str, object] = {
        "repo": Path("/repo"),
        "runner": FakeRunner(),
        "dry_run": False,
    }
    defaults.update(overrides)
    return Context(machine=Machine(**machine_fields), **defaults)  # type: ignore[arg-type]


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
# Steps
#


def test_caches_on_nixos_is_manual_and_writes_nothing() -> None:
    """/etc/nix/nix.conf there is generated; writing it would be undone."""
    ctx = make_context(is_nixos=True)
    assessment = assess_caches(ctx)

    assert assessment.state is State.MANUAL
    assert assessment.write is None
    assert assessment.instructions is not None
    assert "nix.settings" in assessment.instructions


def test_caches_needs_a_write_when_nix_conf_lacks_the_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A machine configured the old way is told what will change."""
    conf = tmp_path / "nix.conf"
    conf.write_text("sandbox = true\n")
    monkeypatch.setattr("setup_devenv.NIX_CONF", conf)

    assessment = assess_caches(make_context())
    assert assessment.state is State.NEEDED
    assert assessment.write is not None
    target, content = assessment.write
    assert target == conf
    assert "sandbox = true" in content
    assert BLOCK_BEGIN in content


def test_caches_is_satisfied_once_the_block_is_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second run asks nothing."""
    conf = tmp_path / "nix.conf"
    conf.write_text(apply_block("sandbox = true\n", render_block()))
    monkeypatch.setattr("setup_devenv.NIX_CONF", conf)

    assert assess_caches(make_context()).state is State.SATISFIED


def test_nix_is_satisfied_on_nixos() -> None:
    """NixOS always has nix; offering to install it would be nonsense."""
    assert assess_nix(make_context(is_nixos=True)).state is State.SATISFIED


def test_daemon_is_satisfied_when_nothing_changed() -> None:
    """No restart is offered when the configuration was not touched."""
    assert assess_daemon(make_context()).state is State.SATISFIED


def test_daemon_is_needed_after_a_cache_write() -> None:
    """The daemon reads nix.conf at startup, so the restart is the payoff."""
    ctx = make_context()
    ctx.nix_conf_changed = True
    assessment = assess_daemon(ctx)

    assert assessment.state is State.NEEDED
    assert ["sudo", "systemctl", "restart", "nix-daemon.service"] in [
        list(argv) for argv in assessment.argv
    ]


def test_daemon_without_systemd_is_manual() -> None:
    """A non-systemd machine is told rather than handed a command that fails."""
    ctx = make_context(has_systemd=False)
    ctx.nix_conf_changed = True
    assert assess_daemon(ctx).state is State.MANUAL


def test_docker_permission_denied_offers_the_group_change() -> None:
    """The common case: docker installed, account not in the group."""
    runner = FakeRunner(
        {
            "docker info": CommandResult(
                1, "", "permission denied on /var/run/docker.sock"
            )
        }
    )
    ctx = make_context(runner=runner)

    assessment = assess_docker(ctx)
    if assessment.state is State.MANUAL:
        pytest.skip("no docker binary on this machine to probe")
    assert assessment.state is State.NEEDED
    assert ["sudo", "gpasswd", "-a", "dev", "docker"] in [
        list(argv) for argv in assessment.argv
    ]


def test_direnv_with_unknown_shell_is_manual() -> None:
    """Guessing an rc file for an unknown shell would edit the wrong file."""
    assessment = assess_direnv(make_context(shell="nushell"))
    if assessment.state is State.NEEDED:
        pytest.skip("direnv is not installed on this machine")
    assert assessment.state is State.MANUAL


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
    assessment = assess_allow(make_context(runner=runner))
    if assessment.state is State.MANUAL:
        pytest.skip("direnv is not installed on this machine")
    assert assessment.state is State.SATISFIED


def test_devenv_step_takes_no_machine_facts() -> None:
    """It reads PATH alone, so it answers the same on any context."""
    assert assess_devenv(make_context()) == assess_devenv(make_context(is_nixos=True))


#
# Step selection
#


def step_names() -> List[str]:
    """Every step name, in order."""
    return [step.name for step in STEPS]


def test_select_defaults_to_every_step_in_order() -> None:
    """No flags means the documented order, unchanged."""
    assert [step.name for step in select(step_names(), [], [])] == step_names()


def test_select_only_keeps_just_that_step() -> None:
    """--only caches is how somebody applies just the fix."""
    assert [step.name for step in select(step_names(), ["caches"], [])] == ["caches"]


def test_select_skip_removes_it() -> None:
    """--skip docker, for a machine that will never run the cluster."""
    assert "docker" not in [step.name for step in select(step_names(), [], ["docker"])]


def test_select_rejects_an_unknown_step() -> None:
    """A typo names a step that silently does nothing otherwise."""
    with pytest.raises(SystemExit) as excinfo:
        select(step_names(), ["cashes"], [])
    assert "cashes" in str(excinfo.value)


def test_every_step_has_a_why() -> None:
    """The prompt prints it, so an empty one leaves a bare command on screen."""
    for step in STEPS:
        assert isinstance(step, Step)
        assert step.why


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
