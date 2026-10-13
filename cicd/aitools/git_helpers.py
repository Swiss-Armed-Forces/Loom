import logging
import os

import git
from git import Repo

from .config import EXCLUDED_PATHSPECS, MAX_DIFF_CHARS
from .models import DiffRange, FileDiffMap

logger = logging.getLogger(__name__)


def _merge_base_range(
    repo: Repo, ref: str, target_branch: str, behind: int
) -> DiffRange:
    """Resolve the diff range from a merge base, used when the branch cannot be merged.

    A branch that has merged its target in has more than one merge base once the target
    advances along a parallel line, and `git merge-base` returns an arbitrary one, so
    the resulting diff can replay work the target already carries. Nothing here can pick
    correctly, so every candidate is logged and the range is marked "merge-base" for the
    caller to warn about.
    """
    try:
        candidates = repo.git.merge_base(
            "--all", f"origin/{target_branch}", ref
        ).split()
    except git.exc.GitCommandError:
        candidates = []
    if not candidates:
        raise RuntimeError(
            f"No common history between origin/{target_branch} and {ref}."
            f" Check that {ref} exists and belongs to this repository."
        )
    if len(candidates) > 1:
        logger.warning(
            "Ambiguous history: %d merge bases between origin/%s and %s (%s)."
            " The diff may contain changes this branch did not make.",
            len(candidates),
            target_branch,
            ref,
            ", ".join(c[:9] for c in candidates),
        )
    return DiffRange(
        left=candidates[0],
        right=ref,
        ref=ref,
        strategy="merge-base",
        behind_count=behind,
    )


def resolve_diff_range(
    repo: Repo, ref: str = "HEAD", target_branch: str = "main"
) -> DiffRange:
    """Resolve the two tree-ishes whose diff is the branch's own contribution.

    Args:
        repo: The git repository.
        ref: The git ref holding the branch. Pass "HEAD" for the currently checked-out
            branch (default), or "origin/<branch>" for one not checked out locally.
        target_branch: The branch the work is destined for. Pass the MR's target branch.

    Merges the branch onto origin/<target_branch> in memory and diffs the target against
    the resulting tree, so the range covers what this branch adds to the target as it
    stands now. `git merge-tree` runs a real recursive merge, which resolves the several
    merge bases a branch that has merged its target in has.

    Falls back to a merge base when the branch no longer merges cleanly or the installed
    git predates `merge-tree --write-tree` (2.38).
    """
    repo.git.fetch("origin", target_branch)
    behind = int(repo.git.rev_list("--count", f"{ref}..origin/{target_branch}").strip())

    try:
        merged_tree = repo.git.merge_tree(
            "--write-tree", f"origin/{target_branch}", ref
        ).splitlines()[0]
    except git.exc.GitCommandError as e:
        logger.warning(
            "Cannot merge %s onto origin/%s (%s) — falling back to a merge base."
            " Run `aitools mr-update` to merge origin/%s into the branch.",
            ref,
            target_branch,
            e.stderr.strip() or f"status {e.status}",
            target_branch,
        )
        return _merge_base_range(repo, ref, target_branch, behind)

    target_ref = f"origin/{target_branch}"
    return DiffRange(
        left=target_ref,
        right=merged_tree,
        ref=ref,
        strategy="merge-tree",
        behind_count=behind,
    )


def get_branch_diff(
    repo: Repo,
    ref: str = "HEAD",
    target_branch: str = "main",
    diff_range: DiffRange | None = None,
) -> str:
    """Return the diff of commits on the given ref relative to the target branch.

    Args:
        repo: The git repository.
        ref: The git ref to diff. Pass "HEAD" for the currently checked-out branch
            (default), or "origin/<branch>" to review a branch not checked out locally.
        target_branch: The branch to diff against (default: "main"). Pass the MR's
            target branch so that the diff reflects only the MR's own increment.
        diff_range: A range already resolved for this ref and target branch. Pass one to
            reuse it, so the diff cannot drift from a range resolved earlier and the
            fetch and merge are not repeated.

    Resolves the range via resolve_diff_range so that commits already in the target are
    excluded. Excludes lockfiles and generated files. Prepends a --stat summary.
    Truncates the diff body if it exceeds MAX_DIFF_CHARS.
    """
    diff_range = diff_range or resolve_diff_range(repo, ref, target_branch)
    logger.debug("Diff range: %s", diff_range)

    left, right = diff_range.left, diff_range.right
    stat = repo.git.diff(left, right, "--stat", "--", *EXCLUDED_PATHSPECS)
    diff = repo.git.diff(left, right, "--", *EXCLUDED_PATHSPECS)

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + (
            f"\n\n[Diff truncated at {MAX_DIFF_CHARS} characters."
            " See stat summary above for full file list.]"
        )
        logger.warning("Diff truncated to %d characters", MAX_DIFF_CHARS)

    result = f"Changed files:\n{stat}\n\nDiff:\n{diff}" if stat else f"Diff:\n{diff}"
    logger.debug("Branch diff retrieved: %d characters", len(result))
    return result


def get_per_file_diffs(repo: Repo, target_branch: str = "main") -> FileDiffMap:
    """Return per-file diffs for the current branch relative to the target branch.

    Uses the same range resolution and exclusions as get_branch_diff. Returns a
    FileDiffMap with the stat summary and a dict of file_path -> diff text.
    """
    diff_range = resolve_diff_range(repo, "HEAD", target_branch)
    logger.debug("Diff range for per-file diffs: %s", diff_range)

    left, right = diff_range.left, diff_range.right
    stat = repo.git.diff(left, right, "--stat", "--", *EXCLUDED_PATHSPECS)
    name_only = repo.git.diff(left, right, "--name-only", "--", *EXCLUDED_PATHSPECS)

    files: dict[str, str] = {}
    for file_path in name_only.strip().splitlines():
        file_path = file_path.strip()
        if not file_path:
            continue
        try:
            file_diff = repo.git.diff(left, right, "--", file_path)
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
