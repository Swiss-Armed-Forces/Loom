from gitlab.v4.objects import ProjectIssue, ProjectJob, ProjectMergeRequest


def build_diff_chunk_summary_prompt(files_in_chunk: list[str], chunk_diff: str) -> str:
    """Build the prompt for summarizing a chunk of file diffs."""
    files_list = ", ".join(files_in_chunk)
    return f"""Summarize the following code diff in 3-8 sentences.
Focus on what changed functionally across these files: {files_list}
Output only the summary paragraph, nothing else.

Diff:
{chunk_diff}
"""


def build_mr_update_prompt(
    mr_template: str,
    current_title: str = "",
    current_description: str = "",
    include_diff: str | None = None,
    user_instructions: str = "",
) -> str:
    """Build the prompt for MR title/description generation.

    Args:
        mr_template: The MR template content to include in instructions.
        current_title: The current MR title (as a hint for the AI).
        current_description: The current MR description (as a hint for the AI).
        include_diff: If provided, append the diff to the prompt.
        user_instructions: Additional user instructions to append to the prompt.
    """
    template_instruction = ""
    if mr_template:
        template_instruction = f"""
- MR description body should follow this template:

{mr_template}

For the Summary section, write a brief paragraph summarizing the changes, followed by
sections like "Added:", "Changed:", "Removed:", "Fixed:" with bullet points
(use "- " for bullets).

Leave the Issue Reference section empty (it will be filled manually).
"""

    current_mr_hint = ""
    if current_title or current_description:
        current_mr_hint = "\nCurrent MR content (use as reference):\n"
        if current_title:
            current_mr_hint += f"Title: {current_title}\n"
        if current_description:
            current_mr_hint += f"Description:\n{current_description}\n"

    prompt = f"""Generate a git commit message and MR description for the following diff.

Format:
- First line: conventional commit format (type(scope): description), max 72 characters
- Blank line
{template_instruction}
Rules:
- Describe what changed, not why
- Output only the raw commit message text, nothing else
- Do NOT wrap output in code fences or markdown code blocks
- Use markdown formatting for the body (headers with #, bullet points with -)
- Preserve external references from the current description if still relevant
  (e.g., "Closes #123", "Related to #456", links to issues/MRs, or other cross-references)
{current_mr_hint}"""

    if user_instructions:
        prompt += f"\nAdditional user instructions:\n{user_instructions}\n"

    if include_diff:
        prompt += f"\nDiff:\n{include_diff}\n"

    return prompt


def build_implement_prompt(issue: ProjectIssue, context_dir: str) -> str:
    """Build the prompt for implementing a GitLab issue."""
    labels = ", ".join(issue.labels) if issue.labels else "(none)"

    return f"""You are implementing a GitLab issue for the Loom project.

## Issue

Title: {issue.title}
URL: {issue.web_url}
Labels: {labels}

## Context

All context files are in: {context_dir}
- issue.md — full issue description

## Task

Implement the changes described in the issue. Follow the project conventions in CLAUDE.md.
Make the necessary code changes, write tests where appropriate, and ensure the implementation
is complete. When done, commit all changes with a conventional commit message
(type(scope): description), then push the branch.
"""


def build_milestone_implement_prompt(issue: ProjectIssue, context_dir: str) -> str:
    """Build the prompt for implementing a GitLab issue as part of milestone
    automation."""
    labels = ", ".join(issue.labels) if issue.labels else "(none)"

    return f"""You are implementing a GitLab issue for the Loom project.

## Issue

Title: {issue.title}
URL: {issue.web_url}
Labels: {labels}

## Context

All context files are in: {context_dir}
- issue.md — full issue description

## Task

Implement the changes described in the issue. Follow the project conventions in CLAUDE.md.
Make the necessary code changes, write tests where appropriate, and ensure the implementation
is complete.
When done, commit all changes with a conventional commit message (type(scope): description),
then push the branch.
"""


def build_mr_fix_prompt(mr: ProjectMergeRequest, context_dir: str) -> str:
    """Build the prompt for fixing MR review comments."""
    return f"""You are addressing code review comments on a GitLab merge request.

## Merge Request

Title: {mr.title}
URL: {mr.web_url}

## Context

All context files are in: {context_dir}
- review_comments.txt — unresolved review threads
- branch.diff — current branch diff

## Task

Address each unresolved review comment by modifying the relevant source files.
Follow the existing code style and project conventions.
When you have implemented all changes, commit them with a conventional commit message
(type(scope): description), then push the branch.
"""


def build_comment_reply_prompt(location: str, thread: str, diff: str) -> str:
    """Build the Claude prompt for generating a reply to a single review comment."""
    return f"""You just addressed a GitLab code review comment by modifying the source code.
Write a concise reply to the reviewer explaining what you changed to address their feedback.

Comment location: {location}

Review thread:
{thread}

Branch diff (your changes):
{diff}

Instructions:
- Reference the specific change you made
- Keep it to 1-3 sentences
- Sound natural and professional
- Do NOT use greetings like "Hi" or sign-offs like "Thanks"
- Output only the reply text, nothing else
"""


