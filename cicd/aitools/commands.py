import argparse
import logging

from . import config
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


def build_parser() -> tuple[argparse.ArgumentParser, list[str]]:
    """Build the argument parser for aitools.

    Returns the parser and the list of registered subcommand names.
    """
    parser = argparse.ArgumentParser(
        description="Loom AI developer tools.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Non-interactive mode: skip all prompts and run Claude with auto-accept",
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
        help="Implement a GitLab issue using Claude in agentic mode",
    )
    implement_parser.add_argument(
        "issue_number",
        help="GitLab issue URL (https://.../issues/123 or .../work_items/123) or bare issue ID",
    )
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
    mr_review_parser.set_defaults(func=cmd_mr_review)

    # mr-fix subcommand
    mr_fix_parser = subparsers.add_parser(
        "mr-fix",
        help="Address unresolved MR review comments using Claude in agentic mode",
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
        help="Diagnose a CI/CD job failure using Claude in agentic mode",
    )
    diagnose_parser.add_argument(
        "job",
        help="GitLab job URL (e.g. https://gitlab.com/group/project/-/jobs/123) or bare job ID",
    )
    diagnose_parser.set_defaults(func=cmd_job_diagnose)

    # mr-watch subcommand
    mr_watch_parser = subparsers.add_parser(
        "mr-watch",
        help="Watch an MR pipeline; auto-fix CI failures using Claude",
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
        help="Update a GitLab issue description interactively using Claude",
    )
    issue_update_parser.add_argument(
        "issue",
        help="GitLab issue URL (https://.../issues/123) or bare issue ID",
    )
    issue_update_parser.set_defaults(func=cmd_issue_update)

    # milestone-implement subcommand
    milestone_parser = subparsers.add_parser(
        "milestone-implement",
        help="Implement all open issues in a GitLab milestone",
    )
    milestone_parser.add_argument(
        "milestone",
        help="GitLab milestone URL (https://.../milestones/123) or bare milestone ID",
    )
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
    config.AUTO_MODE = args.auto
    args.func(args)
