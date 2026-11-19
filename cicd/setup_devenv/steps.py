"""What each setup step concludes, and what it would do about it.

A `Step` splits in two, and the split is what makes the script's promise keepable.

`assess` **reads local state only** -- the filesystem, `git config`, what is on PATH. It
never prompts and never writes. Everything that changes the machine is an `Action` (see
`actions.py`), which can `describe()` itself before it is consented to and `perform()`
itself afterwards. `--dry-run` runs every assessment and no action.

There is one carve-out, and it is deliberate: a step may make a **read-only** GitLab
call while assessing, when a token is **already stored locally**, because "is this key
already on the account" and "what is this account called" have no local answer. Those
calls are skipped under `--dry-run`, so a dry run still opens no socket, asks for
nothing and writes nothing.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from setup_devenv.actions import (
    Action,
    AppendLine,
    Context,
    MakeDirectory,
    Run,
    Session,
    SourceNixProfile,
    StoreGitLabToken,
    UploadSshKey,
    WriteFile,
    holds_only_a_token,
    read_text,
)
from setup_devenv.caches import (
    BLOCK_BEGIN,
    CACHES,
    NIX_CONF,
    apply_block,
    nixos_snippet,
    render_block,
)
from setup_devenv.gitlab import GitLabError, fingerprint_of

SELINUX_CONF = Path("/etc/selinux/config")
NIX_PROFILE = Path("/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh")

# The channel devenv is installed from, as in Documentation/devenv-setup.md.
DEVENV_NIXPKGS = "https://github.com/NixOS/nixpkgs/tarball/nixos-26.05"

NIX_INSTALL_URL = "https://nixos.org/nix/install"
DOCKER_INSTALL_DOCS = "https://docs.docker.com/engine/install/"
DIRENV_HOOK_DOCS = "https://direnv.net/docs/hook.html"
GITLAB_TOKEN_DOCS = "https://gitlab.com/-/user_settings/personal_access_tokens"
GITLAB_PROFILE_DOCS = "https://gitlab.com/-/profile"

# Shell -> (rc file, the line that hooks direnv into it).
DIRENV_HOOKS = {
    "bash": (".bashrc", 'eval "$(direnv hook bash)"'),
    "zsh": (".zshrc", 'eval "$(direnv hook zsh)"'),
    "fish": (".config/fish/config.fish", "direnv hook fish | source"),
}

# Every executable any step asks about, probed once at startup: what a step can see
# is then a fact of the Machine rather than a call the tests cannot intercept.
PROBED_TOOLS: Tuple[str, ...] = (
    "devenv",
    "direnv",
    "docker",
    "git",
    "nix",
    "ssh-keygen",
    "systemctl",
)

SSH_KEY_DIR = ".ssh"
SSH_KEY_NAME = "loom_gitlab"

# Nothing here needs 3.9 to *import*, so the check belongs at the start of a run
# rather than at module scope, where it would have to sit after the imports anyway:
# `from __future__ import annotations` must be a file's first statement.
MINIMUM_PYTHON = (3, 9)


def selinux_mode(current: str) -> str:
    """The mode `/etc/selinux/config` selects, lowercased, or the empty string."""
    for line in current.splitlines():
        stripped = line.strip()
        if stripped.startswith("SELINUX="):
            return stripped.split("=", 1)[1].strip().lower()
    return ""


def disable_selinux(current: str) -> str:
    """`current`, with the mode set to disabled.

    Rewritten line by line rather than by a substitution over the whole file, so the
    comments explaining the other modes survive.
    """
    lines = [
        "SELINUX=disabled" if line.strip().startswith("SELINUX=") else line
        for line in current.splitlines()
    ]
    return "\n".join(lines) + "\n"


#
# Steps
#


class State(Enum):
    """What a step found when it looked."""

    SATISFIED = "satisfied"
    NEEDED = "needed"
    MANUAL = "manual"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Assessment:
    """What a step decided, and what it would do about it."""

    state: State
    detail: str
    actions: Sequence[Action] = field(default_factory=tuple)
    # Shown verbatim before the prompt, for a step whose effect is a file's
    # contents rather than the command that puts them there.
    preview: Optional[str] = None
    # For MANUAL and BLOCKED: what the operator has to do by hand.
    instructions: Optional[str] = None
    # If True, declining the step counts as a failure and stops the run.
    required: bool = False

    def __post_init__(self) -> None:
        """A step that hands the work back has to say how to do it."""
        if self.state in (State.MANUAL, State.BLOCKED) and not self.instructions:
            raise ValueError(
                f"a {self.state.value} assessment needs instructions: {self.detail!r}"
            )


@dataclass(frozen=True)
class Step:
    """One named unit of setup."""

    name: str
    why: str
    emoji: str
    assess: Callable[[Context, Session], Assessment]


def assess_gitlab_token(ctx: Context, session: Session) -> Assessment:
    """The GitLab token this checkout's tooling reads out of devenv.local.nix."""
    if ctx.stored_token():
        return Assessment(State.SATISFIED, f"{ctx.devenv_local.name} holds a token")
    if session.skip_gitlab_token:
        return Assessment(State.SATISFIED, "skipped (--skip-gitlab-token)")

    existing = read_text(ctx.devenv_local)
    if existing and not holds_only_a_token(existing):
        # cicd-mode-enter and .gitlab-ci.yml both write this file; rewriting one
        # that holds anything else would throw their settings away.
        return Assessment(
            State.MANUAL,
            f"{ctx.devenv_local} holds other settings, so it is left alone",
            instructions=(
                f"Create a token with the `api` scope at\n{GITLAB_TOKEN_DOCS}\n"
                f"add it to {ctx.devenv_local} as\n\n"
                '    env.GITLAB_TOKEN = "glpat-...";\n\n'
                f"and then run `chmod 600 {ctx.devenv_local}`."
            ),
        )

    return Assessment(
        State.NEEDED,
        "aitools, up.sh's online probe and the ssh-key step all read this token",
        actions=(StoreGitLabToken(ctx.devenv_local),),
        required=True,
    )