def build_release_notes_prompt(
    tag_name: str,
    previous_tag: str | None,
    milestone_info: str,
    diff: str,
) -> str:
    """Build the Claude prompt for generating release notes."""
    prev_info = (
        f"Previous release: {previous_tag}"
        if previous_tag
        else "First release (no previous tag)"
    )
    diff_header = f"{previous_tag or 'initial'} → {tag_name}"

    milestone_section = ""
    if milestone_info:
        milestone_section = f"\n## Milestone Items\n\n{milestone_info}\n"

    return f"""Generate release notes for version {tag_name} of the Loom project.

## Release Information

Tag: {tag_name}
{prev_info}
{milestone_section}
## Git Diff ({diff_header})

{diff}

## Instructions

Write concise, user-friendly release notes with this structure:

# {tag_name}

A short paragraph summarising the highlights of this release.

## Added
- New features

## Changed
- Changes to existing functionality

## Fixed
- Bug fixes

## Removed
- Removed features (omit this section entirely if there are none)

Rules:
- Focus on user-visible changes, not internal implementation details
- Reference MR/issue numbers where relevant (e.g. !123, #456)
- Be specific but concise
- Output only the raw release notes text, nothing else
- Do NOT wrap output in code fences or markdown code blocks
"""


def build_issue_update_prompt(issue: ProjectIssue, context_dir: str) -> str:
    """Build the prompt for interactively updating a GitLab issue description."""
    return f"""You are helping improve the description of a GitLab issue for the Loom project.

## Issue

Title: {issue.title}
URL: {issue.web_url}
Issue #{issue.iid}

## Context

All context files are in: {context_dir}
- issue.md — current title and description
- comments.md — all user comments on the issue
- proposed_description.md — write your improved description here

## Task

Read issue.md and comments.md to understand the issue and its discussion.
Then write an improved issue description to proposed_description.md.

The improved description should:
- Be clear, concise, and well-structured
- Incorporate relevant context from the comments
- Follow GitLab markdown formatting
- Preserve any important details from the original description

The user will refine the result with you interactively. Always keep proposed_description.md
up to date with the latest version you and the user agree on.

Do NOT modify issue.md or comments.md.
"""


def build_watch_fix_prompt(job: ProjectJob, context_dir: str, pipeline_id: int) -> str:
    """Build the prompt for diagnosing and fixing a CI job failure."""
    return f"""You are fixing a failed GitLab CI/CD job in the Loom project.

## Job Details

Job ID: {job.id}
Job Name: {job.name}
Stage: {job.stage}
Status: {job.status}
URL: {job.web_url}

## Context

All context files are in: {context_dir}
- job_log.txt — full job log
- artifacts/ — extracted job artifacts (empty if none)

## Task

Using the job log, artifacts (if any), and the project source code, diagnose the root cause
of this CI/CD failure.

**If the failure is caused by a transient infrastructure or environment issue** (e.g. network
timeouts, Docker pull failures, flaky external services, DNS failures, resource exhaustion,
or any failure that is not caused by code in this repository), do NOT modify any source files.
Instead, retry the pipeline by running this command in the terminal:

    aitools pipeline-retry {pipeline_id}

**If the failure is caused by a code defect**, make the necessary changes to fix it, then
commit all changes with a conventional commit message (type(scope): description),
then push the branch.
"""


def build_mr_create_commit_prompt(commit_title: str) -> str:
    """Build the prompt for committing staged changes in mr-create."""
    return f"""All changes are already staged with `git add -A`.

Commit the staged changes with this exact message:

    {commit_title}

Run: git commit -m "{commit_title}"

If pre-commit hooks fail (e.g. linting or formatting errors), fix the reported issues,
re-stage the affected files, and retry the commit. Do NOT change the commit message.
Do NOT push.
"""


def build_merge_conflict_prompt(
    branch_name: str, conflicting_files: list[str], context_dir: str
) -> str:
    """Build the prompt for resolving git merge conflicts after merging origin/main."""
    files_list = "\n".join(f"- {f}" for f in conflicting_files)
    return f"""\
You are resolving git merge conflicts on branch '{branch_name}' in the Loom project.
A merge of origin/main was started but left unfinished due to conflicts.

## Conflicting files

{files_list}

## Task

Each file listed above contains git conflict markers (<<<<<<<, =======, >>>>>>>).
For each conflicting file:
1. Read the file and understand both sides of the conflict
2. Resolve it by producing the correct combined result
3. Remove all conflict markers
4. Write the resolved content back

Resolve the conflict markers only — do NOT stage, commit, or push.

Context directory: {context_dir}
- conflicts.txt — list of conflicting files
"""


def build_diagnose_prompt(job: ProjectJob, context_dir: str, pipeline_id: int) -> str:
    """Build the prompt for diagnosing a CI/CD job failure."""
    return f"""You are diagnosing a failed GitLab CI/CD job in the Loom project.

## Job Details

Job ID: {job.id}
Job Name: {job.name}
Stage: {job.stage}
Status: {job.status}
URL: {job.web_url}

## Context

All context files are in: {context_dir}
- job_log.txt — full job log
- artifacts/ — extracted job artifacts (empty if none)

## Task

Using the job log, artifacts (if any), and the project source code, find the root cause
of this CI/CD failure. Navigate the codebase as needed to understand the context.
Provide a clear explanation of what went wrong and suggest how to fix it.

If the failure is caused by a transient infrastructure or environment issue (e.g. network
timeouts, Docker pull failures, flaky external services, DNS failures, resource exhaustion),
you can retry the pipeline directly by running:

    aitools pipeline-retry {pipeline_id}
"""
