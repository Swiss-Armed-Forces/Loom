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


def build_issue_note_reply_prompt(
    author: str, note_body: str, old_description: str, new_description: str
) -> str:
    """Build the Claude prompt for generating a reply to a single issue comment."""
    return f"""You just updated a GitLab issue description to address a comment left by a user.
Write a concise reply to the commenter explaining how the description was updated to address
their feedback.

Comment by @{author}:
{note_body}

Old description:
{old_description}

New description:
{new_description}

Instructions:
- Address @{author} by username at the start
- Explain what was changed in the description to address their comment
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


def build_mr_review_prompt(
    mr: ProjectMergeRequest, context_dir: str, comments_dir: str, branch_ref: str
) -> str:
    """Build the prompt for the multi-agent MR review.

    Claude is instructed to spawn five parallel review sub-agents covering the full
    changeset, then write one JSON comment file per finding to comments_dir. It must not
    modify source files, commit, or push.
    """
    return f"""You are performing a multi-agent code review of a GitLab merge request.

## Merge Request

Title: {mr.title}
URL: {mr.web_url}

## Context

All context files are in: {context_dir}
- branch.diff — full diff of the branch against main (for reference only)

Start by running `git diff origin/main...{branch_ref} --name-only` to discover the
complete changeset. Read the changed files directly from the repository to understand
what was added or removed.

## Review criteria

  1. Bug-free — correct behaviour at runtime, no protocol violations
  2. Complete — nothing missing, no dangling references, no half-wired config
  3. Minimal — no dead code, no unnecessary abstractions, nothing that does not need to exist
  4. Simple — straightforward design, no duplication, easy to follow

## How to review

Spawn 5 parallel review sub-agents using the Agent tool (subagent_type=Explore).
Each agent examines the full changeset from a different angle:

**Agent 1 — Protocol / runtime correctness (bug-free)**
Examine all new or modified production code. Are library APIs called in the correct
order? Race conditions or thread-safety issues? Silent error swallows? Connections
left in a bad state on failure? Reconnect loops sound? Blocking shutdown latency?

**Agent 2 — Integration wiring (bug-free + complete)**
Examine task/worker/framework integration points. Queues routed correctly? Decorator
order correct? Bootsteps registered only for the right worker type? Background threads
joined on stop with no leaks? Duplicate event dispatch — is that acceptable? Dead
imports, variables, or helpers defined but never used?

**Agent 3 — Configuration, deployment wiring, and documentation (complete + minimal)**
Examine settings classes, Helm values, ConfigMaps, and deployment manifests. Do env
var names round-trip correctly (camelCase → snake_case)? Are nil guards correct for
booleans and integers? Do Helm defaults match the settings class defaults? Are there
other deployment files that also need updating? Any dead config (added but never read,
or read but never wired)?
Also check the Documentation/ directory, README.md, and CLAUDE.md for correctness
against the changeset: are new Helm values, settings, CLI flags, or behavioural
changes reflected? Is any existing documentation now stale or misleading?

**Agent 4 — Test quality (bug-free + minimal)**
Examine all new and modified test files. Do fixtures and fake data match real shapes
produced by the libraries under test? Are mocks injected via DI rather than patched?
Duplicated setup? Low-value tests that only verify what the type system enforces?
Missing high-value tests (failure paths, edge cases, rapid duplicate events)? Dead
test helpers or unused imports?

**Agent 5 — Deleted code completeness + test execution (complete + minimal)**
For every file deleted on this branch, search the entire repo for remaining references
to the deleted symbols. Check imports, beat schedules, router registrations, and
OpenAPI-generated frontend types. Look for logic in new files that already exists
elsewhere and should be reused. Run `backend-test` and `frontend-test` and report any
failures, including regressions in code outside the changeset.

## Output

After all agents complete, for **each finding** write one JSON file to: {comments_dir}/

Name files sequentially: 001.json, 002.json, etc.

Each file must contain exactly this JSON structure:
{{
    "file": "path/to/file.py",
    "line": 42,
    "severity": "Critical",
    "body": "The comment text — specific, references exact code, suggests the fix.",
    "context": "def foo():\n    return bar  # the problematic line"
}}

- "file": repo-relative path to the file, or null for a general MR comment
- "line": line number in the new version of the file, or null if not applicable
- "severity": one of "Critical", "High", or "Low"
- "body": the review comment body (plain text, no markdown wrapping)
- "context": the relevant code snippet(s) that illustrate the finding — include enough
  surrounding lines for the reader to understand the issue without opening the file;
  use null if there is no specific code to show

Do NOT modify any source files. Do NOT commit or push. Only write the JSON files.
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