def assess_git_identity(ctx: Context, session: Session) -> Assessment:
    """Git user.name and user.email, taken from the GitLab account."""
    token = ctx.stored_token()
    if token is None:
        return Assessment(
            State.MANUAL,
            "no GitLab token is stored yet",
            instructions="Run the `gitlab-token` step first.",
        )
    if session.dry_run:
        return Assessment(
            State.MANUAL,
            "would ask gitlab.com who you are, which a dry run does not do",
            instructions="Run without --dry-run to see the exact git commands.",
        )

    try:
        user = ctx.make_gitlab(token).fetch_user()
    except GitLabError as error:
        return Assessment(
            State.MANUAL,
            error.detail,
            instructions="Fix the token or the network, then run this step again.",
        )

    if not user.name or not user.email:
        return Assessment(
            State.MANUAL,
            "the GitLab account has no name or no public email",
            instructions=(
                f"Fill both in at {GITLAB_PROFILE_DOCS}, then run this step again."
            ),
        )

    current_name = ctx.runner.run(["git", "config", "--global", "user.name"]).out
    current_email = ctx.runner.run(["git", "config", "--global", "user.email"]).out
    if (current_name, current_email) == (user.name, user.email):
        return Assessment(
            State.SATISFIED, f"git already commits as {user.name} <{user.email}>"
        )

    return Assessment(
        State.NEEDED,
        f"GitLab knows you as {user.name} <{user.email}>",
        actions=(
            Run(("git", "config", "--global", "user.name", user.name)),
            Run(("git", "config", "--global", "user.email", user.email)),
        ),
    )


def assess_ssh_key(ctx: Context, session: Session) -> Assessment:
    """An ssh key for this checkout, registered with GitLab."""
    token = ctx.stored_token()
    if token is None:
        return Assessment(
            State.MANUAL,
            "no GitLab token is stored yet",
            instructions="Run the `gitlab-token` step first.",
        )
    if not ctx.machine.has("ssh-keygen"):
        return Assessment(
            State.MANUAL,
            "ssh-keygen is not installed",
            instructions="Install openssh-client, then run this step again.",
        )
    if session.dry_run:
        return Assessment(
            State.MANUAL,
            "would ask gitlab.com which keys are registered",
            instructions="Run without --dry-run to see what this would do.",
        )

    key_dir = ctx.repo / SSH_KEY_DIR
    private_key = key_dir / SSH_KEY_NAME
    public_key = key_dir / f"{SSH_KEY_NAME}.pub"
    have_key = private_key.exists() and public_key.exists()

    if have_key:
        local = fingerprint_of(read_text(public_key))
        try:
            registered = ctx.make_gitlab(token).list_ssh_keys()
        except GitLabError as error:
            return Assessment(
                State.MANUAL,
                error.detail,
                instructions="Fix the token or the network, then try again.",
            )
        if any(key.fingerprint == local for key in registered):
            return Assessment(State.SATISFIED, f"{local} is already on the account")

    return Assessment(
        State.NEEDED,
        "git over ssh, without a password prompt per push",
        actions=ssh_key_actions(ctx, private_key, public_key, have_key),
    )


