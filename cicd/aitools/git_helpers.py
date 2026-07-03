import logging
import os

import git
from git import Repo

from .config import EXCLUDED_PATHSPECS, MAX_DIFF_CHARS
from .models import FileDiffMap

logger = logging.getLogger(__name__)


def get_branch_diff(repo: Repo, ref: str = "HEAD") -> str:
    """Return the diff of commits on the given ref relative to origin/main.

    Args:
        repo: The git repository.
        ref: The git ref to diff against origin/main. Pass "HEAD" for the currently
            checked-out branch (default), or "origin/<branch>" to review a branch that
            is not checked out locally.

    Uses the merge base so that commits in main that are not yet in this branch are
    excluded. Excludes lockfiles and generated files. Prepends a --stat summary.
    Truncates the diff body if it exceeds MAX_DIFF_CHARS.
    """
    repo.git.fetch("origin", "main")
    merge_base = repo.git.merge_base("origin/main", ref).strip()
    logger.debug("Merge base: %s", merge_base)

    stat = repo.git.diff(merge_base, ref, "--stat", "--", *EXCLUDED_PATHSPECS)
    diff = repo.git.diff(merge_base, ref, "--", *EXCLUDED_PATHSPECS)

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + (
            f"\n\n[Diff truncated at {MAX_DIFF_CHARS} characters."
            " See stat summary above for full file list.]"
        )
        logger.warning("Diff truncated to %d characters", MAX_DIFF_CHARS)

    result = f"Changed files:\n{stat}\n\nDiff:\n{diff}" if stat else f"Diff:\n{diff}"
    logger.debug("Branch diff retrieved: %d characters", len(result))
    return result


def get_per_file_diffs(repo: Repo) -> FileDiffMap:
    """Return per-file diffs for the current branch relative to origin/main.

    Uses the same merge-base logic and exclusions as get_branch_diff. Returns a
    FileDiffMap with the stat summary and a dict of file_path -> diff text.
    """
    repo.git.fetch("origin", "main")
    merge_base = repo.git.merge_base("origin/main", "HEAD").strip()
    logger.debug("Merge base for per-file diffs: %s", merge_base)

    stat = repo.git.diff(merge_base, "HEAD", "--stat", "--", *EXCLUDED_PATHSPECS)
    name_only = repo.git.diff(
        merge_base, "HEAD", "--name-only", "--", *EXCLUDED_PATHSPECS
    )

    files: dict[str, str] = {}
    for file_path in name_only.strip().splitlines():
        file_path = file_path.strip()
        if not file_path:
            continue
        try:
            file_diff = repo.git.diff(merge_base, "HEAD", "--", file_path)
        except git.exc.GitCommandError:
            logger.warning("Failed to get diff for file: %s", file_path)
            file_diff = ""
        files[file_path] = file_diff

    logger.debug("Per-file diffs retrieved for %d files", len(files))
    return FileDiffMap(stat=stat, files=files)


def load_mr_template(repo: Repo) -> str:
    """Load the MR template from the repository."""
    if not repo.working_dir:
        logger.warning("No working directory available (bare repo?)")
        return ""

    template_path = os.path.join(
        repo.working_dir, ".gitlab", "merge_request_templates", "Default.md"
    )
    try:
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("MR template not found at %s", template_path)
        return ""


def get_tag_diff(repo: Repo, from_tag: str, to_tag: str) -> str:
    """Return the diff between two tags, excluding lockfiles and generated files."""
    stat = repo.git.diff(from_tag, to_tag, "--stat", "--", *EXCLUDED_PATHSPECS)
    diff = repo.git.diff(from_tag, to_tag, "--", *EXCLUDED_PATHSPECS)

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + (
            f"\n\n[Diff truncated at {MAX_DIFF_CHARS} characters."
            " See stat summary above for full file list.]"
        )
        logger.warning("Diff truncated to %d characters", MAX_DIFF_CHARS)

    result = f"Changed files:\n{stat}\n\nDiff:\n{diff}" if stat else f"Diff:\n{diff}"
    logger.debug("Tag diff retrieved: %d characters", len(result))
    return result


def get_per_file_tag_diffs(repo: Repo, from_tag: str, to_tag: str) -> FileDiffMap:
    """Return per-file diffs between two tags, excluding lockfiles and generated
    files."""
    stat = repo.git.diff(from_tag, to_tag, "--stat", "--", *EXCLUDED_PATHSPECS)
    name_only = repo.git.diff(
        from_tag, to_tag, "--name-only", "--", *EXCLUDED_PATHSPECS
    )

    files: dict[str, str] = {}
    for file_path in name_only.strip().splitlines():
        file_path = file_path.strip()
        if not file_path:
            continue
        try:
            file_diff = repo.git.diff(from_tag, to_tag, "--", file_path)
        except git.exc.GitCommandError:
            logger.warning("Failed to get diff for file: %s", file_path)
            file_diff = ""
        files[file_path] = file_diff

    logger.debug("Per-file tag diffs retrieved for %d files", len(files))
    return FileDiffMap(stat=stat, files=files)


def fetch_and_sort_tags(repo: Repo) -> list[str]:
    """Fetch all remote tags and return them sorted by semver (newest first)."""
    repo.git.fetch("--tags", "--force")
    raw = repo.git.tag("--list").strip()
    if not raw:
        return []
    tags = [t.strip() for t in raw.split("\n") if t.strip()]

    def semver_key(tag: str) -> tuple[int, ...]:
        clean = tag.lstrip("v")
        try:
            return tuple(int(x) for x in clean.split("."))
        except ValueError:
            return (0, 0, 0)

    return sorted(tags, key=semver_key, reverse=True)
