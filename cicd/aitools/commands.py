import argparse
import logging

from . import config
from .autopilot import DEFAULT_AUTOPILOT_SETTINGS
from .cmd_implement import cmd_implement, cmd_milestone_implement
from .cmd_issue_update import cmd_issue_update
from .cmd_job_diagnose import cmd_job_diagnose
from .cmd_mr_create import cmd_mr_create
from .cmd_mr_describe import cmd_mr_describe
from .cmd_mr_fix import cmd_mr_fix
from .cmd_mr_review import cmd_mr_review
from .cmd_mr_update import cmd_mr_update
from .cmd_mr_watch import cmd_mr_watch
from .cmd_pipeline_retry import cmd_pipeline_retry
from .cmd_release import cmd_release

logger = logging.getLogger(__name__)


def cmd_completions(_args: argparse.Namespace) -> None:
    """Print bash completion script for aitools.

    Source with: source <(aitools completions)
    Or add to your bashrc: aitools completions > ~/.bash_completion.d/aitools
    """
    _, subcommand_names = build_parser()
    subcommands = " ".join(subcommand_names)
    print(f'complete -W "{subcommands}" aitools')


def _add_autopilot_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the caps that bound an autonomous run to a subcommand's parser."""
    parser.add_argument(
        "--max-fix-rounds",
        type=int,
        default=DEFAULT_AUTOPILOT_SETTINGS.limits.max_fix_rounds,
        help="How many times to let the AI fix a failing pipeline (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=DEFAULT_AUTOPILOT_SETTINGS.limits.overall_timeout_s // 60,
        help="How long one issue may take in total (default: %(default)s)",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip the AI review pass that comments on the MR and fixes its findings",
    )