def ssh_key_actions(
    ctx: Context, private_key: Path, public_key: Path, have_key: bool
) -> Tuple[Action, ...]:
    """Everything the ssh-key step would do, in order."""
    title = f"loom-dev@{platform.node() or 'loom'}"
    actions: List[Action] = []
    if not private_key.parent.is_dir():
        actions.append(MakeDirectory(private_key.parent, 0o700))
    if not have_key:
        # ssh-keygen writes 0600 and 0644 itself, so no chmod follows it.
        actions.append(
            Run(
                (
                    "ssh-keygen",
                    "-t",
                    "ed25519",
                    "-f",
                    str(private_key),
                    "-N",
                    "",
                    "-C",
                    title,
                )
            )
        )
    actions.append(UploadSshKey(title, public_key))
    # Repository-local, and deliberately without `-F /dev/null`: overriding which
    # identity git offers is the point, discarding the whole ssh config is not.
    actions.append(Run(("git", "config", "core.sshCommand", f"ssh -i {private_key}")))
    remote = ctx.runner.run(["git", "remote", "get-url", "origin"], cwd=ctx.repo)
    if remote.ok and remote.out:
        actions.append(Run(("git", "ls-remote", remote.out)))
    return tuple(actions)


def assess_selinux(_ctx: Context, _session: Session) -> Assessment:
    """SELinux, which has to be off for nix and docker to behave here."""
    if not SELINUX_CONF.exists():
        return Assessment(State.SATISFIED, "SELinux is not configured on this system")

    current = read_text(SELINUX_CONF)
    mode = selinux_mode(current)
    if mode == "disabled":
        return Assessment(State.SATISFIED, "SELinux is already disabled")

    return Assessment(
        State.NEEDED,
        f"SELinux is {(mode or 'unset').upper()}. The file takes effect at the next "
        "reboot, so setenforce covers this boot as well",
        actions=(
            WriteFile(SELINUX_CONF, disable_selinux(current), 0o644, sudo=True),
            Run(("sudo", "setenforce", "0")),
        ),
        required=True,
    )


def assess_nix(ctx: Context, _session: Session) -> Assessment:
    """Nix itself."""
    if ctx.machine.is_nixos:
        return Assessment(State.SATISFIED, "NixOS ships nix")
    if ctx.machine.has("nix"):
        return Assessment(State.SATISFIED, "nix is on PATH")
    return Assessment(
        State.NEEDED,
        "the installer needs root and sets up the multi-user daemon.\n"
        "  On Fedora, comment out the first two lines of\n"
        "  /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh afterwards.",
        actions=(
            # Process substitution is genuinely a shell feature, and this is the
            # line nixos.org documents. It is the only shell this script runs.
            Run(("bash", "-c", f"sh <(curl --location {NIX_INSTALL_URL}) --daemon")),
            SourceNixProfile(NIX_PROFILE),
        ),
    )


def assess_caches(ctx: Context, _session: Session) -> Assessment:
    """The binary caches -- the reason this script exists."""
    block = render_block()

    if ctx.machine.is_nixos:
        # /etc/nix/nix.conf on NixOS is a symlink into the store, regenerated by
        # every nixos-rebuild. Writing it would appear to work and then vanish.
        return Assessment(
            State.MANUAL,
            "NixOS generates /etc/nix/nix.conf, so it cannot be edited directly",
            instructions=(
                "Add this to your configuration.nix and run `nixos-rebuild "
                "switch`:\n\n" + nixos_snippet()
            ),
        )

    current = read_text(NIX_CONF)
    desired = apply_block(current, block)
    if desired == current:
        return Assessment(State.SATISFIED, f"{NIX_CONF} already names every cache")

    verb = "Updating" if BLOCK_BEGIN in current else "Adding"
    return Assessment(
        State.NEEDED,
        f"{verb} the managed block in {NIX_CONF}",
        preview=block,
        actions=(WriteFile(NIX_CONF, desired, 0o644, sudo=True, is_nix_conf=True),),
    )


def assess_daemon(ctx: Context, session: Session) -> Assessment:
    """Restarting the daemon, so the new nix.conf takes effect."""
    if not session.nix_conf_changed:
        return Assessment(State.SATISFIED, "nix.conf unchanged, nothing to reload")
    if not ctx.machine.has("systemctl"):
        return Assessment(
            State.MANUAL,
            "no systemctl found",
            instructions="Restart the nix daemon however this system manages it.",
        )
    return Assessment(
        State.NEEDED,
        "the daemon reads nix.conf at startup",
        actions=(Run(("sudo", "systemctl", "restart", "nix-daemon.service")),),
    )


def assess_devenv(ctx: Context, _session: Session) -> Assessment:
    """devenv."""
    if ctx.machine.has("devenv"):
        return Assessment(State.SATISFIED, "devenv is on PATH")
    return Assessment(
        State.NEEDED,
        "installs into your user profile, not system-wide",
        actions=(
            Run(("nix-env", "--install", "--attr", "devenv", "--file", DEVENV_NIXPKGS)),
        ),
    )


def assess_direnv(ctx: Context, _session: Session) -> Assessment:
    """Direnv, and its shell hook."""
    if not ctx.machine.has("direnv"):
        return Assessment(
            State.NEEDED,
            "loads the environment on cd, so no command needs a devenv prefix",
            actions=(Run(("nix-env", "--install", "--attr", "nixpkgs.direnv")),),
        )

    hook = DIRENV_HOOKS.get(ctx.machine.shell)
    if hook is None:
        return Assessment(
            State.MANUAL,
            f"unknown shell {ctx.machine.shell!r}",
            instructions=f"Hook direnv into your shell: {DIRENV_HOOK_DOCS}",
        )

    rc_name, line = hook
    rc_path = ctx.machine.home / rc_name
    if line in read_text(rc_path):
        return Assessment(State.SATISFIED, f"hooked into {rc_path}")

    # The line is shown in full before anything is written, because editing
    # somebody's shell profile is the one effect here a re-run cannot undo. It is
    # appended at the end so it runs after rvm, git-prompt and the rest.
    return Assessment(
        State.NEEDED,
        f"direnv does nothing until {rc_path} starts it",
        actions=(AppendLine(rc_path, line),),
    )


def assess_docker(ctx: Context, _session: Session) -> Assessment:
    """Docker, which `up` needs."""
    if not ctx.machine.has("docker"):
        return Assessment(
            State.MANUAL,
            "docker is not installed",
            instructions=(
                "Install docker-engine -- not docker-desktop -- following\n"
                f"{DOCKER_INSTALL_DOCS}, then run this script again."
            ),
        )

    probe = ctx.runner.run(["docker", "info"])
    if probe.ok:
        return Assessment(State.SATISFIED, "docker daemon is running")

    combined = f"{probe.stdout}{probe.stderr}".lower()
    if "permission denied" in combined or "dial unix" in combined:
        return Assessment(
            State.NEEDED,
            "your account cannot reach the docker socket "
            "(the group change needs a re-login to take effect)",
            actions=(Run(("sudo", "gpasswd", "--add", ctx.machine.user, "docker")),),
        )

    reason = probe.stderr.strip() or probe.stdout.strip() or "unknown error"
    return Assessment(
        State.MANUAL,
        f"`docker info` failed (exit {probe.returncode}): {reason}",
        instructions=(
            f"Start the docker daemon following {DOCKER_INSTALL_DOCS}, "
            "then run this script again."
        ),
    )