def build_parser() -> tuple[argparse.ArgumentParser, list[str]]:
    """Build the argument parser for aitools.

    Returns the parser and the list of registered subcommand names.
    """
    parser = argparse.ArgumentParser(
        description="Loom AI developer tools.",
    )
    parser.add_argument(
        "--backend",
        choices=["claude", "opencode"],
        default="claude",
        help="Backend used by Loom AI tools (default: claude)",
    )
    parser.add_argument(
        "--model",
        default="none",
        help="provider/model to use by opencode",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Non-interactive mode: skip aitools' own prompts and run opencode "
        "with auto-accept (claude always runs in auto permission mode)",
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    # mr-create subcommand
    mr_create_parser = subparsers.add_parser(
        "mr-create",
        help="Create a branch, commit all changes, push, and open a draft MR",
    )
    mr_create_parser.add_argument(
        "type",
        choices=["feature", "bugfix"],
        help="Branch type prefix",
    )
    mr_create_parser.add_argument(
        "name",
        help="Branch name slug (e.g. 'my-feature' → feature/my-feature)",
    )
    mr_create_parser.set_defaults(func=cmd_mr_create)

    # mr-update subcommand
    mr_update_parser = subparsers.add_parser(
        "mr-update",
        help="Merge origin/main into the current branch, resolve conflicts, and push",
    )
    mr_update_parser.set_defaults(func=cmd_mr_update)

    # mr-describe subcommand
    mr_describe_parser = subparsers.add_parser(
        "mr-describe",
        help="Update GitLab MR title/description using AI",
    )
    mr_describe_parser.add_argument(
        "instructions",
        nargs="*",
        help="Additional instructions to append to the AI prompt",
    )
    mr_describe_parser.set_defaults(func=cmd_mr_describe)

    # implement subcommand
    implement_parser = subparsers.add_parser(
        "implement",
        help="Implement a GitLab issue autonomously, through to a green pipeline",
    )
    implement_parser.add_argument(
        "issue_number",
        help="GitLab issue URL (https://.../issues/123 or .../work_items/123) or bare issue ID",
    )
    _add_autopilot_arguments(implement_parser)
    implement_parser.set_defaults(func=cmd_implement)

    # mr-review subcommand
    mr_review_parser = subparsers.add_parser(
        "mr-review",
        help="Run a multi-agent AI review of the current MR and post findings as comments",
    )
    mr_review_parser.add_argument(
        "mr",
        nargs="?",
        help=(
            "GitLab MR URL (https://.../merge_requests/123) or bare MR IID. "
            "Omit to review the MR for the current branch."
        ),
    )
    mr_review_parser.add_argument(
        "--fix",
        action="store_true",
        help=("Automatically fix all findings instead of posting them as MR comments"),
    )
    mr_review_parser.set_defaults(func=cmd_mr_review)

    # mr-fix subcommand
    mr_fix_parser = subparsers.add_parser(
        "mr-fix",
        help="Address unresolved MR review comments using AI in agentic mode",
    )
    mr_fix_parser.add_argument(
        "mr",
        nargs="?",
        help=(
            "GitLab MR URL (https://.../merge_requests/123) or bare MR IID. "
            "Omit to fix the MR for the current branch."
        ),
    )
    mr_fix_parser.set_defaults(func=cmd_mr_fix)

    # completions subcommand
    completions_parser = subparsers.add_parser(
        "completions",
        help="Print bash completion script (source with: source <(aitools completions))",
    )
    completions_parser.set_defaults(func=cmd_completions)

    # job-diagnose subcommand
    diagnose_parser = subparsers.add_parser(
        "job-diagnose",
        help="Diagnose a CI/CD job failure using AI in agentic mode",
    )
    diagnose_parser.add_argument(
        "job",
        help="GitLab job URL (e.g. https://gitlab.com/group/project/-/jobs/123) or bare job ID",
    )
    diagnose_parser.set_defaults(func=cmd_job_diagnose)

    # mr-watch subcommand
    mr_watch_parser = subparsers.add_parser(
        "mr-watch",
        help="Watch an MR pipeline; auto-fix CI failures using AI",
    )
    mr_watch_parser.add_argument(
        "mr",
        nargs="?",
        help=(
            "GitLab MR URL (https://.../merge_requests/123) or bare MR IID. "
            "Omit to watch the MR for the current branch."
        ),
    )
    mr_watch_parser.add_argument(
        "--all",
        action="store_true",
        help="Watch all approved, auto-merge, or active-pipeline MRs (not just current branch)",
    )
    mr_watch_parser.set_defaults(func=cmd_mr_watch)

    # pipeline-retry subcommand
    pipeline_retry_parser = subparsers.add_parser(
        "pipeline-retry",
        help="Retry a GitLab pipeline by ID or URL",
    )
    pipeline_retry_parser.add_argument(
        "pipeline",
        help="GitLab pipeline URL (https://.../pipelines/123) or bare pipeline ID",
    )
    pipeline_retry_parser.set_defaults(func=cmd_pipeline_retry)

    # release subcommand
    release_parser = subparsers.add_parser(
        "release",
        help="Create a GitLab release with AI-generated release notes",
    )
    release_parser.set_defaults(func=cmd_release)

    # issue-update subcommand
    issue_update_parser = subparsers.add_parser(
        "issue-update",
        help="Update a GitLab issue description interactively using AI",
    )
    issue_update_parser.add_argument(
        "issue",
        help="GitLab issue URL (https://.../issues/123) or bare issue ID",
    )
    issue_update_parser.set_defaults(func=cmd_issue_update)

    # milestone-implement subcommand
    milestone_parser = subparsers.add_parser(
        "milestone-implement",
        help="Implement all open issues in a GitLab milestone, autonomously",
    )
    milestone_parser.add_argument(
        "milestone",
        help="GitLab milestone URL (https://.../milestones/123) or bare milestone ID",
    )
    milestone_parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="How many issues to implement at once, one tmux window each (default: 1)",
    )
    milestone_parser.add_argument(
        "--no-tmux",
        action="store_true",
        help="Run the issues in this process, one after another, instead of in tmux",
    )
    _add_autopilot_arguments(milestone_parser)
    milestone_parser.set_defaults(func=cmd_milestone_implement)

    return parser, list(subparsers.choices.keys())


def main() -> None:
    """Entry point for aitools."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s",
    )
    parser, _ = build_parser()
    args = parser.parse_args()

    if args.backend == "claude":
        if args.model != "none":
            parser.error("--model can only be set when --backend is set to opencode")
    elif args.backend == "opencode":
        config.BACKEND = args.backend
        if args.model != "none":
            provider_model = args.model.split("/")
            if len(provider_model) != 2:
                parser.error("--model argument needs to have the form provider/model")
            config.MODEL = args.model

    config.AUTO_MODE = args.auto

    if getattr(args, "parallel", 1) < 1:
        parser.error("--parallel must be at least 1")
    if getattr(args, "max_fix_rounds", 0) < 0:
        parser.error("--max-fix-rounds cannot be negative")
    if getattr(args, "timeout_minutes", 1) < 1:
        parser.error("--timeout-minutes must be at least 1")

    args.func(args)