def assess_allow(ctx: Context, _session: Session) -> Assessment:
    """Trusting this checkout, so direnv will load it."""
    if not ctx.machine.has("direnv"):
        return Assessment(
            State.MANUAL,
            "direnv is not installed yet",
            instructions="Run the `direnv` step first.",
        )

    status = ctx.runner.run(["direnv", "status"], cwd=ctx.repo)
    # Newer direnv prints "Found RC allowed true"; older builds print "allowed 0".
    if "Found RC allowed true" in status.stdout or "allowed 0" in status.stdout:
        return Assessment(State.SATISFIED, "direnv already trusts this checkout")
    return Assessment(
        State.NEEDED,
        "direnv refuses to load an untrusted directory",
        actions=(Run(("direnv", "allow"), cwd=ctx.repo),),
    )


def assess_verify(ctx: Context, _session: Session) -> Assessment:
    """Proving the daemon really offers the caches.

    Deliberately asks the daemon with NIX_CONFIG emptied. Inside the devenv shell that
    variable already names every cache, so leaving it set would make this report success
    no matter what /etc/nix/nix.conf says -- it would be measuring the thing we are
    trying to verify.
    """
    if not ctx.machine.has("nix"):
        return Assessment(
            State.MANUAL,
            "nix is not installed yet",
            instructions="Run the `nix` step first, then open a new shell.",
        )

    missing = effective_gaps(ctx)
    if missing is None:
        return Assessment(
            State.MANUAL,
            "could not read the effective nix configuration",
            instructions="Run `nix config show substituters` and check by hand.",
        )
    if not missing:
        return Assessment(State.SATISFIED, "every cache and key is in effect")
    return Assessment(
        State.MANUAL,
        "the daemon does not offer: " + ", ".join(missing),
        instructions=(
            "Re-run the `nix-caches` step, then restart the nix-daemon. On NixOS, "
            "apply the configuration.nix snippet and `nixos-rebuild switch`."
        ),
    )


def effective_gaps(ctx: Context) -> Optional[List[str]]:
    """Caches or keys the daemon does not have.

    None when it cannot be read.
    """
    blank = {"NIX_CONFIG": ""}
    subs = ctx.runner.run(["nix", "config", "show", "substituters"], env=blank)
    keys = ctx.runner.run(["nix", "config", "show", "trusted-public-keys"], env=blank)
    if not subs.ok or not keys.ok:
        return None

    missing: List[str] = []
    for cache in CACHES:
        if cache.url not in subs.stdout:
            missing.append(cache.url)
        elif cache.public_key not in keys.stdout:
            missing.append(f"{cache.url} (key)")
    return missing


STEPS: Tuple[Step, ...] = (
    Step(
        "gitlab-token",
        "the token aitools, up.sh and the ssh-key step read",
        "🎫",
        assess_gitlab_token,
    ),
    Step(
        "git-identity",
        "commits attributed to your GitLab account",
        "🐙",
        assess_git_identity,
    ),
    Step("ssh-key", "git over ssh, with no password per push", "🔑", assess_ssh_key),
    Step(
        "selinux",
        "nix and docker misbehave while it is enforcing",
        "🛡️",
        assess_selinux,
    ),
    Step("nix", "the package manager everything else is built on", "❄️", assess_nix),
    Step(
        "nix-caches", "so builds are fetched instead of compiled", "⚡", assess_caches
    ),
    Step("nix-daemon", "picks up the cache configuration", "👻", assess_daemon),
    Step(
        "devenv", "provides the project's toolchain and commands", "🛠️", assess_devenv
    ),
    Step(
        "direnv",
        "loads the environment on cd, so no command needs a devenv prefix",
        "🔄",
        assess_direnv,
    ),
    Step("docker", "runs the cluster `up` deploys to", "🐳", assess_docker),
    Step("allow", "lets direnv load this checkout", "✅", assess_allow),
    Step("verify", "confirms the caches are actually reachable", "🔍", assess_verify),
)


def select(steps: Sequence[Step], only: List[str], skip: List[str]) -> List[Step]:
    """The steps to run, honouring --only and --skip."""
    names = [step.name for step in steps]
    unknown = (set(only) | set(skip)) - set(names)
    if unknown:
        raise SystemExit(
            f"unknown step(s): {', '.join(sorted(unknown))}. "
            f"Valid: {', '.join(names)}"
        )
    chosen = [step for step in steps if not only or step.name in only]
    return [step for step in chosen if step.name not in skip]
